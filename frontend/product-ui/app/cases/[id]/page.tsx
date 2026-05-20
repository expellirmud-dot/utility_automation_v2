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
    } catch (err: any) {
      alert(err.message || "เกิดข้อผิดพลาดในการวิเคราะห์เอกสาร");
    } finally {
      setProcessingDocs((prev) => ({ ...prev, [docId]: false }));
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
              {casedata.status}
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

        {/* Right 1 Column: Upload Panel */}
        <div className="col-span-1">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-5 sticky top-[94px]">
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
        </div>
      </div>
    </div>
  );
}
