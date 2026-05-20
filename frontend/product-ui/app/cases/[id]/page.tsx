"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

type BillHeader = {
  id: number;
  provider: string | null;
  bill_date: string | null;
  total_amount: number;
  status: string;
  created_at: string;
};

type SourceDocument = {
  id: number;
  file_name: string;
  file_path: string;
  file_type: string;
  document_type: string;
  created_at: string;
  bill_header: BillHeader | null;
};

type ReadinessSummary = {
  document_status: boolean;
  ocr_status: boolean;
  dika_status: boolean;
  memo_status: boolean;
};

type ReadinessData = {
  ready: boolean;
  budget_ok: boolean;
  blockers: string[];
  warnings: string[];
  summary: ReadinessSummary;
};

type AttachmentItem = {
  id: number;
  label: string;
  required: boolean;
  doc_type: string;
  present: boolean;
};

type ElaasPayload = {
  case_number: string;
  department: string;
  division: string;
  fiscal_year_be: number;
  expense_group: string;
  work_month: string;
  payee_name: string;
  provider: string;
  bill_date: string;
  bill_date_thai: string;
  bill_amount: number;
  bill_amount_thai: string;
  dika_number: string;
  dika_date: string;
  dika_date_thai: string;
  memo_number: string;
  memo_date: string;
  memo_date_thai: string;
  memo_file_path: string;
  budget_available: number | null;
  readiness_passed: boolean;
  attachment_checklist: AttachmentItem[];
};

type TimelineEvent = {
  id: number;
  case_id: number;
  event_type: string;
  from_status: string | null;
  to_status: string | null;
  detail: string | null;
  created_at: string;
};

type CaseNote = {
  id: number;
  case_id: number;
  note_text: string;
  created_at: string;
};

type BudgetLineSummary = {
  id: number;
  department: string;
  division: string;
  expense_type: string;
  appropriation_category: string;
  initial_amount: number;
  deducted_amount: number;
  available_amount: number;
  fiscal_year_be: number;
};

type BudgetMatch = {
  status: "selected" | "matched" | "ambiguous" | "not_found";
  selected: BudgetLineSummary | null;
  candidates: BudgetLineSummary[];
};

type Case = {
  id: number;
  case_number: string;
  fiscal_year_be: number;
  work_month: string;
  case_type: string;
  expense_group: string;
  department: string;
  division: string | null;
  status: string;
  total_amount: number;
  note: string | null;
  created_at: string;
  documents: SourceDocument[];
};

export default function CaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const caseId = params?.id;

  const [loading, setLoading] = useState(true);
  const [casedata, setCaseData] = useState<Case | null>(null);
  const [error, setError] = useState("");

  // Upload States
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState("bill");
  const [dragActive, setDragActive] = useState(false);
  const [processingDocs, setProcessingDocs] = useState<Record<number, boolean>>({});

  // Memo States
  const [dikaNo, setDikaNo] = useState("");
  const [dikaDate, setDikaDate] = useState("");
  const [payeeName, setPayeeName] = useState("");
  const [memoNumber, setMemoNumber] = useState("");
  const [memoDate, setMemoDate] = useState("");
  const [memoGenerating, setMemoGenerating] = useState(false);
  const [memoError, setMemoError] = useState("");
  const [memoDownloadUrl, setMemoDownloadUrl] = useState<string | null>(null);

  // Readiness States
  const [readinessData, setReadinessData] = useState<ReadinessData | null>(null);
  const [loadingReadiness, setLoadingReadiness] = useState(false);

  // e-LAAS Assist States
  const [elaasPayload, setElaasPayload] = useState<ElaasPayload | null>(null);
  const [elaasLoading, setElaasLoading] = useState(false);
  const [elaasSaving, setElaasSaving] = useState(false);
  const [elaasSaved, setElaasSaved] = useState(false);
  const [elaasError, setElaasError] = useState("");
  const [elaasConfirm, setElaasConfirm] = useState([false, false, false]);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [timelineError, setTimelineError] = useState("");
  const [notes, setNotes] = useState<CaseNote[]>([]);
  const [noteText, setNoteText] = useState("");
  const [noteSaving, setNoteSaving] = useState(false);
  const [noteError, setNoteError] = useState("");
  const [statusActionLoading, setStatusActionLoading] = useState<string | null>(null);
  const [statusActionError, setStatusActionError] = useState("");
  const [budgetMatch, setBudgetMatch] = useState<BudgetMatch | null>(null);
  const [budgetLoading, setBudgetLoading] = useState(false);
  const [budgetError, setBudgetError] = useState("");
  const [budgetSelecting, setBudgetSelecting] = useState<number | null>(null);

  const lifecycleLabels: Record<string, string> = {
    draft: "รับเรื่อง",
    intake: "รับเรื่อง",
    documents_uploaded: "อัปโหลดเอกสารแล้ว",
    ocr_processed: "วิเคราะห์ OCR แล้ว",
    dika_prepared: "เตรียมฎีกาแล้ว",
    word_generated: "สร้างบันทึกแล้ว",
    memo_generated: "สร้างบันทึกแล้ว",
    readiness_passed: "ผ่านความพร้อม",
    elaas_prepared: "เตรียม e-LAAS แล้ว",
    submitted_manual: "ส่ง e-LAAS แล้ว",
    completed: "เสร็จสิ้น",
  };

  const eventLabels: Record<string, string> = {
    document_uploaded: "อัปโหลดเอกสาร",
    ocr_success: "วิเคราะห์ OCR สำเร็จ",
    dika_saved: "บันทึกข้อมูลฎีกา",
    memo_generated: "สร้างบันทึกข้อความ",
    elaas_payload_saved: "บันทึกข้อมูล e-LAAS",
    submitted_manually: "ทำเครื่องหมายว่าส่งแล้ว",
    completed_manually: "ทำเครื่องหมายว่าเสร็จสิ้น",
  };

  const displayStatus = (status: string | null | undefined) => lifecycleLabels[status || ""] || status || "-";

  const fetchReadiness = async () => {
    setLoadingReadiness(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}/readiness`, {
        cache: "no-store",
      });
      if (res.ok) {
        setReadinessData(await res.json());
      }
    } catch (err) {
      console.error("Failed to fetch readiness", err);
    } finally {
      setLoadingReadiness(false);
    }
  };

  const fetchElaas = async () => {
    setElaasLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}/elaas-payload`, {
        cache: "no-store",
      });
      if (res.ok) {
        setElaasPayload(await res.json());
      }
    } catch (err) {
      console.error("Failed to fetch e-LAAS payload", err);
    } finally {
      setElaasLoading(false);
    }
  };

  const fetchTimeline = async () => {
    setTimelineError("");
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}/timeline`, {
        cache: "no-store",
      });
      if (!res.ok) throw new Error(await res.text());
      setTimeline(await res.json());
    } catch (err: any) {
      setTimelineError(err.message || "ไม่สามารถโหลดประวัติเคสได้");
    }
  };

  const fetchNotes = async () => {
    setNoteError("");
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}/notes`, {
        cache: "no-store",
      });
      if (!res.ok) throw new Error(await res.text());
      setNotes(await res.json());
    } catch (err: any) {
      setNoteError(err.message || "ไม่สามารถโหลดบันทึกผู้ปฏิบัติงานได้");
    }
  };

  const fetchBudgetMatch = async () => {
    setBudgetLoading(true);
    setBudgetError("");
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/budget/cases/${caseId}/match`, {
        cache: "no-store",
      });
      if (!res.ok) throw new Error(await res.text());
      setBudgetMatch(await res.json());
    } catch (err: any) {
      setBudgetError(err.message || "ไม่สามารถโหลดงบประมาณที่เกี่ยวข้องได้");
    } finally {
      setBudgetLoading(false);
    }
  };

  const handleCopyField = (value: string, fieldId: string) => {
    navigator.clipboard.writeText(value).then(() => {
      setCopiedField(fieldId);
      setTimeout(() => setCopiedField(null), 1500);
    });
  };

  const handleCopyAll = () => {
    if (!elaasPayload) return;
    const text = `หน่วยงาน: ${elaasPayload.department}
ปีงบประมาณ: ${elaasPayload.fiscal_year_be}
เดือน: ${elaasPayload.work_month}
กลุ่มค่าใช้จ่าย: ${elaasPayload.expense_group}
ผู้รับเงิน (ตามฎีกา): ${elaasPayload.payee_name}
ผู้ให้บริการ (ตามบิล): ${elaasPayload.provider}
วันที่บิล: ${elaasPayload.bill_date_thai || "-"}
ยอดเงิน: ${elaasPayload.bill_amount}
เลขที่ฎีกา: ${elaasPayload.dika_number || "-"}
วันที่ฎีกา: ${elaasPayload.dika_date_thai || "-"}
เลขที่บันทึก: ${elaasPayload.memo_number || "-"}
วันที่บันทึก: ${elaasPayload.memo_date_thai || "-"}`.trim();
    navigator.clipboard.writeText(text).then(() => {
      setCopiedField("all");
      setTimeout(() => setCopiedField(null), 2000);
    });
  };

  const handleSaveElaas = async () => {
    setElaasSaving(true);
    setElaasError("");
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}/elaas-payload/save`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(await res.text());
      setElaasSaved(true);
      await fetchCaseDetails();
      await fetchTimeline();
    } catch (err: any) {
      setElaasError(err.message || "บันทึกไม่สำเร็จ");
    } finally {
      setElaasSaving(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = noteText.trim();
    if (!trimmed) {
      setNoteError("กรุณากรอกบันทึก");
      return;
    }
    setNoteSaving(true);
    setNoteError("");
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note_text: trimmed }),
      });
      if (!res.ok) throw new Error(await res.text());
      setNoteText("");
      await fetchNotes();
    } catch (err: any) {
      setNoteError(err.message || "บันทึกหมายเหตุไม่สำเร็จ");
    } finally {
      setNoteSaving(false);
    }
  };

  const handleStatusAction = async (action: "submitted" | "completed") => {
    setStatusActionLoading(action);
    setStatusActionError("");
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}/status/${action}`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(await res.text());
      await fetchCaseDetails();
      await fetchTimeline();
    } catch (err: any) {
      setStatusActionError(err.message || "ปรับสถานะไม่สำเร็จ");
    } finally {
      setStatusActionLoading(null);
    }
  };

  const handleBudgetSelection = async (budgetLineId: number) => {
    setBudgetSelecting(budgetLineId);
    setBudgetError("");
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/budget/cases/${caseId}/selection`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ budget_line_id: budgetLineId }),
      });
      if (!res.ok) throw new Error(await res.text());
      await fetchBudgetMatch();
      await fetchReadiness();
      await fetchElaas();
    } catch (err: any) {
      setBudgetError(err.message || "เลือกงบประมาณไม่สำเร็จ");
    } finally {
      setBudgetSelecting(null);
    }
  };

  const fetchCaseDetails = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}`, {
        cache: "no-store",
      });
      if (!res.ok) {
        throw new Error("ไม่สามารถดึงข้อมูลรายละเอียดเคสได้");
      }
      const data = await res.json();
      setCaseData(data);
    } catch (err: any) {
      setError(err.message || "เกิดข้อผิดพลาดในการโหลดข้อมูล");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (caseId) {
      fetchCaseDetails();
      fetchReadiness();
      fetchElaas();
      fetchTimeline();
      fetchNotes();
      fetchBudgetMatch();
    }
  }, [caseId]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError("กรุณาเลือกไฟล์ที่ต้องการอัปโหลด");
      return;
    }

    setUploading(true);
    setUploadError("");
    setUploadSuccess(false);

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("document_type", documentType);

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}/documents`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(await res.text());
      }

      setUploadSuccess(true);
      setSelectedFile(null);
      // Refresh case details to update documents list
      await fetchCaseDetails();
      await fetchReadiness();
      await fetchTimeline();
    } catch (err: any) {
      setUploadError(err.message || "อัปโหลดเอกสารไม่สำเร็จ");
    } finally {
      setUploading(false);
    }
  };

  const handleProcessDocument = async (docId: number) => {
    setProcessingDocs((prev) => ({ ...prev, [docId]: true }));
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}/documents/${docId}/process`, {
        method: "POST",
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "ไม่สามารถวิเคราะห์เอกสารได้");
      }
      await fetchCaseDetails();
      await fetchReadiness();
      await fetchTimeline();
    } catch (err: any) {
      alert(err.message || "เกิดข้อผิดพลาดในการวิเคราะห์เอกสาร");
    } finally {
      setProcessingDocs((prev) => ({ ...prev, [docId]: false }));
    }
  };

  const handleGenerateMemo = async (e: React.FormEvent) => {
    e.preventDefault();
    setMemoGenerating(true);
    setMemoError("");
    setMemoDownloadUrl(null);
    try {
      const dikaRes = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}/dika`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dika_no: dikaNo,
          dika_date: dikaDate,
          payee_name: payeeName,
          memo_number: memoNumber,
          memo_date: memoDate,
        }),
      });
      if (!dikaRes.ok) {
        throw new Error(await dikaRes.text());
      }
      const genRes = await fetch(`http://127.0.0.1:8000/api/cases/${caseId}/memo/generate`, {
        method: "POST",
      });
      if (!genRes.ok) {
        throw new Error(await genRes.text());
      }
      const genData = await genRes.json();
      setMemoDownloadUrl(`http://127.0.0.1:8000${genData.download_url}`);
      await fetchCaseDetails();
      await fetchReadiness();
      await fetchTimeline();
    } catch (err: any) {
      setMemoError(err.message || "เกิดข้อผิดพลาดในการสร้างเอกสาร");
    } finally {
      setMemoGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-500 font-medium animate-pulse">กำลังโหลดรายละเอียดเคส...</p>
      </div>
    );
  }

  if (error || !casedata) {
    return (
      <div className="max-w-4xl mx-auto p-6 bg-red-50 border-l-4 border-red-500 rounded shadow-sm">
        <h3 className="font-bold text-red-800 text-lg">เกิดข้อผิดพลาด</h3>
        <p className="text-red-700 mt-1">{error || "ไม่พบเคสที่ระบุ"}</p>
        <Link
          href="/"
          className="inline-block mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-semibold hover:bg-red-700 transition"
        >
          กลับหน้าหลัก
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-[1200px] mx-auto space-y-6">
      {/* Breadcrumb Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2 text-sm text-slate-500 mb-1">
            <Link href="/" className="hover:underline">แดชบอร์ด</Link>
            <span>/</span>
            <span className="font-medium text-slate-700">รายละเอียดเคส</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
            เลขแฟ้ม: <span className="font-mono text-[#1e3a5f]">{casedata.case_number}</span>
            <span className={`px-2.5 py-0.5 text-xs rounded-full font-bold uppercase tracking-wide border
              ${casedata.status === 'draft' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                casedata.status === 'completed' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                'bg-green-50 text-green-700 border-green-200'}
            `}>
              {displayStatus(casedata.status)}
            </span>
          </h2>
        </div>
        <Link href="/" className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg shadow-sm text-sm font-semibold hover:bg-slate-50 transition">
          ← กลับไปแดชบอร์ด
        </Link>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left 2 Columns: Details & Documents */}
        <div className="col-span-2 space-y-6">
          {/* Card: Case Details */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
            <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-500 flex items-center justify-center text-lg">📋</div>
              <h3 className="font-bold text-[16px] text-slate-800">ข้อมูลใบเบิกจ่ายสาธารณูปโภค</h3>
            </div>

            <div className="grid grid-cols-2 gap-y-4 gap-x-6 text-sm">
              <div>
                <span className="text-slate-400 block text-xs font-semibold uppercase tracking-wider mb-0.5">ประเภทการเบิกจ่าย</span>
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <span className="w-6 h-6 rounded bg-slate-50 text-slate-600 flex items-center justify-center text-xs">
                    {casedata.case_type === 'utility' ? '⚡' : casedata.case_type === 'office' ? '📦' : '📎'}
                  </span>
                  {casedata.case_type === 'utility' ? 'ค่าสาธารณูปโภค' : casedata.case_type === 'office' ? 'วัสดุสำนักงาน' : 'อื่นๆ'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-xs font-semibold uppercase tracking-wider mb-0.5">ปีงบประมาณ</span>
                <span className="font-semibold text-slate-700">พ.ศ. {casedata.fiscal_year_be}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-xs font-semibold uppercase tracking-wider mb-0.5">เดือนประจำการ</span>
                <span className="font-semibold text-slate-700">{casedata.work_month}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-xs font-semibold uppercase tracking-wider mb-0.5">กลุ่มค่าใช้จ่าย</span>
                <span className="font-semibold text-slate-700">{casedata.expense_group}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-xs font-semibold uppercase tracking-wider mb-0.5">หน่วยงานเบิก</span>
                <span className="font-semibold text-slate-700">{casedata.department}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-xs font-semibold uppercase tracking-wider mb-0.5">ฝ่าย / งาน</span>
                <span className="font-semibold text-slate-700">{casedata.division || "-"}</span>
              </div>
              <div className="col-span-2">
                <span className="text-slate-400 block text-xs font-semibold uppercase tracking-wider mb-0.5">หมายเหตุ</span>
                <p className="text-slate-600 mt-1 bg-slate-50 p-3 rounded-lg border border-slate-100 italic">
                  {casedata.note || "ไม่มีหมายเหตุเพิ่มเติม"}
                </p>
              </div>
            </div>
          </div>

          {/* Card: Document Registry List */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center">
              <h3 className="font-bold text-[16px] text-slate-800 flex items-center gap-2">
                <span>📁 แฟ้มเอกสารแนบในเคส</span>
                <span className="text-[12px] font-normal text-slate-400">({casedata.documents.length} รายการ)</span>
              </h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[11px] font-semibold border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3">ชื่อไฟล์เอกสาร</th>
                    <th className="px-6 py-3">ประเภทเอกสาร</th>
                    <th className="px-6 py-3">วันที่เพิ่ม</th>
                    <th className="px-6 py-3">ข้อมูลบิลที่ดึงได้</th>
                    <th className="px-6 py-3 text-right">การจัดการ</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {casedata.documents.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-slate-500 italic">
                        ยังไม่มีเอกสารอัปโหลดสำหรับเคสนี้
                      </td>
                    </tr>
                  )}
                  {casedata.documents.map((doc) => {
                    const isProcessing = !!processingDocs[doc.id];
                    const header = doc.bill_header;
                    return (
                      <tr key={doc.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2.5">
                            <span className="w-8 h-8 rounded-lg bg-red-50 text-red-500 flex items-center justify-center font-bold text-xs uppercase border border-red-100">
                              {doc.file_type}
                            </span>
                            <div>
                              <div className="font-bold text-slate-700">{doc.file_name}</div>
                              <div className="text-[11px] text-slate-400 font-mono truncate max-w-[180px]">{doc.file_path}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-0.5 text-[11px] rounded font-bold border
                            ${doc.document_type === 'bill' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                              doc.document_type === 'receipt' ? 'bg-green-50 text-green-700 border-green-200' :
                              'bg-slate-50 text-slate-600 border-slate-200'}
                          `}>
                            {doc.document_type === 'bill' ? 'ใบแจ้งหนี้ / บิล' :
                             doc.document_type === 'receipt' ? 'ใบเสร็จรับเงิน' : 'อื่นๆ'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-slate-500 text-xs">
                          {new Date(doc.created_at).toLocaleString('th-TH')}
                        </td>
                        <td className="px-6 py-4">
                          {header ? (
                            header.status === 'extracted' ? (
                              <div className="text-xs space-y-0.5 text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 max-w-[200px]">
                                <div><span className="font-semibold text-slate-400">ผู้ให้บริการ:</span> <span className="font-bold text-slate-700">{header.provider || "-"}</span></div>
                                <div><span className="font-semibold text-slate-400">วันที่บิล:</span> <span className="font-semibold text-slate-700">{header.bill_date ? new Date(header.bill_date).toLocaleDateString('th-TH') : "-"}</span></div>
                                <div><span className="font-semibold text-slate-400">ยอดสุทธิ:</span> <span className="font-bold text-blue-600">{header.total_amount.toLocaleString('th-TH')} บาท</span></div>
                              </div>
                            ) : header.status === 'failed' ? (
                              <span className="px-2 py-0.5 text-xs rounded bg-red-50 text-red-700 border border-red-200 font-bold">
                                ⚠️ ล้มเหลว
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 text-xs rounded bg-amber-50 text-amber-700 border border-amber-200 font-bold">
                                {header.status}
                              </span>
                            )
                          ) : (
                            <span className="text-xs text-slate-400 italic">ยังไม่ได้วิเคราะห์</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex flex-col items-end gap-2">
                            {doc.document_type === 'bill' && (
                              <button
                                disabled={isProcessing}
                                onClick={() => handleProcessDocument(doc.id)}
                                className="px-3 py-1 bg-gradient-to-br from-blue-600 to-indigo-700 text-white rounded text-xs font-bold hover:opacity-90 disabled:opacity-50 transition shadow-sm"
                              >
                                {isProcessing ? (
                                  <span className="flex items-center gap-1">
                                    <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                                    กำลังวิเคราะห์...
                                  </span>
                                ) : (
                                  "⚡ วิเคราะห์บิล (Run OCR)"
                                )}
                              </button>
                            )}
                            <span className="text-xs text-blue-500 hover:text-blue-700 font-semibold cursor-pointer underline">
                              เปิดดูไฟล์ (Local)
                            </span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right 1 Column: Upload Panel & Validator */}
        <div className="col-span-1 space-y-6">
          {/* Card: Readiness Validator Panel */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-500 flex items-center justify-center text-lg">🛡️</div>
                <h3 className="font-bold text-[16px] text-slate-800">สถานะความพร้อม</h3>
              </div>
              {loadingReadiness && <span className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></span>}
            </div>

            {loadingReadiness ? (
              <div className="flex flex-col items-center justify-center py-8 space-y-3">
                <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                <div className="text-xs text-slate-500 font-medium">กำลังตรวจสอบความพร้อม...</div>
              </div>
            ) : readinessData ? (
              <div className="space-y-4">
                <div className={`p-3 rounded-lg text-center border font-bold ${readinessData.ready ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
                  {readinessData.ready ? '✅ พร้อมส่งเรื่อง (READY)' : '❌ ยังไม่พร้อม (NOT READY)'}
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center border-b border-slate-50 pb-1">
                    <span className="text-slate-600">เอกสารแนบ</span>
                    <span>{readinessData.summary?.document_status ? '✅' : '❌'}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-slate-50 pb-1">
                    <span className="text-slate-600">สกัดข้อมูล (OCR)</span>
                    <span>{readinessData.summary?.ocr_status ? '✅' : '❌'}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-slate-50 pb-1">
                    <span className="text-slate-600">ข้อมูลฎีกา</span>
                    <span>{readinessData.summary?.dika_status ? '✅' : '❌'}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-slate-50 pb-1">
                    <span className="text-slate-600">สร้างเอกสาร Word</span>
                    <span>{readinessData.summary?.memo_status ? '✅' : '❌'}</span>
                  </div>
                  <div className="flex justify-between items-center bg-slate-50 p-2 rounded-lg mt-2 border border-slate-100">
                    <span className="text-slate-700 font-semibold text-xs">สถานะงบประมาณ</span>
                    <span className={`text-xs px-2 py-1 rounded font-bold border ${readinessData.budget_ok ? "bg-green-100 text-green-700 border-green-200 shadow-sm" : "bg-red-100 text-red-700 border-red-200 shadow-sm"}`}>
                      {readinessData.budget_ok ? '✅ เพียงพอ' : '❌ ไม่เพียงพอ / ไม่พบ'}
                    </span>
                  </div>
                </div>

                {readinessData.blockers && readinessData.blockers.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <div className="text-xs font-bold text-red-600 uppercase tracking-wider">ข้อขัดข้อง (Blockers)</div>
                    <div className="space-y-1.5">
                      {readinessData.blockers.map((b: string, idx: number) => (
                        <div key={idx} className="p-2.5 bg-red-50 border border-red-100 rounded-lg text-xs font-medium text-red-800 flex gap-2 items-start">
                          <span className="shrink-0 mt-0.5">❌</span>
                          <span className="leading-relaxed">{b}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {readinessData.warnings && readinessData.warnings.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <div className="text-xs font-bold text-amber-600 uppercase tracking-wider">ข้อควรระวัง (Warnings)</div>
                    <div className="space-y-1.5">
                      {readinessData.warnings.map((w: string, idx: number) => {
                        const isDuplicate = w.includes("ซ้ำ") || w.includes("Duplicate") || w.includes("ตรงกัน");
                        return (
                          <div key={idx} className={`p-2.5 rounded-lg text-xs font-medium flex gap-2 items-start ${
                            isDuplicate ? 'bg-orange-100 border border-orange-300 text-orange-900 shadow-sm' : 'bg-amber-50 border border-amber-100 text-amber-800'
                          }`}>
                            <span className="shrink-0 mt-0.5">{isDuplicate ? '🚨' : '⚠️'}</span>
                            <span className="leading-relaxed">{w}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6 text-sm text-slate-400 italic">
                ไม่พบข้อมูลความพร้อม
              </div>
            )}
          </div>

          {/* Card: Budget Match */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center text-lg">💰</div>
                <h3 className="font-bold text-[16px] text-slate-800">งบประมาณที่ใช้</h3>
              </div>
              {budgetLoading && <span className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></span>}
            </div>

            {budgetError && (
              <div className="p-2 bg-red-50 border border-red-100 rounded text-xs text-red-700 break-words">{budgetError}</div>
            )}

            {!budgetMatch ? (
              <div className="text-center py-4 text-xs text-slate-400 italic">ยังไม่มีข้อมูลงบประมาณ</div>
            ) : budgetMatch.selected ? (
              <div className="space-y-2">
                <div className={`p-2.5 rounded-lg border text-xs font-bold ${
                  budgetMatch.status === "selected"
                    ? "bg-blue-50 text-blue-700 border-blue-200"
                    : "bg-green-50 text-green-700 border-green-200"
                }`}>
                  {budgetMatch.status === "selected" ? "เลือกงบประมาณด้วยตนเองแล้ว" : "พบงบประมาณที่ตรงกัน"}
                </div>
                <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-xs space-y-1">
                  <div className="font-bold text-slate-700">{budgetMatch.selected.expense_type}</div>
                  <div className="text-slate-500">{budgetMatch.selected.department} · {budgetMatch.selected.division}</div>
                  <div className="text-slate-500">{budgetMatch.selected.appropriation_category || "-"}</div>
                  <div className="flex justify-between pt-2 border-t border-slate-200 mt-2">
                    <span className="text-slate-500">งบคงเหลือ</span>
                    <span className="font-bold text-slate-800">{budgetMatch.selected.available_amount.toLocaleString("th-TH", { minimumFractionDigits: 2 })} บาท</span>
                  </div>
                </div>
              </div>
            ) : budgetMatch.status === "ambiguous" ? (
              <div className="space-y-2">
                <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-xs font-bold text-amber-800">
                  พบหลายรายการ กรุณาเลือกงบประมาณที่ถูกต้อง
                </div>
                <div className="space-y-2">
                  {budgetMatch.candidates.map((candidate) => (
                    <button
                      key={candidate.id}
                      type="button"
                      onClick={() => handleBudgetSelection(candidate.id)}
                      disabled={budgetSelecting !== null}
                      className="w-full text-left p-2.5 bg-slate-50 border border-slate-200 rounded-lg hover:bg-blue-50 hover:border-blue-200 disabled:opacity-50"
                    >
                      <div className="flex justify-between gap-2 text-xs">
                        <span className="font-bold text-slate-700">{candidate.expense_type}</span>
                        <span className="font-bold text-slate-800">{candidate.available_amount.toLocaleString("th-TH", { minimumFractionDigits: 2 })}</span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-1">{candidate.appropriation_category || "-"} · {candidate.division}</div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-2.5 bg-red-50 border border-red-100 rounded-lg text-xs text-red-700">
                ไม่พบรายการงบประมาณที่ตรงกับเคสนี้
              </div>
            )}
          </div>

          {/* Card: Workflow Timeline and Notes */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center text-lg">🧭</div>
                <h3 className="font-bold text-[16px] text-slate-800">วงจรงานและประวัติ</h3>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200 text-[11px] font-bold">
                {displayStatus(casedata.status)}
              </span>
            </div>

            {statusActionError && (
              <div className="p-2.5 bg-red-50 border-l-4 border-red-500 text-red-700 rounded text-xs break-words">
                {statusActionError}
              </div>
            )}

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleStatusAction("submitted")}
                disabled={statusActionLoading !== null || casedata.status !== "elaas_prepared"}
                className="py-2 px-2 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 disabled:opacity-40 transition"
              >
                {statusActionLoading === "submitted" ? "กำลังบันทึก..." : "ทำเครื่องหมายว่าส่งแล้ว"}
              </button>
              <button
                type="button"
                onClick={() => handleStatusAction("completed")}
                disabled={statusActionLoading !== null || casedata.status !== "submitted_manual"}
                className="py-2 px-2 bg-emerald-600 text-white rounded-lg text-xs font-bold hover:bg-emerald-700 disabled:opacity-40 transition"
              >
                {statusActionLoading === "completed" ? "กำลังบันทึก..." : "ทำเครื่องหมายว่าเสร็จสิ้น"}
              </button>
            </div>

            <div className="space-y-2">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Timeline</div>
              {timelineError && (
                <div className="p-2 bg-red-50 border border-red-100 rounded text-xs text-red-700 break-words">{timelineError}</div>
              )}
              {timeline.length === 0 ? (
                <div className="text-center py-4 text-xs text-slate-400 italic border border-dashed border-slate-200 rounded-lg">
                  ยังไม่มีประวัติการดำเนินงาน
                </div>
              ) : (
                <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
                  {timeline.map((event) => (
                    <div key={event.id} className="border border-slate-100 rounded-lg p-2.5 bg-slate-50">
                      <div className="flex items-start justify-between gap-2">
                        <div className="font-bold text-xs text-slate-700">{eventLabels[event.event_type] || event.event_type}</div>
                        <div className="text-[10px] text-slate-400 shrink-0">{new Date(event.created_at).toLocaleString("th-TH")}</div>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-1">
                        {displayStatus(event.from_status)} → {displayStatus(event.to_status)}
                      </div>
                      {event.detail && <div className="text-xs text-slate-600 mt-1 leading-relaxed">{event.detail}</div>}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-2 pt-3 border-t border-slate-100">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">บันทึกผู้ปฏิบัติงาน</div>
              <form onSubmit={handleAddNote} className="space-y-2">
                <textarea
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  rows={3}
                  className="w-full border border-slate-300 rounded-lg p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  placeholder="เช่น รอเอกสารจากกองคลัง"
                />
                <button
                  type="submit"
                  disabled={noteSaving || !noteText.trim()}
                  className="w-full py-2 bg-slate-800 text-white rounded-lg text-xs font-bold hover:bg-slate-900 disabled:opacity-40 transition"
                >
                  {noteSaving ? "กำลังเพิ่มบันทึก..." : "เพิ่มบันทึก"}
                </button>
              </form>
              {noteError && (
                <div className="p-2 bg-red-50 border border-red-100 rounded text-xs text-red-700 break-words">{noteError}</div>
              )}
              {notes.length === 0 ? (
                <div className="text-center py-3 text-xs text-slate-400 italic">ยังไม่มีบันทึก</div>
              ) : (
                <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
                  {notes.map((note) => (
                    <div key={note.id} className="p-2.5 bg-amber-50 border border-amber-100 rounded-lg">
                      <div className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed">{note.note_text}</div>
                      <div className="text-[10px] text-slate-400 mt-1">{new Date(note.created_at).toLocaleString("th-TH")}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Card: e-LAAS Assist Panel — visible only when ready */}
          {elaasPayload && readinessData?.ready && (
            <div className="bg-white rounded-xl border border-emerald-200 shadow-sm p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg">🏛️</div>
                  <h3 className="font-bold text-[16px] text-slate-800">เตรียมข้อมูล e-LAAS</h3>
                </div>
                <div className="flex items-center gap-2">
                  {elaasLoading && <span className="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></span>}
                  <button
                    onClick={handleCopyAll}
                    className="px-3 py-1.5 text-[11px] font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition flex items-center gap-1.5 border border-slate-200 shadow-sm"
                  >
                    {copiedField === "all" ? "✓ คัดลอกทั้งหมดแล้ว" : "📋 คัดลอกทั้งหมด"}
                  </button>
                </div>
              </div>

              {/* Copy-ready fields */}
              <div className="space-y-1.5">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">ข้อมูลพร้อมคัดลอก</div>
                {[
                  {id: "department",     label: "หน่วยงาน",           value: elaasPayload.department},
                  {id: "fiscal_year",   label: "ปีงบประมาณ (พ.ศ.)",  value: String(elaasPayload.fiscal_year_be)},
                  {id: "work_month",    label: "เดือน",              value: elaasPayload.work_month},
                  {id: "expense_group", label: "กลุ่มค่าใช้จ่าย",   value: elaasPayload.expense_group},
                  {id: "payee_name",    label: "ผู้รับเงิน (ตามฎีกา)", value: elaasPayload.payee_name},
                  {id: "provider",      label: "ผู้ให้บริการ (ตามบิล)", value: elaasPayload.provider},
                  {id: "bill_date",     label: "วันที่บิล (ไทย)",   value: elaasPayload.bill_date_thai || "โปรดกรอกด้วยตนเอง"},
                  {id: "bill_amount",   label: "ยอดเงิน (ตัวเลข)",  value: elaasPayload.bill_amount?.toLocaleString("th-TH", {minimumFractionDigits: 2})},
                  {id: "bill_amount_t", label: "ยอดเงิน (ตัวอักษร)", value: elaasPayload.bill_amount_thai},
                  {id: "dika_number",   label: "เลขที่ฎีกา",         value: elaasPayload.dika_number},
                  {id: "dika_date",     label: "วันที่ฎีกา (ไทย)",  value: elaasPayload.dika_date_thai},
                  {id: "memo_number",   label: "เลขที่บันทึก",       value: elaasPayload.memo_number},
                  {id: "memo_date",     label: "วันที่บันทึก (ไทย)", value: elaasPayload.memo_date_thai},
                ].map(({id, label, value}) => (
                  <div key={id} className="flex items-center justify-between gap-2 py-1.5 border-b border-slate-50 last:border-0">
                    <div className="min-w-0">
                      <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">{label}</div>
                      <div className="text-xs font-bold text-slate-700 truncate max-w-[160px]" title={value}>{value || "–"}</div>
                    </div>
                    <button
                      onClick={() => handleCopyField(value || "", id)}
                      className={`shrink-0 px-2 py-0.5 text-[10px] rounded font-bold border transition ${
                        copiedField === id
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                      }`}
                    >
                      {copiedField === id ? "✓ คัดลอก" : "คัดลอก"}
                    </button>
                  </div>
                ))}
              </div>

              {/* Budget info-only */}
              {elaasPayload.budget_available !== null && elaasPayload.budget_available !== undefined && (
                <div className="bg-slate-50 rounded-lg p-2.5 flex justify-between items-center text-xs border border-slate-100">
                  <span className="text-slate-500 font-semibold">งบประมาณคงเหลือ (ข้อมูล)</span>
                  <span className="font-bold text-slate-700">{elaasPayload.budget_available?.toLocaleString("th-TH", {minimumFractionDigits: 2})} บาท</span>
                </div>
              )}

              {/* Attachment checklist */}
              <div className="space-y-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">รายการเอกสารแนบ</div>
                <div className="grid grid-cols-1 gap-1.5">
                  {elaasPayload.attachment_checklist?.map((item: any) => {
                    const isMissingRequired = item.required && !item.present;
                    return (
                      <div key={item.id} className={`flex items-center justify-between p-2 rounded border ${
                        item.present ? "bg-slate-50 border-slate-100" :
                        isMissingRequired ? "bg-red-50 border-red-200" : "bg-slate-50 border-slate-100 opacity-60"
                      }`}>
                        <div className="flex items-center gap-2 text-xs">
                          <span className={item.present ? "text-emerald-600 font-bold" : "text-slate-300"}>
                            {item.present ? "✅" : "⬜"}
                          </span>
                          <span className={`${item.present ? "text-slate-700 font-medium" : isMissingRequired ? "text-red-700 font-bold" : "text-slate-500"}`}>
                            {item.label}
                          </span>
                        </div>
                        {isMissingRequired && (
                          <span className="text-[10px] font-bold bg-red-100 text-red-600 px-1.5 py-0.5 rounded">
                            ต้องแนบ
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Operator confirmation */}
              <div className="space-y-2 pt-2 border-t border-slate-100">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">ยืนยันความถูกต้อง</div>
                {[
                  "ตรวจสอบข้อมูลถูกต้องแล้ว",
                  "เอกสารแนบครบถ้วนแล้ว",
                  "พร้อมนำเข้า e-LAAS",
                ].map((label, idx) => (
                  <label key={idx} className="flex items-center gap-2 text-xs cursor-pointer">
                    <input
                      type="checkbox"
                      checked={elaasConfirm[idx]}
                      onChange={() => setElaasConfirm(prev => {
                        const next = [...prev];
                        next[idx] = !next[idx];
                        return next;
                      })}
                      className="w-3.5 h-3.5 accent-emerald-600"
                    />
                    <span className={elaasConfirm[idx] ? "text-emerald-700 font-semibold" : "text-slate-600"}>{label}</span>
                  </label>
                ))}
              </div>

              {elaasError && (
                <div className="p-2 bg-red-50 border-l-4 border-red-500 text-red-700 rounded text-xs">{elaasError}</div>
              )}

              {elaasSaved ? (
                <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-lg text-center text-xs font-bold text-emerald-700">
                  ✅ บันทึกเตรียมข้อมูลเรียบร้อยแล้ว
                </div>
              ) : (
                <button
                  onClick={handleSaveElaas}
                  disabled={!elaasConfirm.every(Boolean) || elaasSaving}
                  className="w-full py-2.5 bg-gradient-to-br from-emerald-600 to-teal-700 text-white rounded-lg shadow text-sm font-bold hover:opacity-90 transition disabled:opacity-40"
                >
                  {elaasSaving ? "กำลังบันทึก..." : "💾 บันทึกเตรียมข้อมูล e-LAAS"}
                </button>
              )}
            </div>
          )}

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-5">
            <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
              <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-500 flex items-center justify-center text-lg">📤</div>
              <h3 className="font-bold text-[16px] text-slate-800">อัปโหลดเข้าคลังเอกสาร</h3>
            </div>

            {uploadError && (
              <div className="p-3 bg-red-50 border-l-4 border-red-500 text-red-800 rounded text-xs">
                {uploadError}
              </div>
            )}

            {uploadSuccess && (
              <div className="p-3 bg-green-50 border-l-4 border-green-500 text-green-800 rounded text-xs flex justify-between items-center">
                <span>อัปโหลดสำเร็จ!</span>
                <button onClick={() => setUploadSuccess(false)} className="underline font-bold text-green-600 hover:text-green-800">ปิด</button>
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div>
                <label className="block text-[12px] font-bold text-slate-500 uppercase tracking-wider mb-2">ประเภทเอกสารแนบ</label>
                <select
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow"
                >
                  <option value="bill">ใบแจ้งหนี้ / บิลค่าใช้จ่าย</option>
                  <option value="receipt">ใบเสร็จรับเงิน / ใบรับเงิน</option>
                  <option value="other">เอกสารอื่นๆ</option>
                </select>
              </div>

              {/* Drag & Drop File Zone */}
              <div
                className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer relative
                  ${dragActive ? 'border-blue-500 bg-blue-50/50' : 'border-slate-300 hover:bg-slate-50/50'}
                `}
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  id="file-upload-input"
                  onChange={handleFileChange}
                  className="hidden"
                  accept=".pdf,.png,.jpg,.jpeg"
                />
                <label htmlFor="file-upload-input" className="cursor-pointer">
                  <div className="w-10 h-10 bg-slate-50 text-slate-400 rounded-full flex items-center justify-center text-lg mx-auto mb-2 border border-slate-100">
                    📂
                  </div>
                  {selectedFile ? (
                    <div>
                      <div className="font-bold text-slate-700 text-xs break-all">{selectedFile.name}</div>
                      <div className="text-[10px] text-slate-400 mt-1">{(selectedFile.size / 1024).toFixed(1)} KB</div>
                      <span className="text-[11px] text-blue-500 hover:underline font-semibold block mt-2">เปลี่ยนไฟล์</span>
                    </div>
                  ) : (
                    <div>
                      <h4 className="font-bold text-slate-700 text-xs mb-1">เลือกไฟล์ หรือลากมาวาง</h4>
                      <p className="text-[10px] text-slate-400">PDF, PNG, JPG (สูงสุด 10MB)</p>
                    </div>
                  )}
                </label>
              </div>

              <button
                type="submit"
                disabled={uploading || !selectedFile}
                className="w-full py-2.5 bg-gradient-to-br from-[#1e3a5f] to-[#2d5a8e] text-white rounded-lg shadow text-sm font-bold hover:opacity-90 transition disabled:opacity-50"
              >
                {uploading ? "กำลังอัปโหลด..." : "อัปโหลดเข้าแฟ้มเอกสาร"}
              </button>
            </form>
          </div>

          {/* Card: Memo Generation Panel */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-5">
            <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
              <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-500 flex items-center justify-center text-lg">📝</div>
              <h3 className="font-bold text-[16px] text-slate-800">สร้างเอกสารเบิกจ่าย</h3>
            </div>

            {memoError && (
              <div className="p-3 bg-red-50 border-l-4 border-red-500 text-red-800 rounded text-xs break-words">
                {memoError}
              </div>
            )}

            {memoDownloadUrl ? (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center space-y-3">
                <div className="text-green-700 font-bold text-sm">สร้างเอกสารสำเร็จ!</div>
                <a
                  href={memoDownloadUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-block w-full py-2 bg-green-600 text-white rounded-lg shadow text-sm font-bold hover:bg-green-700 transition"
                >
                  📥 ดาวน์โหลด Word
                </a>
                <button
                  onClick={() => setMemoDownloadUrl(null)}
                  className="text-xs text-green-600 underline font-semibold hover:text-green-800"
                >
                  สร้างใหม่
                </button>
              </div>
            ) : (
              <form onSubmit={handleGenerateMemo} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="col-span-2">
                    <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">เลขที่ฎีกา</label>
                    <input type="text" required value={dikaNo} onChange={e => setDikaNo(e.target.value)} className="w-full border border-slate-300 rounded-lg p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" placeholder="เช่น 123/2569" />
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">วันที่ฎีกา</label>
                    <input type="date" required value={dikaDate} onChange={e => setDikaDate(e.target.value)} className="w-full border border-slate-300 rounded-lg p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">วันที่ทำรายการ</label>
                    <input type="date" required value={memoDate} onChange={e => setMemoDate(e.target.value)} className="w-full border border-slate-300 rounded-lg p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">ชื่อผู้รับเงิน / ผู้ให้บริการ</label>
                    <input type="text" required value={payeeName} onChange={e => setPayeeName(e.target.value)} className="w-full border border-slate-300 rounded-lg p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" placeholder="ระบุชื่อบริษัทหรือผู้รับเงิน" />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">เลขที่เอกสารภายใน</label>
                    <input type="text" required value={memoNumber} onChange={e => setMemoNumber(e.target.value)} className="w-full border border-slate-300 rounded-lg p-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" placeholder="เช่น กค 001/2569" />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={memoGenerating}
                  className="w-full mt-2 py-2.5 bg-gradient-to-br from-emerald-600 to-green-700 text-white rounded-lg shadow text-sm font-bold hover:opacity-90 transition disabled:opacity-50"
                >
                  {memoGenerating ? "กำลังสร้างเอกสาร..." : "📄 สร้าง Word Document"}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
