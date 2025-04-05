from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Admin(Base):
    __tablename__ = "admins"  # Ensure this matches your database table name

    admin_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    is_super_admin = Column(Integer, unique=True, nullable=False)
   
class Lecturer(Base):
    __tablename__ = "lecturers"  # Ensure this matches your database table name

    lecturer_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    department = Column(String, unique=True, nullable=False)