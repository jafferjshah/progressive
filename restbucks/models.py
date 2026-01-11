"""
SQLAlchemy models
"""

from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    drink = Column(String, nullable=False)
    size = Column(String, nullable=False)
    milk = Column(String, nullable=False)
    shots = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")
    cost = Column(Float, nullable=False)
    paid = Column(Boolean, nullable=False, default=False)
    card_last_four = Column(String, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "drink": self.drink,
            "size": self.size,
            "milk": self.milk,
            "shots": self.shots,
            "status": self.status,
            "cost": self.cost,
            "paid": self.paid,
            "card_last_four": self.card_last_four
        }
