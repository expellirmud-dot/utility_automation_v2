import "./globals.css";
import Link from "next/link";
import React from "react";

export const metadata = {
  title: "เทศบาลตำบลด่านทับตะโก - Utility Disbursement",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="th">
      <body className="flex h-screen overflow-hidden font-sans">
        {/* Sidebar */}
        <aside className="w-64 bg-gradient-to-b from-sidebar-dark to-sidebar text-white flex flex-col">
          <div className="p-6 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-yellow-500 to-yellow-300 rounded-lg flex items-center justify-center text-xl shadow-lg">
                🏛️
              </div>
              <div>
                <h1 className="font-bold text-[15px] leading-tight text-white">เทศบาลตำบลด่านทับตะโก</h1>
                <p className="text-[11px] text-white/60 mt-0.5">Utility Disbursement</p>
              </div>
            </div>
          </div>
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            <div className="text-[10px] font-semibold text-white/40 uppercase tracking-[1.5px] mb-2 mt-4 px-3">เมนูหลัก</div>
            <Link href="/" className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/10 transition-colors text-sm font-medium">
              <span className="opacity-80">📊</span> แดชบอร์ด
            </Link>
            <Link href="/create" className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/10 transition-colors text-sm font-medium">
              <span className="opacity-80">➕</span> สร้างเคสใหม่
            </Link>
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/10 transition-colors text-sm font-medium cursor-pointer text-white/70 hover:text-white">
              <span className="opacity-80">📋</span> รายการเคส
            </div>
            
            <div className="text-[10px] font-semibold text-white/40 uppercase tracking-[1.5px] mb-2 mt-6 px-3">การจัดการ</div>
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/10 transition-colors text-sm font-medium cursor-pointer text-white/70 hover:text-white">
              <span className="opacity-80">💰</span> งบประมาณ
            </div>
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/10 transition-colors text-sm font-medium cursor-pointer text-white/70 hover:text-white">
              <span className="opacity-80">📄</span> เอกสาร
            </div>
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/10 transition-colors text-sm font-medium cursor-pointer text-white/70 hover:text-white">
              <span className="opacity-80">📈</span> รายงาน
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0 bg-[#f5f7fa] overflow-y-auto relative">
          <header className="h-[70px] bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0 sticky top-0 z-10">
            <div className="text-sm text-slate-500 flex items-center gap-2">
              <span>Home</span>
              <span>/</span>
              <span className="font-semibold text-slate-800">แดชบอร์ด</span>
            </div>
            <div className="flex items-center gap-3">
              <button className="w-10 h-10 rounded-lg border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-50 transition-colors relative">
                🔔
                <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
              </button>
            </div>
          </header>
          <main className="p-8 flex-1">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
