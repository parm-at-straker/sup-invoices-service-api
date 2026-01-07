import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    """LanguageCloud users.

    Table: `sitemanager.obj_m_member`
    """

    __tablename__ = "obj_m_member"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String, name="obj_uuid", unique=True)
    email: Mapped[str] = mapped_column(String, name="email_primary")
    username: Mapped[str] = mapped_column(String, name="login")
    given_name: Mapped[str] = mapped_column(String)
    family_name: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, name="active")
    is_deleted: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, name="created")
    modified_at: Mapped[datetime.datetime] = mapped_column(DateTime, name="modified")
