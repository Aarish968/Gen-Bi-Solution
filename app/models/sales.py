from sqlalchemy import Column, Integer, String, Float, Date
from app.models.base import Base

class Sales(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    sale_date = Column(Date, nullable=False)
    region = Column(String(100))
