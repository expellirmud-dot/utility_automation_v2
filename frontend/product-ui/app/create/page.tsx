"use client";
import React, { useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const IssueItem = ({ issue, type }: { issue: any, type: 'missing_data' | 'warning' | 'blocker' }) => {
  if (typeof issue === 'string') {
    return <li>{issue}</li>;
  }
  
  const metaColor = type === 'blocker' ? 'text-red-500 border-red-200' : type === 'warning' ? 'text-amber-600 border-amber-200' : 'text-slate-500 border-slate-200';
  const detailBg = type === 'blocker' ? 'bg-red-100' : type === 'warning' ? 'bg-amber-100' : 'bg-slate-200';
  
  return (
    <li className="mb-2 last:mb-0">
      <div className="font-semibold">{issue.message}</div>
      <div className={`flex flex-wrap gap-1.5 mt-1 text-[11px] ${metaColor}`}>
        {issue.code && <span className="font-mono bg-white px-1.5 py-0.5 rounded border">code: {issue.code}</span>}
        {issue.component && <span className="font-mono bg-white px-1.5 py-0.5 rounded border">cmp: {issue.component}</span>}
        {issue.field && <span className="font-mono bg-white px-1.5 py-0.5 rounded border">field: {issue.field}</span>}
      </div>
      {issue.detail && Object.keys(issue.detail).length > 0 && (
        <details className="mt-1.5">
          <summary className={`cursor-pointer text-[11px] underline ${metaColor} opacity-80 hover:opacity-100 outline-none`}>
            แสดงข้อมูลเพิ่มเติม
          </summary>
          <div className={`mt-1.5 p-2 rounded text-[11px] font-mono whitespace-pre-wrap overflow-x-auto ${detailBg} text-slate-800`}>
            {Object.entries(issue.detail).map(([k, v]) => (
              <div key={k}><span className="font-bold opacity-70">{k}:</span> {typeof v === 'object' ? JSON.stringify(v) : String(v)}</div>
            ))}
          </div>
        </details>
      )}
    </li>
  );
};

const IssueList = ({
  flatArray,
  structuredArray,
  type,
  title,
  containerBg,
  containerBorder,
  titleColor,
  listColor
}: {
  flatArray?: string[];
  structuredArray?: any[];
  type: 'missing_data' | 'warning' | 'blocker';
  title: string;
  containerBg: string;
  containerBorder: string;
  titleColor: string;
  listColor: string;
}) => {
  const hasStructured = structuredArray && structuredArray.length > 0;
  const hasFlat = flatArray && flatArray.length > 0;
  
  if (!hasStructured && !hasFlat) return null;
  
  const items = hasStructured ? structuredArray : flatArray;
  
  return (
    <div className={`mt-2 p-3 ${containerBg} border ${containerBorder} rounded-lg`}>
      <div className={`font-bold ${titleColor} mb-2`}>{title}:</div>
      <ul className={`list-disc pl-5 space-y-2 ${listColor}`}>
        {items!.map((item: any, idx: number) => (
          <IssueItem key={idx} issue={item} type={type} />
        ))}
      </ul>
    </div>
  );
};

export default function CreateCase() {
  const API_BASE_URL = process.env.NEXT_PUBLIC_PRODUCT_API_BASE_URL ?? "http://127.0.0.1:8000";
  const apiUrl = (path: string) => `${API_BASE_URL}${path}`;

  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [caseId, setCaseId] = useState("");
  const [error, setError] = useState("");

  // Local file upload states
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Budget Preview States
  const [previewData, setPreviewData] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(true);
  const [previewError, setPreviewError] = useState("");

  // Readiness Preview States
  const [formExpenseGroup, setFormExpenseGroup] = useState("");
  const [formFiscalYear, setFormFiscalYear] = useState("2569");
  const [formAmount, setFormAmount] = useState("");
  const [formProvider, setFormProvider] = useState("");
  const [readinessData, setReadinessData] = useState<any>(null);
  const [readinessLoading, setReadinessLoading] = useState(false);
  const [readinessError, setReadinessError] = useState("");


  React.useEffect(() => {
    const fetchPreview = async () => {
      try {
        const res = await fetch(apiUrl("/api/budget/preview/remained-budget"));
        if (!res.ok) {
          throw new Error("ไม่พบไฟล์ B_RemainedBudget.xlsx หรือไม่สามารถโหลดตัวอย่างได้");
        }
        const data = await res.json();
        setPreviewData(data);
      } catch (err: any) {
        setPreviewError(err.message);
      } finally {
        setPreviewLoading(false);
      }
    };
    fetchPreview();
  }, []);

  React.useEffect(() => {
    if (!previewData || !formExpenseGroup) {
      setReadinessData(null);
      return;
    }

    const checkReadiness = async () => {
      setReadinessLoading(true);
      setReadinessError("");
      try {
        const payload = {
          case_facts: {
            fiscal_year_be: parseInt(formFiscalYear, 10) || previewData.metadata?.fiscal_year_be || 2569,
            expense_group: formExpenseGroup,
            required_amount: formAmount ? parseFloat(formAmount) : null,
            provider: formProvider ? formProvider : null
          },
          budget_preview_batch: previewData
        };

        const res = await fetch(apiUrl("/api/budget/preview/readiness"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          throw new Error("Failed to fetch readiness preview");
        }

        const data = await res.json();
        setReadinessData(data);
      } catch (err: any) {
        setReadinessError(err.message);
      } finally {
        setReadinessLoading(false);
      }
    };

    const timerId = setTimeout(() => {
      checkReadiness();
    }, 300);
    return () => clearTimeout(timerId);
  }, [previewData, formExpenseGroup, formFiscalYear, formAmount, formProvider]);

  const formatCurrency = (val: any) => {
    if (val === null || val === undefined) return "-";
    return Number(val).toLocaleString("th-TH", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const handleFiles = (files: FileList) => {
    const newFiles: File[] = [];
    const errors: string[] = [];
    const allowedTypes = ["application/pdf", "image/jpeg", "image/jpg", "image/png"];
    
    Array.from(files).forEach((file) => {
      const fileExt = file.name.split('.').pop()?.toLowerCase();
      const isValidType = allowedTypes.includes(file.type) || ['pdf', 'jpg', 'jpeg', 'png'].includes(fileExt || '');
      
      if (!isValidType) {
        errors.push(`ไฟล์ "${file.name}" ต้องเป็น PDF, JPG, หรือ PNG เท่านั้น`);
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        errors.push(`ไฟล์ "${file.name}" มีขนาดเกิน 10MB (ปัจจุบัน ${(file.size / (1024 * 1024)).toFixed(2)}MB)`);
        return;
      }
      newFiles.push(file);
    });
    
    if (errors.length > 0) {
      setValidationErrors(prev => [...prev, ...errors]);
    }
    if (newFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...newFiles]);
    }
  };

  const handleBoxClick = () => {
    fileInputRef.current?.click();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    
    const formData = new FormData(e.currentTarget);
    const payload = {
      fiscal_year_be: parseInt(formData.get("fiscal_year_be") as string, 10),
      work_month: formData.get("work_month") as string,
      case_type: formData.get("case_type") as string,
      expense_group: formData.get("expense_group") as string,
      department: formData.get("department") as string,
      division: formData.get("division") as string || null,
      note: formData.get("note") as string || null,
    };

    try {
      const res = await fetch(apiUrl("/api/cases/"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) {
        throw new Error(await res.text());
      }
      
      const data = await res.json();
      setCaseId(data.case_number);
      setSuccess(true);
      setSelectedFiles([]);
      setValidationErrors([]);
      e.currentTarget.reset();
      
      // Refresh dashboard route cache
      router.refresh();
      
    } catch (err: any) {
      setError(err.message || "Failed to create case");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">สร้างเคสใหม่</h2>
          <p className="text-slate-500 text-sm mt-1">กรอกข้อมูลเคสเบิกจ่ายค่าสาธารณูปโภค</p>
        </div>
        <Link href="/" className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg shadow-sm text-sm font-semibold hover:bg-slate-50 transition">
          ← กลับ
        </Link>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-500 text-red-800 rounded shadow-sm">
          <span className="font-bold">Error:</span> {error}
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-50 border-l-4 border-green-500 text-green-800 rounded shadow-sm flex justify-between items-center">
          <div>
            <span className="font-bold">สร้างเคสสำเร็จ!</span> เลขแฟ้ม: <span className="font-mono">{caseId}</span>
          </div>
          <button onClick={() => setSuccess(false)} className="text-sm font-semibold text-green-600 hover:text-green-800">สร้างใหม่</button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-100">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center text-sm">📋</div>
            <h3 className="font-bold text-[16px] text-slate-800">ข้อมูลทั่วไป</h3>
          </div>
          
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-[13px] font-bold text-slate-700 mb-2">ประเภทเคส <span className="text-red-500">*</span></label>
              <select name="case_type" className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow" required>
                <option value="">-- เลือกประเภท --</option>
                <option value="utility">ค่าสาธารณูปโภค</option>
                <option value="office">วัสดุสำนักงาน</option>
                <option value="other">อื่นๆ</option>
              </select>
            </div>
            <div>
              <label className="block text-[13px] font-bold text-slate-700 mb-2">ปีงบประมาณ <span className="text-red-500">*</span></label>
              <select 
                name="fiscal_year_be" 
                value={formFiscalYear}
                onChange={(e) => setFormFiscalYear(e.target.value)}
                className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow" 
                required
              >
                <option value="2569">2569 (ต.ค. 2568 - ก.ย. 2569)</option>
                <option value="2568">2568 (ต.ค. 2567 - ก.ย. 2568)</option>
              </select>
            </div>
            <div>
              <label className="block text-[13px] font-bold text-slate-700 mb-2">เดือนที่เบิก <span className="text-red-500">*</span></label>
              <select name="work_month" className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow" required>
                <option value="">-- เลือกเดือน --</option>
                <option value="ตุลาคม">ตุลาคม</option>
                <option value="พฤศจิกายน">พฤศจิกายน</option>
                <option value="ธันวาคม">ธันวาคม</option>
                <option value="มกราคม">มกราคม</option>
                <option value="กุมภาพันธ์">กุมภาพันธ์</option>
                <option value="มีนาคม">มีนาคม</option>
              </select>
            </div>
            <div>
              <label className="block text-[13px] font-bold text-slate-700 mb-2">กลุ่มค่าใช้จ่าย <span className="text-red-500">*</span></label>
              <select 
                name="expense_group" 
                value={formExpenseGroup}
                onChange={(e) => setFormExpenseGroup(e.target.value)}
                className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow" 
                required
              >
                <option value="">-- เลือกกลุ่ม --</option>
                <option value="ค่าไฟฟ้า">ค่าไฟฟ้า</option>
                <option value="ค่าน้ำประปา">ค่าน้ำประปา</option>
                <option value="ค่าโทรศัพท์">ค่าโทรศัพท์</option>
                <option value="ค่าอินเทอร์เน็ต">ค่าอินเทอร์เน็ต</option>
              </select>
            </div>
            <div>
              <label className="block text-[13px] font-bold text-slate-700 mb-2">หน่วยงาน <span className="text-red-500">*</span></label>
              <select name="department" className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow" required>
                <option value="">-- เลือกหน่วยงาน --</option>
                <option value="สำนักปลัด">สำนักปลัด</option>
                <option value="กองคลัง">กองคลัง</option>
                <option value="กองช่าง">กองช่าง</option>
              </select>
            </div>
            <div>
              <label className="block text-[13px] font-bold text-slate-700 mb-2">ฝ่าย/งาน</label>
              <select name="division" className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow">
                <option value="">-- เลือกฝ่าย --</option>
                <option value="งานการเงิน">งานการเงิน</option>
                <option value="งานบัญชี">งานบัญชี</option>
              </select>
            </div>
            <div>
              <label className="block text-[13px] font-bold text-slate-700 mb-2">จำนวนเงินที่ขอเบิก <span className="text-slate-400 text-xs font-normal">(ถ้ามี)</span></label>
              <input 
                type="number" 
                step="0.01"
                value={formAmount}
                onChange={(e) => setFormAmount(e.target.value)}
                className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow" 
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-[13px] font-bold text-slate-700 mb-2">ผู้ให้บริการ <span className="text-slate-400 text-xs font-normal">(ถ้ามี)</span></label>
              <input 
                type="text" 
                value={formProvider}
                onChange={(e) => setFormProvider(e.target.value)}
                className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow" 
                placeholder="เช่น PEA, NT..."
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-100">
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center text-sm">📄</div>
            <h3 className="font-bold text-[16px] text-slate-800">อัปโหลดเอกสารต้นฉบับ</h3>
          </div>

          <input 
            type="file"
            ref={fileInputRef}
            onChange={handleInputChange}
            multiple
            accept=".pdf,.jpg,.jpeg,.png"
            className="hidden"
          />
          
          <div 
            onClick={handleBoxClick}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer select-none
              ${isDragging 
                ? 'border-blue-500 bg-blue-50/30' 
                : 'border-slate-300 hover:bg-slate-50'}`}
          >
            <div className="w-14 h-14 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center text-2xl mx-auto mb-4">📤</div>
            <h4 className="font-bold text-slate-700 mb-1">คลิกเพื่ออัปโหลด หรือ ลากไฟล์มาวาง</h4>
            <p className="text-sm text-slate-500">รองรับไฟล์ PDF, JPG, PNG (สูงสุด 10MB ต่อไฟล์)</p>
            <p className="text-xs text-slate-400 mt-2">(MOCK: ไม่มีการอัปโหลดไฟล์จริงใน Checkpoint นี้)</p>
          </div>

          {/* Validation errors */}
          {validationErrors.length > 0 && (
            <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg text-xs text-red-800">
              <div className="flex justify-between items-center font-bold mb-2">
                <span>ข้อผิดพลาดเกี่ยวกับไฟล์:</span>
                <button 
                  type="button" 
                  onClick={() => setValidationErrors([])} 
                  className="text-red-600 hover:text-red-800 underline font-semibold"
                >
                  ล้างข้อผิดพลาด
                </button>
              </div>
              <ul className="list-disc pl-4 space-y-1">
                {validationErrors.map((err, idx) => (
                  <li key={idx}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Selected files list */}
          {selectedFiles.length > 0 && (
            <div className="mt-6 space-y-3">
              <h5 className="text-[13px] font-bold text-slate-700">ไฟล์ที่เตรียมอัปโหลด ({selectedFiles.length})</h5>
              <div className="grid grid-cols-1 gap-2">
                {selectedFiles.map((file, idx) => (
                  <div key={idx} className="flex justify-between items-center p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm hover:border-slate-300 transition-colors">
                    <div className="flex items-center gap-3 truncate">
                      <span className="text-2xl">
                        {file.name.toLowerCase().endsWith('.pdf') ? '📄' : '🖼️'}
                      </span>
                      <div className="truncate">
                        <p className="font-bold text-slate-700 truncate">{file.name}</p>
                        <p className="text-[11px] text-slate-400">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                      </div>
                    </div>
                    <button 
                      type="button" 
                      onClick={() => setSelectedFiles(prev => prev.filter((_, i) => i !== idx))}
                      className="text-red-500 hover:text-red-700 font-bold px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition shadow-sm"
                    >
                      ลบออก
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Budget Readiness Preview Section */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-4 pb-4 border-b border-slate-100">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center text-sm">🛡️</div>
            <h3 className="font-bold text-[16px] text-slate-800">ตรวจความพร้อมงบประมาณ</h3>
          </div>
          
          <div className="p-3 mb-4 bg-slate-50 border border-slate-200 text-slate-600 rounded-lg text-sm flex items-start gap-2">
            <span className="text-slate-400">ℹ️</span>
            <p><strong>ผลตรวจนี้เป็นการประเมินเบื้องต้นจากข้อมูลตัวอย่าง ยังไม่บันทึกลงฐานข้อมูล</strong></p>
          </div>

          {!previewData || !formExpenseGroup ? (
            <div className="text-center py-8 text-slate-500 text-sm border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
               รอข้อมูลสำหรับตรวจความพร้อม
            </div>
          ) : readinessLoading ? (
            <div className="text-center py-8 text-slate-500 text-sm">
              <span className="inline-block animate-spin mr-2">⏳</span> กำลังประมวลผล...
            </div>
          ) : readinessError ? (
            <div className="text-center py-8 text-red-500 text-sm border-2 border-dashed border-red-200 rounded-xl bg-red-50">
              <span className="text-red-400">{readinessError}</span>
            </div>
          ) : readinessData ? (
            <div className="space-y-4 text-sm">
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-700">สถานะความพร้อม:</span>
                {readinessData.status === 'ready' && <span className="px-2 py-1 bg-green-100 text-green-700 rounded-md font-bold">พร้อมเบิกจ่าย (Ready)</span>}
                {readinessData.status === 'warning' && <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded-md font-bold">แจ้งเตือน (Warning)</span>}
                {readinessData.status === 'blocked' && <span className="px-2 py-1 bg-red-100 text-red-700 rounded-md font-bold">ติดขัด (Blocked)</span>}
                {readinessData.status === 'missing_data' && <span className="px-2 py-1 bg-slate-100 text-slate-700 rounded-md font-bold">ข้อมูลไม่ครบ (Missing Data)</span>}
              </div>

              {readinessData.withholding_tax && (
                <div>
                  <span className="font-bold text-slate-700">ภาษีหัก ณ ที่จ่าย: </span>
                  <span className={`px-2 py-0.5 rounded text-xs ${readinessData.withholding_tax.applies === true ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600'}`}>
                    {readinessData.withholding_tax.display_label}
                  </span>
                </div>
              )}

              {readinessData.budget_match && readinessData.budget_match.match_status === 'matched' && (
                <div className="mt-4 border border-slate-200 rounded-lg overflow-hidden">
                  <div className="bg-slate-50 px-3 py-2 border-b border-slate-200 font-bold text-slate-700">ข้อมูลรายการงบประมาณที่จับคู่ได้</div>
                  <div className="p-3 grid grid-cols-2 gap-y-2 gap-x-4">
                    <div><span className="text-slate-500">ประเภทรายจ่าย:</span> <span className="font-semibold text-slate-800">{readinessData.budget_match.expense_type}</span></div>
                    <div><span className="text-slate-500">งาน:</span> <span className="font-semibold text-slate-800">{readinessData.budget_match.work}</span></div>
                    <div><span className="text-slate-500">หมวดรายจ่าย:</span> <span className="font-semibold text-slate-800">{readinessData.budget_match.appropriation_category}</span></div>
                    <div><span className="text-slate-500">รหัสงบประมาณ:</span> <span className="font-mono text-xs font-semibold text-slate-800">{readinessData.budget_match.budget_code}</span></div>
                    <div className="col-span-2"><span className="text-slate-500">งบคงเหลือ:</span> <span className="font-bold text-emerald-600">{readinessData.budget_match.remaining_amount !== null ? readinessData.budget_match.remaining_amount.toLocaleString("th-TH", { minimumFractionDigits: 2 }) : "-"} บาท</span></div>
                  </div>
                </div>
              )}

              <IssueList
                flatArray={readinessData.missing_data}
                structuredArray={readinessData.missing_data_details}
                type="missing_data"
                title="ข้อมูลที่ขาดหาย"
                containerBg="bg-slate-50"
                containerBorder="border-slate-200"
                titleColor="text-slate-700"
                listColor="text-slate-600"
              />

              <IssueList
                flatArray={readinessData.warnings}
                structuredArray={readinessData.warning_details}
                type="warning"
                title="แจ้งเตือน"
                containerBg="bg-amber-50"
                containerBorder="border-amber-200"
                titleColor="text-amber-800"
                listColor="text-amber-700"
              />

              <IssueList
                flatArray={readinessData.blockers}
                structuredArray={readinessData.blocker_details}
                type="blocker"
                title="ปัญหาที่ทำให้เบิกจ่ายไม่ได้"
                containerBg="bg-red-50"
                containerBorder="border-red-200"
                titleColor="text-red-800"
                listColor="text-red-700"
              />
            </div>
          ) : null}
        </div>

        {/* Budget Preview Section */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-4 pb-4 border-b border-slate-100">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-500 flex items-center justify-center text-sm">📊</div>
            <h3 className="font-bold text-[16px] text-slate-800">ตัวอย่างงบประมาณ (Budget Preview)</h3>
          </div>

          <div className="p-3 mb-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-sm flex items-start gap-2">
            <span className="text-amber-500">⚠️</span>
            <p><strong>ข้อมูลนี้เป็นตัวอย่างตรวจสอบเท่านั้น ยังไม่นำเข้า DB</strong> (db_import_safe=false)</p>
          </div>

          {previewLoading ? (
            <div className="text-center py-8 text-slate-500 text-sm">
              <span className="inline-block animate-spin mr-2">⏳</span> กำลังโหลดข้อมูล...
            </div>
          ) : previewError ? (
            <div className="text-center py-8 text-slate-500 text-sm border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
              <span className="text-slate-400">{previewError}</span>
            </div>
          ) : previewData && previewData.rows && previewData.rows.length > 0 ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-sm bg-slate-50 p-3 rounded-lg border border-slate-200">
                <div><span className="text-slate-500">ปีงบประมาณ:</span> <strong>{previewData.metadata?.fiscal_year_be || "-"}</strong></div>
                <div><span className="text-slate-500">เดือน:</span> <strong>{previewData.metadata?.printed_month || "-"}</strong></div>
                <div><span className="text-slate-500">อปท.:</span> <strong>{previewData.metadata?.municipality || "-"}</strong></div>
              </div>

              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-sm whitespace-nowrap">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold">
                    <tr>
                      <th className="px-4 py-2 border-r border-slate-200">แถว (Excel)</th>
                      <th className="px-4 py-2 border-r border-slate-200">แผนงาน (Plan)</th>
                      <th className="px-4 py-2 border-r border-slate-200">งาน (Work)</th>
                      <th className="px-4 py-2 border-r border-slate-200">หมวดรายจ่าย</th>
                      <th className="px-4 py-2 border-r border-slate-200">ประเภทรายจ่าย</th>
                      <th className="px-4 py-2 border-r border-slate-200">รหัสงบประมาณ</th>
                      <th className="px-4 py-2 border-r border-slate-200 text-right">งบอนุมัติ</th>
                      <th className="px-4 py-2 border-r border-slate-200 text-right">ผูกพัน</th>
                      <th className="px-4 py-2 border-r border-slate-200 text-right">เบิกจ่าย</th>
                      <th className="px-4 py-2 border-r border-slate-200 text-right">คงเหลือ</th>
                      <th className="px-4 py-2 border-r border-slate-200 text-center">ภาษี หัก ณ ที่จ่าย</th>
                      <th className="px-4 py-2 border-r border-slate-200">หน่วยงาน (Dept)</th>
                      <th className="px-4 py-2">งบ (Budget)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {previewData.rows.slice(0, 50).map((row: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-4 py-2 border-r border-slate-100 text-slate-500">{row.source_row}</td>
                        <td className="px-4 py-2 border-r border-slate-100 text-slate-400 italic">{row.placeholders?.plan}</td>
                        <td className="px-4 py-2 border-r border-slate-100 truncate max-w-[150px]" title={row.extracted?.work}>{row.extracted?.work}</td>
                        <td className="px-4 py-2 border-r border-slate-100 truncate max-w-[150px]">{row.extracted?.appropriation_category}</td>
                        <td className="px-4 py-2 border-r border-slate-100 truncate max-w-[150px]" title={row.extracted?.expense_type}>{row.extracted?.expense_type}</td>
                        <td className="px-4 py-2 border-r border-slate-100 font-mono text-xs">{row.extracted?.budget_code}</td>
                        <td className="px-4 py-2 border-r border-slate-100 text-right">{formatCurrency(row.extracted?.approved_amount)}</td>
                        <td className="px-4 py-2 border-r border-slate-100 text-right">{formatCurrency(row.extracted?.obligated_amount)}</td>
                        <td className="px-4 py-2 border-r border-slate-100 text-right">{formatCurrency(row.extracted?.disbursed_amount)}</td>
                        <td className="px-4 py-2 border-r border-slate-100 text-right font-bold text-slate-700">{formatCurrency(row.extracted?.remaining_amount)}</td>
                        <td className="px-4 py-2 border-r border-slate-100 text-center">
                          <span className={`px-2 py-0.5 rounded text-xs ${row.derived?.withholding_tax?.applies === true ? 'bg-purple-100 text-purple-700' : row.derived?.withholding_tax?.applies === false ? 'bg-slate-100 text-slate-600' : 'bg-amber-100 text-amber-700'}`}>
                            {row.derived?.withholding_tax?.display_label || "-"}
                          </span>
                        </td>
                        <td className="px-4 py-2 border-r border-slate-100 text-slate-400 italic">{row.placeholders?.department}</td>
                        <td className="px-4 py-2 text-slate-400 italic">{row.placeholders?.budget}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="text-right text-xs text-slate-500 mt-2">
                แสดงผลตัวอย่างสูงสุด 50 รายการ (จากทั้งหมด {previewData.summary?.total_rows || 0})
              </div>
            </div>
          ) : (
             <div className="text-center py-8 text-slate-500 text-sm border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
               ไม่มีข้อมูลให้แสดงผล
             </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-100">
            <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-500 flex items-center justify-center text-sm">📝</div>
            <h3 className="font-bold text-[16px] text-slate-800">หมายเหตุเพิ่มเติม</h3>
          </div>
          
          <textarea 
            name="note"
            className="w-full border border-slate-300 rounded-lg p-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow min-h-[100px]" 
            placeholder="ระบุรายละเอียดเพิ่มเติม (ถ้ามี)..."
          ></textarea>
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Link href="/" className="px-5 py-2.5 bg-white border border-slate-300 text-slate-700 rounded-lg shadow-sm text-sm font-bold hover:bg-slate-50 transition">
            ยกเลิก
          </Link>
          <button type="submit" disabled={loading} className="px-8 py-2.5 bg-gradient-to-br from-[#1e3a5f] to-[#2d5a8e] text-white rounded-lg shadow text-sm font-bold hover:opacity-90 transition disabled:opacity-50">
            {loading ? "กำลังบันทึก..." : "สร้างเคส"}
          </button>
        </div>
      </form>
    </div>
  );
}
