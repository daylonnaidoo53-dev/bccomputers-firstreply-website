"""
app/adapters — Channel adapters.
Author: Daylon Naido · BCComputers
"""

from app.adapters.base import BaseAdapter, InboundMessage
from app.adapters.email import EmailAdapter
from app.adapters.form import FormAdapter
from app.adapters.instagram import InstagramAdapter
from app.adapters.whatsapp import WhatsAppAdapter

__all__ = [
    "BaseAdapter",
    "InboundMessage",
    "FormAdapter",
    "WhatsAppAdapter",
    "InstagramAdapter",
    "EmailAdapter",
]
