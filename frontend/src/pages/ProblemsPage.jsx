import { ListChecks } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import CompilerNavbar from '../components/CompilerNavbar';
import Panel from '../components/Panel';
import { api } from '../lib/api';

// Tailwind classes for each difficulty badge.
const difficultyStyles = {
  easy: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  medium: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  hard: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
};

function DifficultyBadge({ difficulty }) {
  const style = difficultyStyles[difficulty] || difficultyStyles.easy;
  return (
    <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold capitalize ${style}`}>
      {difficulty}
    </span>
  );
}

function ProblemsPage() {
  const [problems, setProblems] = useState([]);
  const [status, setStatus] = useState('loading'); // loading | ready | error

  useEffect(() => {
    async function loadProblems() {
      try {
        const { data } = await api.get('/problems');
        setProblems(data.problems);
        setStatus('ready');
      } catch {
        setStatus('error');
      }
    }
    loadProblems();
  }, []);

  return (
    <main className="min-h-screen bg-[#0d1117] text-slate-100">
      <CompilerNavbar language="cpp" onLanguageChange={() => {}} onRun={() => {}} onSave={() => {}} isBusy={false} />

      <section className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-6">
          <p className="text-sm font-semibold text-blue-400">Problem Set</p>
          <h1 className="mt-2 text-3xl font-bold text-white">Problems</h1>
          <p className="mt-2 text-slate-400">Pick a problem, read the statement, and start solving.</p>
        </div>

        <Panel title="All Problems" icon={<ListChecks size={16} />}>
          {status === 'loading' && (
            <p className="p-6 text-sm text-slate-400">Loading problems…</p>
          )}

          {status === 'error' && (
            <p className="p-6 text-sm text-rose-300">Could not load problems. Is the backend running?</p>
          )}

          {status === 'ready' && problems.length === 0 && (
            <p className="p-6 text-sm text-slate-400">
              No problems yet. Run <code className="text-slate-300">python seed_problems.py</code> in the backend.
            </p>
          )}

          {status === 'ready' && problems.length > 0 && (
            <ul className="divide-y divide-slate-800">
              {problems.map((problem, index) => (
                <li key={problem.id}>
                  <Link
                    to={`/problems/${problem.slug}`}
                    className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-slate-800/40"
                  >
                    <span className="flex min-w-0 items-center gap-3">
                      <span className="w-6 shrink-0 text-right text-sm text-slate-500">{index + 1}</span>
                      <span className="truncate text-sm font-semibold text-slate-100">{problem.title}</span>
                    </span>
                    <DifficultyBadge difficulty={problem.difficulty} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </section>
    </main>
  );
}

export default ProblemsPage;
