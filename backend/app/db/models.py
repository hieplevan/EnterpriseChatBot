import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="EMPLOYEE")  # ADMIN, LEGAL, HR, FINANCE, EMPLOYEE
    department = Column(String(50), nullable=False, default="GENERAL")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), default="New Conversation")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(String(64), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    citations_json = Column(Text, nullable=True)  # JSON string of citations
    metrics_json = Column(Text, nullable=True)  # JSON string of latency, scores
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    feedbacks = relationship("Feedback", back_populates="message", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    rating = Column(Integer, nullable=False)  # +1: Thumbs Up, -1: Thumbs Down
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    message = relationship("Message", back_populates="feedbacks")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)
    role = Column(String(20), nullable=True)
    action = Column(String(50), nullable=False)  # QUERY, UPLOAD, DELETE, EVALUATION
    query_text = Column(Text, nullable=True)
    pii_detected = Column(String(200), nullable=True)  # None or comma-separated detected types
    latency_ms = Column(Float, default=0.0)
    faithfulness_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), unique=True, index=True, nullable=False)
    file_type = Column(String(20), nullable=False)
    size_bytes = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    department = Column(String(50), default="GENERAL")
    classification = Column(String(50), default="INTERNAL")  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    uploaded_by = Column(String(50), default="admin")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
