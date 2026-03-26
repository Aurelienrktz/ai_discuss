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
            ai_user = self.env.ref("ai_internal_chatbot.user_ai_assistant")

            # Vérifier que c'est un chat privé
            if self.channel_type == "chat" and ai_user.partner_id in self.channel_partner_ids:

                # Ne pas répondre aux messages du bot
                if message.author_id != ai_user.partner_id:

                    user_message = kwargs.get("body")

                    if user_message:
                        # Lancer l'appel IA en arrière-plan
                        threading.Thread(
                            target=self._send_to_ai_background,
                            args=(user_message, ai_user.id, self.id, self.env.uid)
                        ).start()

        except Exception as e:
            _logger.error("AI Internal Chat Error: %s", e)

        return message

    def _send_to_ai_background(self, text, ai_user_id, channel_id, uid):

        with api.Environment.manage():

            registry = self.env.registry
            with registry.cursor() as cr:

                env = api.Environment(cr, uid, {})
                channel = env["mail.channel"].browse(channel_id)
                ai_user = env["res.users"].browse(ai_user_id)

                config = env["ir.config_parameter"].sudo()
                api_url = config.get_param("ai_internal.api_url")

                error_message = "Erreur, veuillez réessayer."

                try:

                    if not api_url:
                        raise Exception("AI API URL not configured")

                    response = requests.post(
                        api_url,
                        json={
                            "message": text,
                            "sessionId": f"user_{uid}"
                        },
                        timeout=(5,60)
                    )

                    if response.status_code != 200:
                        raise Exception(f"API returned {response.status_code}")

                    reply = response.text.strip()

                    if not reply:
                        raise Exception("Empty AI response")

                    channel.message_post(
                        body=reply,
                        author_id=ai_user.partner_id.id,
                        message_type='comment',
                        subtype_id=env.ref('mail.mt_comment').id
                    )

                except Exception as e:

                    _logger.error("AI Request failed: %s", e)

                    # envoyer message d'erreur à l'utilisateur
                    channel.message_post(
                        body=error_message,
                        author_id=ai_user.partner_id.id,
                        message_type='comment',
                        subtype_id=env.ref('mail.mt_comment').id
                    )

                cr.commit()