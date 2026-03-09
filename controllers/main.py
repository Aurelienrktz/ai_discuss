from odoo import http
from odoo.http import request


class AIInternalController(http.Controller):

    @http.route("/ai_internal/start_chat", type="json", auth="user")
    def start_chat(self):
        user = request.env.user
        ai_user = self.env.ref("ai_internal_chatbot.user_ai_assistant")

        channel = request.env["mail.channel"].sudo().search([
            ("channel_type", "=", "chat"),
            ("channel_partner_ids", "in", [user.partner_id.id]),
            ("channel_partner_ids", "in", [ai_user.partner_id.id]),
        ], limit=1)

        if not channel:
            channel = request.env["mail.channel"].sudo().create({
                "channel_type": "chat",
                "channel_partner_ids": [
                    (4, user.partner_id.id),
                    (4, ai_user.partner_id.id),
                ],
            })

        return {
            "channel_id": channel.id
        }