from fastapi import FastAPI
from app.api import router


app = FastAPI(title="AI Fraud & Compliance Brain")
app.include_router(router)


@app.get("/")
async def root():
return {"status": "ok", "service": "AI Fraud & Compliance Brain"}
