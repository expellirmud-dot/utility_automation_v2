from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.product.api.cases import router as cases_router
from src.product.api.budget import router as budget_router
from src.product.api.documents import router as documents_router
from src.product.api.memos import router as memos_router
from src.product.api.validation import router as validation_router
from src.product.api.elaas import router as elaas_router
from src.product.api.workflow import router as workflow_router

app = FastAPI(title="Municipal Finance Utility Disbursement API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases_router)
app.include_router(budget_router)
app.include_router(documents_router)
app.include_router(memos_router)
app.include_router(validation_router)
app.include_router(elaas_router)
app.include_router(workflow_router)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "municipal-finance-product-api"}
