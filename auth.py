from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from enum import Enum as PyEnum
import smtplib
import random
import ssl
import bcrypt
import uvicorn
import re
from typing import List, Literal, Optional
from datetime import date

# === Local Imports ===
from dbConnection import get_db

# === Configuration ===
EMAIL_ADDRESS = "venkat7softcy@gmail.com"
EMAIL_PASSWORD = "ztxu zffx xhdd tnts"  # Use environment variables in production

# === FastAPI App Setup ===
app = FastAPI()

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class RoleEnum(str, PyEnum):
    student = "student"
    lecturer = "lecturer"

# === Pydantic Schemas ===
class UserCreate(BaseModel):
    
    email: EmailStr
    password: str
    role: RoleEnum
    employee_id: str | None = None
    roll_number: str | None = None
    

class EmailRequest(BaseModel):
    email: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

# === OTP Store ===
otp_store = {}

# === Helper Functions ===
def send_email(to_email: str, otp: str):
    subject = "Your OTP Code"
    body = f"Your OTP is: {otp}"
    message = f"Subject: {subject}\n\n{body}"
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")

# === Routes ===

@app.post("/send-otp")
def send_otp(request: EmailRequest):
    otp = str(random.randint(100000, 999999))
    otp_store[request.email] = otp
    send_email(request.email, otp)
    return {"message": "OTP sent to email"}

@app.post("/verify-otp")
def verify_otp(request: OTPVerifyRequest):
    stored_otp = otp_store.get(request.email)
    if stored_otp and stored_otp == request.otp:
        del otp_store[request.email]
        return {"message": "OTP verified successfully"}
    raise HTTPException(status_code=400, detail="Invalid OTP")

@app.get("/departments")
def get_departments(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("CALL get_departments()"))
        return result.mappings().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching departments: {e}")

@app.get("/years")
def get_years(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("CALL get_years()"))
        return result.mappings().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching years: {e}")




class UserExistenceCheck(BaseModel):
    role: str  # should be 'student' or 'lecturer'
    roll_number: str | None = None
    employee_id: str | None = None

# === Route ===
@app.post("/check-user-exists")
def check_user_exists(data: UserExistenceCheck, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            CALL check_user_exists(:role, :roll_number, :employee_id)
        """), {
            "role": data.role,
            "roll_number": data.roll_number,
            "employee_id": data.employee_id
        })

        row = result.mappings().first()
        print("result",result)
        print("row value",row)
        print("row status",row.get("status"))
        if row.get("roll_number") == data.roll_number:
            return {"exists": True, "data": dict(row)}
        return {"exists": False, "message": "User mismatch"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking user existence: {e}")

class CreateUserRequest(BaseModel):
    password: str
    role: str  # should be 'student' or 'lecturer'
    roll_number: str | None = None
    employee_id: str | None = None

# === API Endpoint ===
@app.post("/create-user")
def create_user(user: CreateUserRequest, db: Session = Depends(get_db)):
    try:
        # Hash the password before sending to the DB
        hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        db.execute(text("""
            CALL create_student_lecturer(:password, :role, :roll_number, :employee_id)
        """), {
            "password": hashed_password,
            "role": user.role,
            "roll_number": user.roll_number,
            "employee_id": user.employee_id
        })

        db.commit()
        return {"message": "User created successfully"}

    except Exception as e:
        print("error:",e)
        return {"error":e}
        # error_msg = str(e.orig)
        # match = re.search(r"Duplicate entry '.*' for key '.*'", error_msg)
        # if match:
            
        #     return {"message": "user already exists"}
        # else:
        #     return {"message": "something went wrong"}
            

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# === Login Endpoint ===
@app.post("/login")
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        # 1. Call stored procedure to get user by email
        result = db.execute(text("CALL login_user(:email)"), {
            "email": request.email,
        })

        user = result.mappings().first()

        # 2. Check if user exists
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 3. Compare entered password with hashed password from DB
        stored_hash = user["password"]
        if not bcrypt.checkpw(request.password.encode("utf-8"), stored_hash.encode("utf-8")):
            raise HTTPException(status_code=401, detail="Invalid password")

        # 4. Return user info (without password)
        user_data = {key: value for key, value in user.items() if key != "password"}
        return {"message": "Login successful", "user": user_data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")

class MCQQuestion(BaseModel):
    question_text: str
    question_type: Literal["mcq"]
    marks: int
    options: List[str]
    correct_index: int  # 1-based index


class DescriptiveQuestion(BaseModel):
    question_text: str
    question_type: Literal["descriptive"]
    marks: int
    descriptive_answer: str


Question = MCQQuestion | DescriptiveQuestion


class ExamCreateRequest(BaseModel):
    subject_id: int
    title: str
    description: str  # ✅ Added this field
    total_marks: int
    date: date
    duration_minutes: int
    created_by: int
    questions: List[Question]


@app.post("/create-exam")
def create_exam(request: ExamCreateRequest, db: Session = Depends(get_db)):
    try:
        import json
        questions_json = json.dumps([q.dict() for q in request.questions])

        result = db.execute(text("""
            CALL create_exam_with_questions_json(
                :subject_id, :title, :description, :total_marks, :date,
                :duration_minutes, :created_by, :questions_json
            )
        """), {
            "subject_id": request.subject_id,
            "title": request.title,
            "description": request.description,  # ✅ Pass the description here
            "total_marks": request.total_marks,
            "date": request.date,
            "duration_minutes": request.duration_minutes,
            "created_by": request.created_by,
            "questions_json": questions_json
        })

        exam_id_row = result.fetchone()
        db.commit()

        if exam_id_row:
            return {
                "message": "Exam created successfully",
                "exam_id": exam_id_row[0]
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve exam ID")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating exam: {e}")


class DepartmentRequest(BaseModel):
    department_id: int

@app.post("/exams/by-department")
def get_exams_by_department(request: DepartmentRequest, db: Session = Depends(get_db)):
    try:
        result = db.execute(text(""" 
            CALL get_exams_by_department_json(:department_id)
        """), {"department_id": request.department_id})

        row = result.fetchone()

        if row and row[0]:
            import json
            return json.loads(row[0])

        return []

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error fetching exams: {e}")


class LecturerRequest(BaseModel):
    lecturer_id: int

@app.post("/exams/by-lecturer")
def get_exams_by_lecturer(request: LecturerRequest, db: Session = Depends(get_db)):
    try:
        result = db.execute(text(""" 
            CALL get_exams_by_lecturer_json(:lecturer_id)
        """), {"lecturer_id": request.lecturer_id})

        row = result.fetchone()

        if row and row[0]:
            import json
            return json.loads(row[0])

        return []

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error fetching exams: {e}")



class ExamDetailsRequest(BaseModel):
    exam_id: int
    role: Literal["primary_admin", "admin", "lecturer", "student"]


@app.post("/exam/details")
def get_exam_details(request: ExamDetailsRequest, db: Session = Depends(get_db)):
    try:
        result = db.execute(text(""" 
            CALL get_exam_details_by_id_json(:exam_id, :role)
        """), {
            "exam_id": request.exam_id,
            "role": request.role
        })

        row = result.fetchone()

        if row and row[0]:
            import json
            return json.loads(row[0])

        return {}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error fetching exam details: {e}")


# === Optional: Run directly ===
if __name__ == "__main__":
    print("✅ Starting FastAPI server...")
    uvicorn.run
