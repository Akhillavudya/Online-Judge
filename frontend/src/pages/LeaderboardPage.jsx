import { Trophy } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import CompilerNavbar from '../components/CompilerNavbar';
import Panel from '../components/Panel';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';

// A little flair for the podium positions; everyone else gets the plain number.
const rankBadge = {
  1: '🥇',
  2: '🥈',
  3: '🥉',
};

function LeaderboardPage() {
  const { user } = useAuth();
  const [entries, setEntries] = useState([]);
  const [status, setStatus] = useState('loading'); // loading | ready | error

  useEffect(() => {
    async function loadLeaderboard() {
      try {
        const { data } = await api.get('/leaderboard');
        setEntries(data.leaderboard);
        setStatus('ready');
      } catch {
        setStatus('error');
      }
    }
    loadLeaderboard();
  }, []);

  return (
    <main className="min-h-screen bg-[#0d1117] text-slate-100">
      <CompilerNavbar language="cpp" onLanguageChange={() => {}} onRun={() => {}} onSave={() => {}} isBusy={false} />

      <section className="mx-auto max-w-4xl px-4 py-8">
        <div className="mb-6">
          <p className="text-sm font-semibold text-blue-400">Community</p>
          <h1 className="mt-2 text-3xl font-bold text-white">Leaderboard</h1>
          <p className="mt-2 text-slate-400">Top solvers, ranked by number of problems solved.</p>
        </div>

        <Panel title="Top Solvers" icon={<Trophy size={16} />}>
          {status === 'loading' && (
            <p className="p-6 text-sm text-slate-400">Loading leaderboard…</p>
          )}

          {status === 'error' && (
            <p className="p-6 text-sm text-rose-300">Could not load the leaderboard. Is the backend running?</p>
          )}

          {status === 'ready' && entries.length === 0 && (
            <p className="p-6 text-sm text-slate-400">
              No one has solved a problem yet. Be the first — open a{' '}
              <Link to="/problems" className="text-blue-400 hover:underline">problem</Link> and submit an Accepted solution.
            </p>
          )}

          {status === 'ready' && entries.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-4 py-2.5 font-semibold">Rank</th>
                    <th className="px-4 py-2.5 font-semibold">User</th>
                    <th className="px-4 py-2.5 font-semibold text-right">Solved</th>
                    <th className="px-4 py-2.5 font-semibold text-right">Submissions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {entries.map((entry) => {
                    const isMe = user?.id === entry.user_id;
                    return (
                      <tr key={entry.user_id} className={isMe ? 'bg-blue-500/10' : 'hover:bg-slate-800/40'}>
                        <td className="px-4 py-2.5 font-semibold text-slate-300">
                          {rankBadge[entry.rank] || `#${entry.rank}`}
                        </td>
                        <td className="px-4 py-2.5">
                          <Link to={`/users/${entry.user_id}`} className="font-semibold text-slate-100 hover:text-blue-400">
                            {entry.name}
                          </Link>
                          {isMe && <span className="ml-2 text-xs font-semibold text-blue-400">You</span>}
                        </td>
                        <td className="px-4 py-2.5 text-right font-semibold text-emerald-300">{entry.solved_count}</td>
                        <td className="px-4 py-2.5 text-right text-slate-400">{entry.submission_count}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </section>
    </main>
  );
}

export default LeaderboardPage;
