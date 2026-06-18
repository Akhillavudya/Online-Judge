import { History } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import CompilerNavbar from '../components/CompilerNavbar';
import Panel from '../components/Panel';
import { api } from '../lib/api';

// Human-readable label + colors for each verdict code from the judge.
const verdictMeta = {
  AC: { label: 'Accepted', style: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' },
  WA: { label: 'Wrong Answer', style: 'bg-rose-500/15 text-rose-300 border-rose-500/40' },
  TLE: { label: 'Time Limit Exceeded', style: 'bg-amber-500/15 text-amber-300 border-amber-500/40' },
  RE: { label: 'Runtime Error', style: 'bg-orange-500/15 text-orange-300 border-orange-500/40' },
  CE: { label: 'Compilation Error', style: 'bg-violet-500/15 text-violet-300 border-violet-500/40' },
};

function verdictInfo(code) {
  return verdictMeta[code] || { label: code, style: 'bg-slate-500/15 text-slate-300 border-slate-500/40' };
}

function MySubmissionsPage() {
  const [submissions, setSubmissions] = useState([]);
  const [status, setStatus] = useState('loading'); // loading | ready | error

  useEffect(() => {
    async function loadSubmissions() {
      try {
        const { data } = await api.get('/me/submissions');
        setSubmissions(data.submissions);
        setStatus('ready');
      } catch {
        setStatus('error');
      }
    }
    loadSubmissions();
  }, []);

  return (
    <main className="min-h-screen bg-[#0d1117] text-slate-100">
      <CompilerNavbar language="cpp" onLanguageChange={() => {}} onRun={() => {}} onSave={() => {}} isBusy={false} />

      <section className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-6">
          <p className="text-sm font-semibold text-blue-400">Your Activity</p>
          <h1 className="mt-2 text-3xl font-bold text-white">My Submissions</h1>
          <p className="mt-2 text-slate-400">Every solution you've submitted for judging, newest first.</p>
        </div>

        <Panel title="All Submissions" icon={<History size={16} />}>
          {status === 'loading' && (
            <p className="p-6 text-sm text-slate-400">Loading submissions…</p>
          )}

          {status === 'error' && (
            <p className="p-6 text-sm text-rose-300">Could not load submissions. Is the backend running?</p>
          )}

          {status === 'ready' && submissions.length === 0 && (
            <p className="p-6 text-sm text-slate-400">
              No submissions yet. Open a <Link to="/problems" className="text-blue-400 hover:underline">problem</Link> and hit Submit.
            </p>
          )}

          {status === 'ready' && submissions.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-4 py-2.5 font-semibold">Problem</th>
                    <th className="px-4 py-2.5 font-semibold">Verdict</th>
                    <th className="px-4 py-2.5 font-semibold">Tests</th>
                    <th className="px-4 py-2.5 font-semibold">Lang</th>
                    <th className="px-4 py-2.5 font-semibold">Time</th>
                    <th className="px-4 py-2.5 font-semibold">When</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {submissions.map((sub) => (
                    <tr key={sub.id} className="hover:bg-slate-800/40">
                      <td className="px-4 py-2.5">
                        <Link to={`/problems/${sub.problem_slug}`} className="font-semibold text-slate-100 hover:text-blue-400">
                          {sub.problem_title}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5">
                        <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${verdictInfo(sub.verdict).style}`}>
                          {sub.verdict}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-slate-400">{sub.passed_count}/{sub.total_count}</td>
                      <td className="px-4 py-2.5 uppercase text-slate-400">{sub.language}</td>
                      <td className="px-4 py-2.5 text-slate-500">{sub.runtime_ms} ms</td>
                      <td className="px-4 py-2.5 text-slate-500">{new Date(sub.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </section>
    </main>
  );
}

export default MySubmissionsPage;
