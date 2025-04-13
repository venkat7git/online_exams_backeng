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


class RoleEnum(str, PyEnum):
    student = "student"
    lecturer = "lecturer"

class GenderEnum(str, PyEnum):
    male = "male"
    female = "female"
    other = "other"

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: RoleEnum
    employee_id: str | None = None
    roll_number: str | None = None
    phone: str
    gender: GenderEnum
    department_id: int
    class_id: int
