from flask_login import UserMixin
from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import ForeignKey,String,Float,Integer,DateTime
from . import db
from datetime import datetime,timezone
from typing import List,Optional


class User(db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'customer' or 'vendor'

    # Relationships (Type-hinted with List collections)
    menu_items: Mapped[List["MenuItem"]] = relationship(back_populates="vendor", lazy=True)
    orders: Mapped[List["Order"]] = relationship(back_populates="customer", lazy=True)


# 3. MenuItem Model
class MenuItem(db.Model):
    __tablename__ = "menu_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    vendor: Mapped["User"] = relationship(back_populates="menu_items")


# 4. Order Model (One Order with  Many OrderItems)
class Order(db.Model):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    customer: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", lazy=True, cascade="all, delete-orphan")


# 5. OrderItem Model
class OrderItem(db.Model):
    __tablename__ = "order_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), nullable=False)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_item.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    menu_item: Mapped["MenuItem"] = relationship()  # Directly links the item to its current menu details

    
    
    