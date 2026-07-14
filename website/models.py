from flask_login import UserMixin
from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import ForeignKey
from . import db
from datetime import datetime,timezone

class User(db.Model,UserMixin):
    
    __tablename__ = 'user'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False)
    Email: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    Role: Mapped[str] = mapped_column(nullable=False)
    
class MenuItem():
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
    decription: Mapped[str] = mapped_column(nullable=False)
    
class Order():
    
    id:Mapped[int] = mapped_column(primary_key=True)
    customer_id : Mapped[int] = mapped_column(ForeignKey('user.id'),nullable=False)
    status: Mapped[str] = mapped_column(default="pending")
    orderTime: Mapped[datetime] = mapped_column(datetime) 
    
    
    
    