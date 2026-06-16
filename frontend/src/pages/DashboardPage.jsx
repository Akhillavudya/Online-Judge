import { Code2, FileCode2, Play, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import CompilerNavbar from '../components/CompilerNavbar';
import Panel from '../components/Panel';
import { useAuth } from '../context/AuthContext';

function DashboardPage() {
  const { user } = useAuth();

  return (
    <main className="min-h-screen bg-[#0d1117] text-slate-100">
      <CompilerNavbar language="cpp" onLanguageChange={() => {}} onRun={() => {}} onSave={() => {}} isBusy={false} />
      <section className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-8">
          <p className="text-sm font-semibold text-blue-400">Dashboard</p>
          <h1 className="mt-2 text-3xl font-bold text-white">Welcome back, {user?.name}</h1>
          <p className="mt-2 text-slate-400">Jump into your coding workspace or review saved work.</p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <Panel title="Compiler" icon={<Code2 size={16} />}>
            <div className="p-4">
              <p className="min-h-16 text-sm leading-6 text-slate-400">Run C++ programs with custom input and terminal output.</p>
              <Link className="mt-4 inline-flex h-10 items-center gap-2 rounded-md bg-blue-600 px-4 text-sm font-semibold text-white" to="/compiler">
                <Play size={16} />
                Open Compiler
              </Link>
            </div>
          </Panel>
          <Panel title="Saved Codes" icon={<FileCode2 size={16} />}>
            <div className="p-4">
              <p className="min-h-16 text-sm leading-6 text-slate-400">Save programs under your profile and reopen them anytime.</p>
              <Link className="mt-4 inline-flex h-10 items-center rounded-md border border-slate-700 px-4 text-sm font-semibold text-slate-200" to="/compiler">
                View Files
              </Link>
            </div>
          </Panel>
          <Panel title="AI Review" icon={<Sparkles size={16} />}>
            <div className="p-4">
              <p className="min-h-16 text-sm leading-6 text-slate-400">Ask Gemini Flash for code quality, complexity, and optimization tips.</p>
              <Link className="mt-4 inline-flex h-10 items-center rounded-md border border-slate-700 px-4 text-sm font-semibold text-slate-200" to="/compiler">
                Review Code
              </Link>
            </div>
          </Panel>
        </div>
      </section>
    </main>
  );
}

export default DashboardPage;
