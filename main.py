from fastapi import FastAPI
from pydantic import BaseModel
from model import get_similarity

app = FastAPI()

class AnswerEvaluationRequest(BaseModel):
    actual_answer: str
    student_answer: str

@app.post("/evaluate")
def evaluate(request: AnswerEvaluationRequest):
    score,feedback = get_similarity(request.actual_answer, request.student_answer)
    
    return {"score": score, "feedback": feedback}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
