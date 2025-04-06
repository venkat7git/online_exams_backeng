from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum  # For use in Pydantic
from sqlalchemy import Enum  # For SQLAlchemy column


Base = declarative_base()

class Admin(Base):
    __tablename__ = "admin_details"  # Ensure this matches your database table name

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    is_super_admin = Column(Integer, unique=True, nullable=False)
   
class Lecturer(Base):
    __tablename__ = "lecturers"  # Ensure this matches your database table name

    lecturer_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    department = Column(String, unique=True, nullable=False)


class Student(Base):
    __tablename__ = "student_registration"  # ✅ Changed from dash to underscore

    id = Column(String, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    roll_number = Column(String(50))
    branch = Column(String(100))
    class_year = Column(String(50))
    gender = Column(Enum("Male", "Female", "Other", name="gender_enum"), nullable=False)
    mobile_number = Column(String(15))
    first_name = Column(String(50))
    last_name = Column(String(50))
