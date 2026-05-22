export const dynamic = "force-dynamic";
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
  appropriation_category: string;
  initial_amount: number;
  deducted_amount: number;
  available_amount: number;
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
  let totalPaid = 0;
  budgets.forEach((b: BudgetLine) => totalBudget += b.initial_amount);
  budgets.forEach((b: BudgetLine) => totalPaid += b.deducted_amount || 0);

  const stats = {
    fy: 2569,
    totalBudget: totalBudget,
    totalPaid: totalPaid,
    remaining: totalBudget - totalPaid,
    openCases: cases.filter((c: Case) => c.status !== 'closed').length
  };

  return (
    <div className="space-y-8 max-w-[1200px] mx-auto pb-12">
      {/* Banner / Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-r from-red-600 via-rose-700 to-red-800 rounded-2xl shadow-xl border border-red-500/20 text-white p-6 md:p-8 flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="space-y-4 max-w-xl text-center md:text-left z-10">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-xs font-semibold tracking-wide border border-white/20">
            <span className="w-1.5 h-1.5 bg-red-400 rounded-full animate-ping"></span>
            ระบบเบิกจ่ายเทศบาล
          </div>
          <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight leading-tight">
            ระบบติดตามการเบิกจ่ายงบประมาณ
          </h2>
          <p className="text-red-100 text-sm md:text-base font-light leading-relaxed">
            ติดตาม ตรวจสอบ และวิเคราะห์ข้อมูลการเบิกจ่ายค่าสาธารณูปโภค 
            ปีงบประมาณ {stats.fy} ของกองต่างๆ อย่างโปร่งใสและมีประสิทธิภาพ
          </p>
          <div className="flex flex-wrap gap-3 pt-2 justify-center md:justify-start">
            <Link href="/create" className="px-5 py-2.5 bg-white text-red-700 hover:bg-red-50 rounded-xl shadow-md text-sm font-bold transition duration-200 ease-in-out transform hover:-translate-y-0.5 active:translate-y-0 flex items-center gap-2">
              <span>➕</span> สร้างเคสใหม่
            </Link>
            <Link href="/budget" className="px-5 py-2.5 bg-red-500/20 hover:bg-red-500/30 text-white border border-white/20 rounded-xl shadow-sm text-sm font-semibold transition duration-200 ease-in-out transform hover:-translate-y-0.5 active:translate-y-0 flex items-center gap-2">
              <span>💰</span> นำเข้างบประมาณ
            </Link>
          </div>
        </div>
        <div className="relative w-48 h-48 md:w-56 md:h-56 flex-shrink-0 flex items-center justify-center select-none z-10">
          <div className="absolute inset-0 bg-white/10 blur-2xl rounded-full"></div>
          <img 
            src="/abstract_3d_red_white.png" 
            alt="Dashboard Banner Art" 
            className="w-full h-full object-contain drop-shadow-2xl transform hover:scale-105 transition-transform duration-300"
          />
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Stat 1 */}
        <div className="bg-white p-6 rounded-2xl border border-red-100/50 shadow-sm hover:shadow-md transition-all duration-300 relative group overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[3px] bg-red-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300"></div>
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 rounded-xl bg-red-50 text-red-600 flex items-center justify-center text-xl font-bold shadow-inner">
              📋
            </div>
            <span className="text-[11px] font-bold text-red-600/70 bg-red-50 px-2 py-0.5 rounded-full">Total</span>
          </div>
          <div className="text-3xl font-extrabold text-slate-800 tracking-tight mb-1">{cases.length}</div>
          <div className="text-slate-500 text-xs font-medium">เคสทั้งหมดในระบบ</div>
        </div>
        
        {/* Stat 2 */}
        <div className="bg-white p-6 rounded-2xl border border-red-100/50 shadow-sm hover:shadow-md transition-all duration-300 relative group overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[3px] bg-amber-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300"></div>
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center text-xl font-bold shadow-inner">
              ⏳
            </div>
            <span className="text-[11px] font-bold text-amber-600/70 bg-amber-50 px-2 py-0.5 rounded-full">Pending</span>
          </div>
          <div className="text-3xl font-extrabold text-slate-800 tracking-tight mb-1">{stats.openCases}</div>
          <div className="text-slate-500 text-xs font-medium">เคสที่รอดำเนินการ</div>
        </div>

        {/* Stat 3 */}
        <div className="bg-white p-6 rounded-2xl border border-red-100/50 shadow-sm hover:shadow-md transition-all duration-300 relative group overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[3px] bg-emerald-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300"></div>
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl font-bold shadow-inner">
              ✅
            </div>
            <span className="text-[11px] font-bold text-emerald-600/70 bg-emerald-50 px-2 py-0.5 rounded-full">Done</span>
          </div>
          <div className="text-3xl font-extrabold text-slate-800 tracking-tight mb-1">
            {cases.filter((c: Case) => c.status === 'closed').length}
          </div>
          <div className="text-slate-500 text-xs font-medium">เคสที่ดำเนินการเสร็จสิ้น</div>
        </div>

        {/* Stat 4 */}
        <div className="bg-white p-6 rounded-2xl border border-red-100/50 shadow-sm hover:shadow-md transition-all duration-300 relative group overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[3px] bg-red-600 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300"></div>
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 rounded-xl bg-red-50 text-red-600 flex items-center justify-center text-xl font-bold shadow-inner">
              💰
            </div>
            <span className="text-[11px] font-bold text-red-600/70 bg-red-50 px-2 py-0.5 rounded-full">Paid</span>
          </div>
          <div className="text-3xl font-extrabold text-slate-800 tracking-tight mb-1">
            ฿{(stats.totalPaid/1000000).toFixed(2)}M
          </div>
          <div className="text-slate-500 text-xs font-medium">เบิกจ่ายสะสม (ปีงบฯ {stats.fy})</div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Panel: Cases (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-red-100/30 shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 bg-red-600 rounded-full"></span>
              <h3 className="font-bold text-[17px] text-slate-800">รายการใบเบิกสาธารณูปโภคล่าสุด</h3>
            </div>
            <button className="text-xs font-bold text-red-600 hover:text-red-800 bg-red-50 px-3 py-1.5 rounded-lg transition">
              ดูทั้งหมด
            </button>
          </div>
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/70 border-b border-slate-100 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
                  <th className="px-6 py-4">เลขแฟ้มกรณี</th>
                  <th className="px-6 py-4">ประเภท/สังกัดหน่วยงาน</th>
                  <th className="px-6 py-4">ยอดเงินสุทธิ</th>
                  <th className="px-6 py-4">สถานะกระบวนการ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {cases.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-slate-400 font-medium">
                      <div className="text-3xl mb-2">📥</div>
                      ไม่พบข้อมูลเคสปัจจุบันในฐานข้อมูล
                    </td>
                  </tr>
                )}
                {cases.map((c: Case) => (
                  <tr key={c.id} className="hover:bg-red-50/10 transition-colors group">
                    <td className="px-6 py-4">
                      <Link href={`/cases/${c.id}`} className="font-bold text-[#1e3a5f] hover:text-red-700 hover:underline transition-colors flex flex-col">
                        <span>{c.case_number}</span>
                        <span className="text-[11px] text-slate-400 font-normal mt-1">
                          {new Date(c.created_at).toLocaleString('th-TH', { 
                            year: 'numeric', 
                            month: 'short', 
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })} น.
                        </span>
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <span className="w-9 h-9 rounded-xl bg-red-50 text-red-600 flex items-center justify-center text-base border border-red-100/40 shadow-sm">
                          {c.case_type === 'utility' ? '⚡' : c.case_type === 'office' ? '📦' : '📎'}
                        </span>
                        <div>
                          <div className="font-bold text-slate-700 text-[13px]">{c.department}</div>
                          <div className="text-[11px] text-slate-400 mt-0.5">{c.expense_group} ({c.work_month})</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-extrabold text-slate-700 text-sm">
                      ฿{(c.total_amount || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border tracking-wide uppercase shadow-sm
                        ${c.status === 'draft' 
                          ? 'bg-amber-50 text-amber-700 border-amber-200' 
                          : c.status === 'completed' 
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                          : 'bg-rose-50 text-red-700 border-red-100'}
                      `}>
                        <span className={`w-1.5 h-1.5 rounded-full mr-1.5
                          ${c.status === 'draft' ? 'bg-amber-500' : c.status === 'completed' ? 'bg-emerald-500' : 'bg-red-500'}
                        `}></span>
                        {c.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Panel: Budgets (1 col) */}
        <div className="bg-white rounded-2xl border border-red-100/30 shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-5 border-b border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 bg-red-600 rounded-full"></span>
              <h3 className="font-bold text-[17px] text-slate-800">การจัดสรรงบประมาณคงเหลือ</h3>
            </div>
          </div>
          <div className="p-6 flex-1 space-y-6 overflow-y-auto">
            {budgets.length === 0 && (
              <div className="text-center text-slate-400 py-8">
                <div className="text-3xl mb-2">📊</div>
                ไม่พบข้อมูลงบประมาณในกองของท่าน
              </div>
            )}
            {budgets.map((b: BudgetLine) => {
              const paid = b.deducted_amount || 0;
              const pct = b.initial_amount > 0 ? Math.round((paid / b.initial_amount) * 100) : 0;
              return (
                <div key={b.id} className="space-y-2 p-3.5 rounded-xl border border-slate-50 hover:border-red-100/50 hover:bg-red-50/5 transition-colors">
                  <div className="flex justify-between items-start gap-2">
                    <span className="font-bold text-[13px] text-slate-800 block line-clamp-1">
                      {b.expense_type}
                    </span>
                    <span className="text-[12px] font-bold text-slate-600 shrink-0">
                      ฿{paid.toLocaleString()} <span className="text-slate-400 font-normal">/ ฿{b.initial_amount.toLocaleString()}</span>
                    </span>
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>{b.department} · {b.division}</span>
                    <span className={`font-bold ${pct > 80 ? 'text-red-600' : pct > 60 ? 'text-amber-600' : 'text-emerald-600'}`}>
                      {pct}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden shadow-inner">
                    <div 
                      className={`h-full rounded-full transition-all duration-500
                        ${pct > 80 ? 'bg-gradient-to-r from-red-500 to-rose-600' 
                          : pct > 60 ? 'bg-gradient-to-r from-amber-400 to-amber-500' 
                          : 'bg-gradient-to-r from-emerald-400 to-emerald-500'}`} 
                      style={{ width: `${pct}%` }}
                    ></div>
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
