from odoo import models, api
import requests
import logging
import threading

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

            with registry.cursor() as cr:
                env = api.Environment(cr, uid, {})

                channel = env["mail.channel"].browse(channel_id)
                ai_partner = env["res.partner"].browse(partner_id)

                config = env["ir.config_parameter"].sudo()
                api_url = config.get_param("ai_internal.api_url")

                try:
                    if not api_url:
                        raise Exception("API URL non configurée")

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

                except requests.exceptions.Timeout:
                    channel.message_post(
                        body="Le délai de réponse est dépassé. Veuillez réessayer.",
                        author_id=ai_partner.id,
                        message_type='comment',
                        subtype_id=env.ref('mail.mt_comment').id
                    )

                except requests.exceptions.ConnectionError:
                    channel.message_post(
                        body="Impossible de contacter le serveur IA.",
                        author_id=ai_partner.id,
                        message_type='comment',
                        subtype_id=env.ref('mail.mt_comment').id
                    )

                except Exception as e:
                    _logger.error("AI Thread Error: %s", e)

                    channel.message_post(
                        body="Une erreur est survenue, veuillez réessayer.",
                        author_id=ai_partner.id,
                        message_type='comment',
                        subtype_id=env.ref('mail.mt_comment').id
                    )

                cr.commit()