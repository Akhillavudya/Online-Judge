import { CircleUser, History } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import CompilerNavbar from '../components/CompilerNavbar';
import Panel from '../components/Panel';
import { api } from '../lib/api';

// Reused verdict colors (matches MySubmissionsPage).
const verdictMeta = {
  AC: { style: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' },
  WA: { style: 'bg-rose-500/15 text-rose-300 border-rose-500/40' },
  TLE: { style: 'bg-amber-500/15 text-amber-300 border-amber-500/40' },
  RE: { style: 'bg-orange-500/15 text-orange-300 border-orange-500/40' },
  CE: { style: 'bg-violet-500/15 text-violet-300 border-violet-500/40' },
};

function verdictStyle(code) {
  return verdictMeta[code]?.style || 'bg-slate-500/15 text-slate-300 border-slate-500/40';
}

// A single headline number with a label underneath.
function StatCard({ label, value, accent = 'text-white' }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-[#161b22] px-4 py-4">
      <p className={`text-2xl font-bold ${accent}`}>{value}</p>
      <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">{label}</p>
    </div>
  );
}

function ProfilePage() {
  const { userId } = useParams();
  const [profile, setProfile] = useState(null);
  const [status, setStatus] = useState('loading'); // loading | ready | error | notfound

  useEffect(() => {
    async function loadProfile() {
      setStatus('loading');
      try {
        const { data } = await api.get(`/users/${userId}/profile`);
        setProfile(data);
        setStatus('ready');
      } catch (error) {
        setStatus(error?.response?.status === 404 ? 'notfound' : 'error');
      }
    }
    loadProfile();
  }, [userId]);

  const acceptanceRate =
    profile && profile.total_submissions > 0
      ? Math.round((profile.accepted_submissions / profile.total_submissions) * 100)
      : 0;

  return (
    <main className="min-h-screen bg-[#0d1117] text-slate-100">
      <CompilerNavbar language="cpp" onLanguageChange={() => {}} onRun={() => {}} onSave={() => {}} isBusy={false} />

      <section className="mx-auto max-w-4xl px-4 py-8">
        {status === 'loading' && (
          <p className="p-6 text-sm text-slate-400">Loading profile…</p>
        )}

        {status === 'error' && (
          <p className="p-6 text-sm text-rose-300">Could not load this profile. Is the backend running?</p>
        )}

        {status === 'notfound' && (
          <p className="p-6 text-sm text-slate-400">
            No such user. Head back to the{' '}
            <Link to="/leaderboard" className="text-blue-400 hover:underline">leaderboard</Link>.
          </p>
        )}

        {status === 'ready' && profile && (
          <>
            {/* Header */}
            <div className="mb-6 flex items-center gap-4">
              <span className="grid h-14 w-14 place-items-center rounded-full bg-blue-600/20 text-blue-300">
                <CircleUser size={32} />
              </span>
              <div>
                <h1 className="text-2xl font-bold text-white">
                  {profile.name}
                  {profile.role === 'admin' && (
                    <span className="ml-2 rounded-full border border-amber-500/40 bg-amber-500/15 px-2 py-0.5 text-xs font-semibold text-amber-300">
                      Admin
                    </span>
                  )}
                </h1>
                <p className="mt-1 text-sm text-slate-400">
                  Joined {new Date(profile.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            {/* Headline stats */}
            <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard label="Solved" value={profile.total_solved} accent="text-emerald-300" />
              <StatCard label="Submissions" value={profile.total_submissions} />
              <StatCard label="Accepted" value={profile.accepted_submissions} />
              <StatCard label="Acceptance" value={`${acceptanceRate}%`} accent="text-blue-300" />
            </div>

            {/* Solved by difficulty */}
            <div className="mb-6 grid grid-cols-3 gap-3">
              <StatCard label="Easy" value={profile.solved_by_difficulty.easy} accent="text-emerald-300" />
              <StatCard label="Medium" value={profile.solved_by_difficulty.medium} accent="text-amber-300" />
              <StatCard label="Hard" value={profile.solved_by_difficulty.hard} accent="text-rose-300" />
            </div>

            {/* Recent activity */}
            <Panel title="Recent Submissions" icon={<History size={16} />}>
              {profile.recent_submissions.length === 0 && (
                <p className="p-6 text-sm text-slate-400">No submissions yet.</p>
              )}

              {profile.recent_submissions.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-500">
                        <th className="px-4 py-2.5 font-semibold">Problem</th>
                        <th className="px-4 py-2.5 font-semibold">Verdict</th>
                        <th className="px-4 py-2.5 font-semibold">Lang</th>
                        <th className="px-4 py-2.5 font-semibold">When</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {profile.recent_submissions.map((sub) => (
                        <tr key={sub.id} className="hover:bg-slate-800/40">
                          <td className="px-4 py-2.5">
                            <Link to={`/problems/${sub.problem_slug}`} className="font-semibold text-slate-100 hover:text-blue-400">
                              {sub.problem_title}
                            </Link>
                          </td>
                          <td className="px-4 py-2.5">
                            <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${verdictStyle(sub.verdict)}`}>
                              {sub.verdict}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 uppercase text-slate-400">{sub.language}</td>
                          <td className="px-4 py-2.5 text-slate-500">{new Date(sub.created_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
          </>
        )}
      </section>
    </main>
  );
}

export default ProfilePage;
