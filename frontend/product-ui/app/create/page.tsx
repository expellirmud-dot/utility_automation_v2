"use client";
import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function CreateCase() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [caseId, setCaseId] = useState("");
  const [error, setError] = useState("");

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
      const res = await fetch("http://127.0.0.1:8000/api/cases/", {
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
              <select name="fiscal_year_be" className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow" required defaultValue="2569">
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
              <select name="expense_group" className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-shadow" required>
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
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-100">
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center text-sm">📄</div>
            <h3 className="font-bold text-[16px] text-slate-800">อัปโหลดเอกสารต้นฉบับ</h3>
          </div>
          
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-10 text-center hover:bg-slate-50 transition-colors cursor-pointer">
            <div className="w-14 h-14 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center text-2xl mx-auto mb-4">📤</div>
            <h4 className="font-bold text-slate-700 mb-1">คลิกเพื่ออัปโหลด หรือ ลากไฟล์มาวาง</h4>
            <p className="text-sm text-slate-500">รองรับไฟล์ PDF, JPG, PNG (สูงสุด 10MB ต่อไฟล์)</p>
            <p className="text-xs text-slate-400 mt-2">(MOCK: ไม่มีการอัปโหลดไฟล์จริงใน Checkpoint นี้)</p>
          </div>
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
