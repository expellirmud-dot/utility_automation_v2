"use client";

import React, { useState } from "react";
import Link from "next/link";

type PreviewRow = {
  row_number: number;
  department: string;
  division: string;
  expense_type: string;
  appropriation_category: string;
  initial_amount: number;
  import_action?: string;
  valid: boolean;
  errors: string[];
};

type PreviewResult = {
  valid: boolean;
  source_hash: string;
  sheet_names: string[];
  selected_sheet: string | null;
  rows: PreviewRow[];
  errors: string[];
  summary: {
    row_count: number;
    total_initial_amount: number;
  };
};

type CommitResult = {
  message: string;
  created: number;
  updated: number;
  lines_processed: number;
};

export default function BudgetImportPage() {
  const [fiscalYear, setFiscalYear] = useState("2569");
  const [file, setFile] = useState<File | null>(null);
  const [sheetNames, setSheetNames] = useState<string[]>([]);
  const [selectedSheet, setSelectedSheet] = useState("");
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [commitResult, setCommitResult] = useState<CommitResult | null>(null);
  const [loadingSheets, setLoadingSheets] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [error, setError] = useState("");

  const resetResults = () => {
    setPreview(null);
    setCommitResult(null);
    setError("");
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] || null;
    setFile(nextFile);
    setSheetNames([]);
    setSelectedSheet("");
    resetResults();
    if (!nextFile) return;

    setLoadingSheets(true);
    try {
      const formData = new FormData();
      formData.append("file", nextFile);
      const res = await fetch("http://127.0.0.1:8000/api/budget/import/sheets", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setSheetNames(data.sheet_names || []);
      if (data.sheet_names?.length === 1) setSelectedSheet(data.sheet_names[0]);
    } catch (err: any) {
      setError(err.message || "อ่านรายชื่อ worksheet ไม่สำเร็จ");
    } finally {
      setLoadingSheets(false);
    }
  };

  const handlePreview = async () => {
    if (!file) {
      setError("กรุณาเลือกไฟล์ Excel");
      return;
    }
    setPreviewing(true);
    setCommitResult(null);
    setError("");
    try {
      const formData = new FormData();
      formData.append("fiscal_year_be", fiscalYear);
      formData.append("file", file);
      if (selectedSheet) formData.append("sheet_name", selectedSheet);

      const res = await fetch("http://127.0.0.1:8000/api/budget/import/preview", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(await res.text());
      setPreview(await res.json());
    } catch (err: any) {
      setError(err.message || "Preview ไม่สำเร็จ");
    } finally {
      setPreviewing(false);
    }
  };

  const handleCommit = async () => {
    if (!file || !preview?.valid) return;
    setCommitting(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("fiscal_year_be", fiscalYear);
      formData.append("source_hash", preview.source_hash);
      formData.append("file", file);
      if (preview.selected_sheet) formData.append("sheet_name", preview.selected_sheet);

      const res = await fetch("http://127.0.0.1:8000/api/budget/import/commit", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(await res.text());
      setCommitResult(await res.json());
    } catch (err: any) {
      setError(err.message || "Commit ไม่สำเร็จ");
    } finally {
      setCommitting(false);
    }
  };

  return (
    <div className="max-w-[1200px] mx-auto space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">นำเข้างบประมาณจาก Excel</h2>
          <p className="text-slate-500 text-sm mt-1">Preview และตรวจสอบข้อมูลก่อนบันทึกเข้าระบบ</p>
        </div>
        <Link href="/" className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg shadow-sm text-sm font-semibold hover:bg-slate-50 transition">
          ← กลับแดชบอร์ด
        </Link>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-5">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-[12px] font-bold text-slate-500 uppercase tracking-wider mb-2">ปีงบประมาณ</label>
            <input
              value={fiscalYear}
              onChange={(e) => {
                setFiscalYear(e.target.value);
                resetResults();
              }}
              className="w-full border border-slate-300 rounded-lg p-2.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-[12px] font-bold text-slate-500 uppercase tracking-wider mb-2">ไฟล์ Excel</label>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
              className="w-full border border-slate-300 rounded-lg p-2 text-sm bg-white"
            />
          </div>
          <div>
            <label className="block text-[12px] font-bold text-slate-500 uppercase tracking-wider mb-2">Worksheet</label>
            <select
              value={selectedSheet}
              onChange={(e) => {
                setSelectedSheet(e.target.value);
                resetResults();
              }}
              disabled={loadingSheets || sheetNames.length === 0}
              className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white disabled:opacity-50"
            >
              <option value="">{loadingSheets ? "กำลังอ่าน..." : "-- เลือก worksheet --"}</option>
              {sheetNames.map((sheet) => (
                <option key={sheet} value={sheet}>{sheet}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handlePreview}
            disabled={!file || previewing || (sheetNames.length > 1 && !selectedSheet)}
            className="px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 disabled:opacity-40"
          >
            {previewing ? "กำลัง Preview..." : "Preview"}
          </button>
          <button
            onClick={handleCommit}
            disabled={!preview?.valid || committing}
            className="px-5 py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-bold hover:bg-emerald-700 disabled:opacity-40"
          >
            {committing ? "กำลังบันทึก..." : "Confirm Import"}
          </button>
        </div>

        {error && <div className="p-3 bg-red-50 border-l-4 border-red-500 text-red-700 rounded text-xs break-words">{error}</div>}
        {commitResult && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-sm text-emerald-800">
            บันทึกสำเร็จ: สร้างใหม่ {commitResult.created} รายการ, อัปเดต {commitResult.updated} รายการ
          </div>
        )}
      </div>

      {preview && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200 flex justify-between items-center">
            <div>
              <h3 className="font-bold text-[16px] text-slate-800">Preview</h3>
              <p className="text-xs text-slate-500 mt-1">
                {preview.selected_sheet || "-"} · {preview.summary.row_count} rows · รวม {preview.summary.total_initial_amount.toLocaleString("th-TH", { minimumFractionDigits: 2 })} บาท
              </p>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${preview.valid ? "bg-green-50 text-green-700 border-green-200" : "bg-red-50 text-red-700 border-red-200"}`}>
              {preview.valid ? "VALID" : "INVALID"}
            </span>
          </div>

          {preview.errors.length > 0 && (
            <div className="m-5 p-3 bg-red-50 border border-red-100 rounded text-xs text-red-700 space-y-1">
              {preview.errors.map((item, idx) => <div key={idx}>{item}</div>)}
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Row</th>
                  <th className="px-4 py-3">หน่วยงาน</th>
                  <th className="px-4 py-3">ฝ่าย/งาน</th>
                  <th className="px-4 py-3">ประเภทรายจ่าย</th>
                  <th className="px-4 py-3">หมวดงบประมาณ</th>
                  <th className="px-4 py-3 text-right">งบตั้งต้น</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Errors</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {preview.rows.map((row) => (
                  <tr key={row.row_number} className={row.valid ? "hover:bg-slate-50" : "bg-red-50/50"}>
                    <td className="px-4 py-3 font-mono">{row.row_number}</td>
                    <td className="px-4 py-3 font-semibold text-slate-700">{row.department}</td>
                    <td className="px-4 py-3">{row.division}</td>
                    <td className="px-4 py-3">{row.expense_type}</td>
                    <td className="px-4 py-3">{row.appropriation_category}</td>
                    <td className="px-4 py-3 text-right font-bold">{row.initial_amount.toLocaleString("th-TH", { minimumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 font-bold">{row.import_action || "-"}</span>
                    </td>
                    <td className="px-4 py-3 text-red-700">{row.errors.join("; ") || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
