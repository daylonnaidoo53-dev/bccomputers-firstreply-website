"""
app/adapters/base.py — Abstract channel adapter interface and message models.
Author: Daylon Naido · BCComputers
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from config import Config


@dataclass
class InboundMessage:
    """Normalized internal message model."""
    channel: str
    sender_id: str
    sender_name: str
    text: str
    received_at: datetime


class BaseAdapter(ABC):
    """Abstract base class for all channel communication adapters."""

    channel: str

    @abstractmethod
    def normalize(self, raw: Any) -> Optional[InboundMessage]:
        """Normalize vendor-specific webhook payload into an InboundMessage."""

    @abstractmethod
    async def send(self, to: str, text: str, cfg: Config) -> None:
        """Send an outbound reply through this channel."""
