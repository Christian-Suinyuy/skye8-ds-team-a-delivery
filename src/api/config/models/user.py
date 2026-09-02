from sqlalchemy import String, UUID
import uuid
from sqlalchemy.orm import Mapped, mapped_column

from api.config.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique = True, index=True)
    password_hashed: Mapped[str] = mapped_column(String(255), nullable=False)