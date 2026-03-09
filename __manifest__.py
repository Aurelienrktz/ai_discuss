{
    "name": "AI Internal ChatBot",
    "version": "16.0.1.0.0",
    "summary": "Private AI Assistant for internal users via Discuss",
    "description": "Provides a private AI chat assistant inside Odoo Discuss for each internal user.",
    "author": "Your Company",
    "depends": ["mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/ai_user.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ai_discuss/static/src/css/style.css",
        ],
    },
    "stallable": True,
    "application": False,
}