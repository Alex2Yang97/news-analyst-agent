from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, ARRAY, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    identifier = Column(String, unique=True, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=False)
    createdAt = Column(String)

    # Relationships
    threads = relationship("Thread", back_populates="user", cascade="all, delete-orphan")


class Thread(Base):
    __tablename__ = 'threads'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    createdAt = Column(String)
    name = Column(String)
    userId = Column(UUID, ForeignKey('users.id', ondelete='CASCADE'))
    userIdentifier = Column(String)
    tags = Column(ARRAY(String))
    metadata_ = Column("metadata", JSON)

    # Relationships
    user = relationship("User", back_populates="threads")
    steps = relationship("Step", back_populates="thread", cascade="all, delete-orphan")
    elements = relationship("Element", back_populates="thread", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="thread", cascade="all, delete-orphan")


class Step(Base):
    __tablename__ = 'steps'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    threadId = Column(UUID, ForeignKey('threads.id'), nullable=False)
    parentId = Column(UUID)
    disableFeedback = Column(Boolean)
    streaming = Column(Boolean, nullable=False)
    waitForAnswer = Column(Boolean)
    isError = Column(Boolean)
    metadata_ = Column("metadata", JSON)
    tags = Column(ARRAY(String))
    input = Column(String)
    output = Column(String)
    createdAt = Column(String)
    start = Column(String)
    end = Column(String)
    generation = Column(JSON)
    showInput = Column(String)
    language = Column(String)
    indent = Column(Integer)

    # Relationships
    thread = relationship("Thread", back_populates="steps")


class Element(Base):
    __tablename__ = 'elements'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    threadId = Column(UUID, ForeignKey('threads.id'))
    type = Column(String)
    url = Column(String)
    chainlitKey = Column(String)
    name = Column(String, nullable=False)
    display = Column(String)
    objectKey = Column(String)
    size = Column(String)
    page = Column(Integer)
    language = Column(String)
    forId = Column(UUID)
    mime = Column(String)

    # Relationships
    thread = relationship("Thread", back_populates="elements")


class Feedback(Base):
    __tablename__ = 'feedbacks'

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    forId = Column(UUID, nullable=False)
    threadId = Column(UUID, ForeignKey('threads.id'), nullable=False)
    value = Column(Integer, nullable=False)
    comment = Column(String)

    # Relationships
    thread = relationship("Thread", back_populates="feedbacks")