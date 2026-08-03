import os
#from dotenv import load_dotenv
#load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from parser import extract_resume_text
from analyzer import run_full_analysis
from emailer import send_report_email

app = FastAPI(title="ATS Gap Detector")

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisResponse(BaseModel):
    role_title: str
    seniority: str
    match_score: int
    summary: str
    have: list
    weak: list
    missing: list
    email_sent: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    email: str = Form(...),
    jd_text: str = Form(...),
    resume: UploadFile = File(...),
):
    if not jd_text.strip() or len(jd_text.strip()) < 30:
        raise HTTPException(400, "Job description looks too short — paste the full JD.")

    file_bytes = await resume.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(400, "Resume file too large (max 5MB).")

    try:
        resume_text = extract_resume_text(resume.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(400, str(e))

    try:
        result = run_full_analysis(resume_text, jd_text)
    except Exception as e:
        raise HTTPException(502, f"Analysis failed: {e}")

    jd_req = result["jd_requirements"]
    gap = result["gap_report"]

    email_sent = False
    try:
        send_report_email(
            to_email=email,
            role_title=jd_req.get("role_title", "this role"),
            seniority=jd_req.get("seniority", "unclear"),
            gap_report=gap,
        )
        email_sent = True
    except Exception as e:
        # Don't fail the whole request if email delivery fails —
        # the candidate still gets the report in the browser response.
        print(f"[email error] {e}")

    return AnalysisResponse(
        role_title=jd_req.get("role_title", "this role"),
        seniority=jd_req.get("seniority", "unclear"),
        match_score=gap.get("match_score", 0),
        summary=gap.get("summary", ""),
        have=gap.get("have", []),
        weak=gap.get("weak", []),
        missing=gap.get("missing", []),
        email_sent=email_sent,
    )
