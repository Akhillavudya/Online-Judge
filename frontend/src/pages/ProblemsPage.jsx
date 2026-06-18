import { CheckCircle2, ListChecks, Search } from 'lucide-react';
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
  const [total, setTotal] = useState(0);
  const [solved, setSolved] = useState(new Set()); // slugs the user has solved
  const [availableTags, setAvailableTags] = useState([]);
  const [status, setStatus] = useState('loading'); // loading | ready | error

  // Filters + pagination.
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [tag, setTag] = useState('');
  const [page, setPage] = useState(1);
  const limit = 20;

  const totalPages = Math.max(1, Math.ceil(total / limit));

  // Wait until the user stops typing before searching; reset to the first page.
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Solved slugs and the tag list are user/global — fetch them once.
  useEffect(() => {
    api.get('/me/solved').then((r) => setSolved(new Set(r.data.solved))).catch(() => {});
    api.get('/problems/tags').then((r) => setAvailableTags(r.data.tags)).catch(() => {});
  }, []);

  // Re-fetch the list whenever a filter or the page changes.
  useEffect(() => {
    let active = true;
    async function loadProblems() {
      setStatus('loading');
      try {
        const params = { page, limit };
        if (debouncedSearch) params.search = debouncedSearch;
        if (difficulty) params.difficulty = difficulty;
        if (tag) params.tag = tag;
        const { data } = await api.get('/problems', { params });
        if (!active) return;
        setProblems(data.problems);
        setTotal(data.total);
        setStatus('ready');
      } catch {
        if (active) setStatus('error');
      }
    }
    loadProblems();
    return () => {
      active = false;
    };
  }, [debouncedSearch, difficulty, tag, page]);

  function handleDifficultyChange(value) {
    setDifficulty(value);
    setPage(1);
  }

  function handleTagChange(value) {
    setTag(value);
    setPage(1);
  }

  return (
    <main className="min-h-screen bg-[#0d1117] text-slate-100">
      <CompilerNavbar language="cpp" onLanguageChange={() => {}} onRun={() => {}} onSave={() => {}} isBusy={false} />

      <section className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-6">
          <p className="text-sm font-semibold text-blue-400">Problem Set</p>
          <h1 className="mt-2 text-3xl font-bold text-white">Problems</h1>
          <p className="mt-2 text-slate-400">Search, filter by difficulty or tag, and start solving.</p>
        </div>

        {/* Filter bar */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="relative min-w-[220px] flex-1">
            <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search problems by title…"
              className="h-10 w-full rounded-md border border-slate-700 bg-[#161b22] pl-9 pr-3 text-sm text-slate-100 outline-none placeholder:text-slate-600 focus:border-blue-500"
            />
          </div>
          <select
            value={difficulty}
            onChange={(event) => handleDifficultyChange(event.target.value)}
            className="h-10 rounded-md border border-slate-700 bg-[#161b22] px-3 text-sm text-slate-100 outline-none focus:border-blue-500"
          >
            <option value="">All difficulties</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
          <select
            value={tag}
            onChange={(event) => handleTagChange(event.target.value)}
            className="h-10 rounded-md border border-slate-700 bg-[#161b22] px-3 text-sm text-slate-100 outline-none focus:border-blue-500"
          >
            <option value="">All tags</option>
            {availableTags.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
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
              No problems match your filters.
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
                      <span className="w-6 shrink-0 text-right text-sm text-slate-500">
                        {(page - 1) * limit + index + 1}
                      </span>
                      {solved.has(problem.slug) ? (
                        <CheckCircle2 size={16} className="shrink-0 text-emerald-400" aria-label="Solved" />
                      ) : (
                        <span className="w-4 shrink-0" />
                      )}
                      <span className="truncate text-sm font-semibold text-slate-100">{problem.title}</span>
                      <span className="hidden gap-1.5 sm:flex">
                        {problem.tags.map((name) => (
                          <span key={name} className="rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] text-slate-400">
                            {name}
                          </span>
                        ))}
                      </span>
                    </span>
                    <DifficultyBadge difficulty={problem.difficulty} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        {/* Pagination */}
        {status === 'ready' && total > 0 && (
          <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
            <span>
              Showing {(page - 1) * limit + 1}–{Math.min(page * limit, total)} of {total}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="rounded-md border border-slate-700 bg-[#161b22] px-3 py-1.5 font-semibold text-slate-200 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Prev
              </button>
              <span className="text-slate-500">Page {page} / {totalPages}</span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="rounded-md border border-slate-700 bg-[#161b22] px-3 py-1.5 font-semibold text-slate-200 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

export default ProblemsPage;
