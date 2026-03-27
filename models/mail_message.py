from odoo import models, api
import requests
import logging
import threading
import time
from psycopg2 import OperationalError

_logger = logging.getLogger(__name__)


class MailChannel(models.Model):
    _inherit = "mail.channel"

    def message_post(self, **kwargs):
        message = super().message_post(**kwargs)

        try:
            config = self.env["ir.config_parameter"].sudo()

            partner_id_raw = config.get_param("assistant_id", 0)
            partner_id = int(partner_id_raw) if partner_id_raw else 0

            if not partner_id:
                return message

            ai_partner = self.env["res.partner"].browse(partner_id)

            if not ai_partner.exists():
                _logger.warning("AI partner not found")
                return message

            self.invalidate_recordset()

            if self.channel_type == 'chat' and partner_id in self.channel_partner_ids.ids:
                
                if message.author_id.id != partner_id:

                    user_message = kwargs.get("body")

                    if user_message:
                        threading.Thread(
                            target=self._send_to_ai_background,
                            args=(user_message, partner_id, self.id, self.env.user.id),
                            daemon=True
                        ).start()

        except Exception as e:
            _logger.error("Erreur détection AI : %s", e)

        return message

    def _send_to_ai_background(self, text, partner_id, channel_id, uid):
        with api.Environment.manage():
            registry = self.env.registry

            for attempt in range(3):
                try:
                    with registry.cursor() as cr:
                        env = api.Environment(cr, uid, {})

                        channel = env["mail.channel"].browse(channel_id)
                        ai_partner = env["res.partner"].browse(partner_id)

                        config = env["ir.config_parameter"].sudo()
                        api_url = config.get_param("ai_internal.api_url")

                        if not api_url:
                            raise Exception("API URL non configurée")

                        time.sleep(0.3)

                        response = requests.post(
                            api_url,
                            json={
                                "message": text,
                                "sessionId": f"user_{uid}"
                            },
                            timeout=(10, 60)
                        )

                        if response.status_code != 200:
                            raise Exception(f"Erreur API {response.status_code}")

                        reply = response.text.strip()

                        if not reply:
                            raise Exception("Réponse vide")

                        cr.commit()

                        channel.invalidate_recordset()

                        channel.message_post(
                            body=reply,
                            author_id=ai_partner.id,
                            message_type='comment',
                            subtype_id=env.ref('mail.mt_comment').id
                        )

                        cr.commit()
                        return

                except OperationalError as e:
                    if "could not serialize access" in str(e):
                        _logger.warning(f"Retry {attempt+1} (concurrency)")
                        time.sleep(0.5)
                        continue
                    else:
                        raise

                except requests.exceptions.Timeout:
                    self._send_error_message(
                        channel_id, partner_id, uid,
                        "Erreur : Le délai de réponse est dépassé. Veuillez réessayer."
                    )
                    return

                except requests.exceptions.ConnectionError:
                    self._send_error_message(
                        channel_id, partner_id, uid,
                        "Impossible de contacter le serveur IA."
                    )
                    return

                except Exception as e:
                    _logger.error("AI Thread Error: %s", e)

                    self._send_error_message(
                        channel_id, partner_id, uid,
                        "Une erreur est survenue, veuillez réessayer."
                    )
                    return

    def _send_error_message(self, channel_id, partner_id, uid, message):

        with api.Environment.manage():
            registry = self.env.registry

            with registry.cursor() as cr:
                env = api.Environment(cr, uid, {})

                channel = env["mail.channel"].browse(channel_id)

                channel.message_post(
                    body=message,
                    author_id=partner_id,
                    message_type='comment',
                    subtype_id=env.ref('mail.mt_comment').id
                )

                cr.commit()