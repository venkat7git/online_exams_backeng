

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from dbConnection import get_db
from dbModels import Admin,Lecturer  # Ensure models.py has Admin model

# Create FastAPI instance
app = FastAPI()

@app.get("/admins")
def get_admins(db: Session = Depends(get_db)):
    admins = db.query(Admin).all()  # Fetch all records
    if not admins:
        raise HTTPException(status_code=404, detail="No admins found")
    return admins

@app.get("/lecturers")
def get_admins(db: Session = Depends(get_db)):
    admins = db.query(Lecturer).all()  # Fetch all records
    if not admins:
        raise HTTPException(status_code=404, detail="No lecturer found")
    return admins



# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("auth:app", host="0.0.0.0", port=8000, reload=True)
