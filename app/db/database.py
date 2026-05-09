from sqlalchemy import create_engine, Column, Integer, Float, String, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agro_shield.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class WeatherHistory(Base):
    __tablename__ = "weather_history"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    date = Column(Date)
    precipitation = Column(Float)
    eto = Column(Float)
    soil_moisture = Column(Float)
    
    __table_args__ = (UniqueConstraint('latitude', 'longitude', 'date', name='_lat_lon_date_uc'),)

class SoilData(Base):
    __tablename__ = "soil_data"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    clay = Column(Float)
    sand = Column(Float)
    wv0033 = Column(Float)
    wv1500 = Column(Float)
    tipo_solo = Column(String)
    
    __table_args__ = (UniqueConstraint('latitude', 'longitude', name='_lat_lon_uc'),)

Base.metadata.create_all(bind=engine)
