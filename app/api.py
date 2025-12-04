from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_reader import parse_pdf
from app.services.extractor import extract_metadata
from app.services.summarizer import summarize_changes
from app.services.checklist import generate_checklist
from app.services.risk_model import RiskModel
from typing import List


router = APIRouter()


@router.post('/ingest/pdf')
async def ingest_pdf(file: UploadFile = File(...)):
if not file.filename.lower().endswith('.pdf'):
raise HTTPException(status_code=400, detail='Only PDF allowed')
contents = await file.read()
text = parse_pdf(contents)
metadata = extract_metadata(text)
summary = summarize_changes(text)
checklist = generate_checklist(metadata)
return {
'filename': file.filename,
'metadata': metadata,
'summary': summary,
'checklist': checklist
}


@router.post('/predict/risk')
async def predict_risk(payload: dict):
model = RiskModel.load_or_train()
score = model.predict_proba(payload)
return {'risk_score': score}
