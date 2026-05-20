from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class FiscalYear(Base):
    __tablename__ = "fiscal_years"
    
    id = Column(Integer, primary_key=True, index=True)
    year_be = Column(Integer, unique=True, index=True) # e.g. 2569
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BudgetLine(Base):
    __tablename__ = "budget_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id"), nullable=False)
    department = Column(String, index=True) # หน่วยงาน
    division = Column(String, index=True) # ฝ่าย/งาน
    expense_type = Column(String, index=True) # ประเภทรายจ่าย (e.g. ค่าไฟฟ้า, ค่าน้ำประปา)
    initial_amount = Column(Float, default=0.0) # งบตั้งต้น
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    fiscal_year = relationship("FiscalYear")

class ExpenseLedger(Base):
    __tablename__ = "expense_ledgers"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_line_id = Column(Integer, ForeignKey("budget_lines.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True) # Reference to the case causing expense
    amount_deducted = Column(Float, default=0.0)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now())
    
    budget_line = relationship("BudgetLine")
    case = relationship("Case", back_populates="ledger_entries")

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String, unique=True, index=True) # เลขแฟ้ม e.g. CASE-2569-03-005
    fiscal_year_be = Column(Integer, index=True) # ปีงบประมาณ 2569
    work_month = Column(String) # เดือน e.g. มีนาคม
    case_type = Column(String) # ประเภทเคส e.g. utility, office
    expense_group = Column(String) # กลุ่มค่าใช้จ่าย e.g. ค่าไฟฟ้า
    department = Column(String)
    division = Column(String, nullable=True)
    vendor_name = Column(String, nullable=True) # ผู้รับเงิน
    total_amount = Column(Float, default=0.0)
    status = Column(String, default="draft")
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    ledger_entries = relationship("ExpenseLedger", back_populates="case")
    documents = relationship("SourceDocument", back_populates="case")
    dika = relationship("Dika", back_populates="case", uselist=False)

class SourceDocument(Base):
    __tablename__ = "source_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    file_name = Column(String)
    file_path = Column(String)
    file_type = Column(String) # pdf, jpg, etc.
    document_type = Column(String) # bill, receipt, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    case = relationship("Case", back_populates="documents")
    bill_header = relationship("BillHeader", back_populates="document", uselist=False)

class BillHeader(Base):
    __tablename__ = "bill_headers"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("source_documents.id"), nullable=False)
    provider = Column(String)
    bill_date = Column(Date, nullable=True)
    total_amount = Column(Float, default=0.0)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("SourceDocument", back_populates="bill_header")

class Dika(Base):
    __tablename__ = "dikas"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    dika_number = Column(String, unique=True, nullable=True)
    dika_date = Column(Date, nullable=True)
    payee_name = Column(String, nullable=True)  # ผู้รับเงิน
    status = Column(String, default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    case = relationship("Case", back_populates="dika")
    memo = relationship("Memo", back_populates="dika", uselist=False)

class Memo(Base):
    __tablename__ = "memos"
    
    id = Column(Integer, primary_key=True, index=True)
    dika_id = Column(Integer, ForeignKey("dikas.id"), nullable=False)
    memo_number = Column(String, nullable=True)
    memo_date = Column(Date, nullable=True)
    content = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)  # path to generated .docx output
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    dika = relationship("Dika", back_populates="memo")

class ElaasPayload(Base):
    __tablename__ = "elaas_payloads"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    payload_data = Column(JSON)
    status = Column(String, default="prepared")
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
