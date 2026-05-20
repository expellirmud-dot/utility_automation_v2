from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.product.api.cases import router as cases_router
from src.product.api.budget import router as budget_router

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

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "municipal-finance-product-api"}
