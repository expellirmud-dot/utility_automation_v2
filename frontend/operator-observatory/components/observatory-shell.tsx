import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

export function ObservatoryShell({ 
  children 
}: { 
  children: React.ReactNode; 
}) {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-white">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6 lg:p-10">
          <div className="mx-auto max-w-7xl w-full flex flex-col gap-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
