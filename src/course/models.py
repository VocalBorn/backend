from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

class Course(SQLModel, table=True):
    __tablename__ = "courses"

    course_id: Optional[int] = Field(default=None, primary_key=True)
    course_name: str = Field(index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    chapters: List["Chapter"] = Relationship(back_populates="course")

class Chapter(SQLModel, table=True):
    __tablename__ = "chapters"

    chapter_id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.course_id")
    chapter_name: str = Field(index=True)
    description: Optional[str] = None
    sequence_number: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    course: Course = Relationship(back_populates="chapters")
    sentences: List["Sentence"] = Relationship(back_populates="chapter")

class Sentence(SQLModel, table=True):
    __tablename__ = "sentences"

    sentence_id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="chapters.chapter_id")
    sentence_name: str = Field(index=True)
    speaker_role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    chapter: Chapter = Relationship(back_populates="sentences")
