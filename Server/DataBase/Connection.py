from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base,sessionmaker
DATABASE_URL = "postgresql+psycopg://postgres:Pankaj0403%40@localhost/Rapido"
engine=create_engine(DATABASE_URL)
SessionLocal=sessionmaker(bind=engine)
Base=declarative_base()