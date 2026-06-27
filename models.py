from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from db import Base
from datetime import datetime


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False, unique=True)
    passwd = Column(String, nullable=False)
    email = Column(String, unique=True)
    storage_path = Column(String, nullable=True)


class Files(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, nullable=False)
    file_name = Column(String(30), nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_owner = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_type = Column(String(50))
    is_deleted = Column(Boolean, default=False)
    create_date = Column(DateTime, nullable=False, default=datetime.now)
