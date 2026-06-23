from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


DATABASE_URL = "sqlite:///./my_cloud.db"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user_info"
    
    name: Mapped[str] = mapped_column(String(10))
    id: Mapped[int] = mapped_column(primary_key=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(50), unique=True, index=True)


engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(engine)
