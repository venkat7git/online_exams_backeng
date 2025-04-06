from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dbConnection import get_db
from dbModels import Admin, Lecturer, Student
import smtplib
import random
import ssl
from pydantic import BaseModel, EmailStr
from enum import Enum as PyEnum

# === Enums ===
class GenderEnum(str, PyEnum):
    Male = "Male"
    Female = "Female"
    Other = "Other"

# === Pydantic Schemas ===
class StudentCreate(BaseModel):
    id: str
    email: EmailStr
    password: str
    roll_number: str
    branch: str
    class_year: str
    gender: GenderEnum
    mobile_number: str
    first_name: str
    last_name: str

class EmailRequest(BaseModel):
    email: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

# === FastAPI App Setup ===
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === OTP Store ===
otp_store = {}

# === Email Configuration ===
EMAIL_ADDRESS = "venkat7softcy@gmail.com"
EMAIL_PASSWORD = "ztxu zffx xhdd tnts"  # Use your Gmail app password

def send_email(to_email, otp):
    subject = "Your OTP Code"
    body = f"Your OTP is: {otp}"
    message = f"Subject: {subject}\n\n{body}"

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, message)

# === Routes ===

@app.post("/send-otp")
def send_otp(request: EmailRequest):
    email = request.email
    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp

    try:
        send_email(email, otp)
        return {"message": "OTP sent to email"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to send OTP")

@app.post("/verify-otp")
def verify_otp(request: OTPVerifyRequest):
    email = request.email
    otp = request.otp

    if otp_store.get(email) == otp:
        del otp_store[email]
        return {"message": "OTP verified successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")

@app.get("/admins")
def get_admins(db: Session = Depends(get_db)):
    admins = db.query(Admin).all()
    if not admins:
        raise HTTPException(status_code=404, detail="No admins found")
    return admins

@app.get("/lecturers")
def get_lecturers(db: Session = Depends(get_db)):
    lecturers = db.query(Lecturer).all()
    if not lecturers:
        raise HTTPException(status_code=404, detail="No lecturers found")
    return lecturers

import uuid

@app.post("/student-register")
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.email == student.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists")

    new_student_data = student.dict()
    new_student_data["id"] = str(uuid.uuid4())  # Generate a unique UUID for id

    new_student = Student(**new_student_data)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return {"message": "Student registered successfully"}


# Run with: uvicorn filename:app --reload
