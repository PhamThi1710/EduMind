from core.repository import BaseRepository
from machine.models.conversation import Conversation, Message


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for Conversation model."""
    pass


class MessageRepository(BaseRepository[Message]):
    """Repository for Message model."""
    pass
