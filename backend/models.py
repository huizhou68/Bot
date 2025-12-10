# Everything Is Good at This Point
# 01:05:42, 18.10.2025

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    passcode = Column(String, unique=True, index=True)
    last_login = Column(DateTime, nullable=True, default=None)
    context_summary = Column(Text, nullable=True)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    passcode = Column(String, nullable=False)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())