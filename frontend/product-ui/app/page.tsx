import Link from "next/link";

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
  created_at: string;
};

type BudgetLine = {
  id: number;
  department: string;
  division: string;
  expense_type: string;
  initial_amount: number;
  fiscal_year_be: number;
};

export default async function Dashboard() {
  let cases: Case[] = [];
  let budgets: BudgetLine[] = [];
  try {
    const casesRes = await fetch("http://127.0.0.1:8000/api/cases/", { cache: "no-store" });
    if (casesRes.ok) cases = await casesRes.json();
    
    const budgetsRes = await fetch("http://127.0.0.1:8000/api/budget/", { cache: "no-store" });
    if (budgetsRes.ok) budgets = await budgetsRes.json();
  } catch (e) {
    console.error("Backend not reachable", e);
  }

  let totalBudget = 0;
  budgets.forEach((b: BudgetLine) => totalBudget += b.initial_amount);
  
  const stats = { 
    fy: 2569, 
    totalBudget: totalBudget, 
    totalPaid: 0, 
    remaining: totalBudget, 
    openCases: cases.filter((c: Case) => c.status !== 'closed').length 
  };

  return (
    <div className="space-y-7 max-w-[1200px] mx-auto">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">แดชบอร์ดภาพรวม</h2>
          <p className="text-slate-500 text-sm mt-1">ข้อมูลสรุปการเบิกจ่ายค่าสาธารณูปโภค ปีงบประมาณ {stats.fy}</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg shadow-sm text-sm font-semibold hover:bg-slate-50 transition">
            🔄 รีเฟรช
          </button>
          <Link href="/create" className="px-4 py-2 bg-gradient-to-br from-[#1e3a5f] to-[#2d5a8e] text-white rounded-lg shadow text-sm font-semibold hover:opacity-90 transition">
            ➕ สร้างเคสใหม่
          </Link>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-2">
            <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-500 flex items-center justify-center text-xl">📋</div>
          </div>
          <div className="text-3xl font-bold text-slate-800 mb-1">{cases.length}</div>
          <div className="text-slate-500 text-[13px]">เคสทั้งหมด</div>
        </div>
        
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-2">
            <div className="w-11 h-11 rounded-xl bg-amber-50 text-amber-500 flex items-center justify-center text-xl">⏳</div>
          </div>
          <div className="text-3xl font-bold text-slate-800 mb-1">{stats.openCases}</div>
          <div className="text-slate-500 text-[13px]">รอดำเนินการ</div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-2">
            <div className="w-11 h-11 rounded-xl bg-green-50 text-green-500 flex items-center justify-center text-xl">✅</div>
          </div>
          <div className="text-3xl font-bold text-slate-800 mb-1">{cases.filter((c: Case) => c.status === 'closed').length}</div>
          <div className="text-slate-500 text-[13px]">ดำเนินการเสร็จสิ้น</div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-2">
            <div className="w-11 h-11 rounded-xl bg-purple-50 text-purple-500 flex items-center justify-center text-xl">💰</div>
          </div>
          <div className="text-3xl font-bold text-slate-800 mb-1">฿{(stats.totalPaid/1000000).toFixed(1)}M</div>
          <div className="text-slate-500 text-[13px]">เบิกจ่ายแล้ว (ปี {stats.fy})</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Panel: Cases */}
        <div className="col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-slate-200 flex justify-between items-center">
            <h3 className="font-bold text-[16px] text-slate-800">รายการเคสล่าสุด</h3>
            <button className="text-sm font-semibold text-blue-600 hover:text-blue-800">ดูทั้งหมด</button>
          </div>
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[11px] font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-5 py-3">เลขแฟ้ม</th>
                  <th className="px-5 py-3">ประเภท</th>
                  <th className="px-5 py-3">ยอดรวม</th>
                  <th className="px-5 py-3">สถานะ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {cases.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-5 py-8 text-center text-slate-500">ไม่มีข้อมูลเคส</td>
                  </tr>
                )}
                {cases.map((c: Case) => (
                  <tr key={c.id} className="hover:bg-slate-50 transition-colors cursor-pointer">
                    <td className="px-5 py-4">
                      <div className="font-bold text-[#1e3a5f]">{c.case_number}</div>
                      <div className="text-[12px] text-slate-400 mt-0.5">{new Date(c.created_at).toLocaleString('th-TH')}</div>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        <span className="w-8 h-8 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center text-sm">
                          {c.case_type === 'utility' ? '⚡' : c.case_type === 'office' ? '📦' : '📎'}
                        </span>
                        <div>
                          <div className="font-medium text-slate-700">{c.department}</div>
                          <div className="text-[12px] text-slate-500">{c.expense_group} ({c.work_month})</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4 font-bold text-slate-700">฿{(c.total_amount || 0).toLocaleString()}</td>
                    <td className="px-5 py-4">
                      <span className={`px-3 py-1 text-[11px] rounded-full font-bold uppercase tracking-wide
                        ${c.status === 'draft' ? 'bg-amber-100 text-amber-700 border border-amber-200' : 
                          c.status === 'completed' ? 'bg-purple-100 text-purple-700 border border-purple-200' :
                          'bg-green-100 text-green-700 border border-green-200'}
                      `}>
                        {c.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Panel: Budgets */}
        <div className="col-span-1 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-slate-200 flex justify-between items-center">
            <h3 className="font-bold text-[16px] text-slate-800">สถานะงบประมาณ</h3>
          </div>
          <div className="p-5 flex-1 space-y-6">
            {budgets.length === 0 && (
              <div className="text-center text-slate-500 py-4">ไม่มีข้อมูลงบประมาณ</div>
            )}
            {budgets.map((b: BudgetLine) => {
              const paid = 0; // Mock paid for now
              const pct = b.initial_amount > 0 ? Math.round((paid / b.initial_amount) * 100) : 0;
              return (
                <div key={b.id}>
                  <div className="flex justify-between text-[13px] mb-2">
                    <span className="font-bold text-slate-700">{b.expense_type} ({b.department})</span>
                    <span className="font-semibold text-slate-600">฿{paid.toLocaleString()} / ฿{b.initial_amount.toLocaleString()} <span className="text-slate-400">({pct}%)</span></span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div className={`h-full rounded-full ${pct > 60 ? 'bg-amber-500' : pct > 80 ? 'bg-red-500' : 'bg-green-500'}`} style={{ width: `${pct}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}