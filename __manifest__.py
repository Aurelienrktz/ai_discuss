{
    "name": "AI Internal ChatBot",
    "version": "16.0.1.0.0",
    "summary": "Private AI Assistant for internal users via Discuss",
    "description": """
        Provides a private AI chat assistant inside Odoo Discuss for each internal user.

        Main Features:
        - Automatic interception
        - External AI API integration
        - Real-time automated responses 
        - Dynamic API URL configuration via system parameters
        - Compatible with Odoo 16
        - This module need 2 key that you need to create in Odoo system settings :
            *ai_internal.api_url : the endpoint of the back
            *assistant_id : the assistant profil id 
    """,
    "author": "RAKOTOZANAKA Aurelien",
    "depends": ["mail"],
    "assets": {
        "web.assets_backend": [
            "ai_discuss/static/src/css/style.css",
        ],
    },
    "stallable": True,
    "application": False,
}