import { Plus, ShieldCheck, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import CompilerNavbar from '../components/CompilerNavbar';
import Panel from '../components/Panel';
import { api } from '../lib/api';

// A fresh, empty test-case row for the dynamic list below.
const emptyCase = () => ({ input: '', expected_output: '', is_sample: false });

const inputClass =
  'w-full rounded-md border border-slate-700 bg-[#0d1117] px-3 py-2 text-sm text-slate-100 outline-none focus:border-blue-500';

function AdminPage() {
  const [form, setForm] = useState({
    title: '',
    statement: '',
    input_format: '',
    output_format: '',
    constraints: '',
    difficulty: 'easy',
    time_limit_ms: 2000,
    memory_limit_mb: 256,
    tags: '',
  });
  const [testCases, setTestCases] = useState([{ ...emptyCase(), is_sample: true }]);
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState(null); // { type: 'ok'|'err', text, slug? }

  function setField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function setCase(index, key, value) {
    setTestCases((prev) => prev.map((c, i) => (i === index ? { ...c, [key]: value } : c)));
  }

  function addCase() {
    setTestCases((prev) => [...prev, emptyCase()]);
  }

  function removeCase(index) {
    setTestCases((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsBusy(true);
    setMessage(null);

    // Turn the comma-separated tags string into a clean list.
    const tags = form.tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    const payload = {
      ...form,
      time_limit_ms: Number(form.time_limit_ms),
      memory_limit_mb: Number(form.memory_limit_mb),
      tags,
      test_cases: testCases,
    };

    try {
      const { data } = await api.post('/admin/problems', payload);
      const slug = data.problem.slug;
      setMessage({ type: 'ok', text: `Created "${data.problem.title}".`, slug });
      // Reset for the next problem.
      setForm({
        title: '', statement: '', input_format: '', output_format: '',
        constraints: '', difficulty: 'easy', time_limit_ms: 2000, memory_limit_mb: 256, tags: '',
      });
      setTestCases([{ ...emptyCase(), is_sample: true }]);
    } catch (error) {
      setMessage({ type: 'err', text: error.response?.data?.detail || 'Could not create the problem.' });
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#0d1117] text-slate-100">
      <CompilerNavbar language="cpp" onLanguageChange={() => {}} onRun={() => {}} onSave={() => {}} isBusy={false} />

      <section className="mx-auto max-w-4xl px-4 py-6">
        <div className="mb-6 flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-md bg-amber-500/15 text-amber-300">
            <ShieldCheck size={22} />
          </span>
          <div>
            <h1 className="text-xl font-bold text-white">Admin — Create Problem</h1>
            <p className="text-sm text-slate-400">Add a new problem and its test cases. Hidden cases are used for judging.</p>
          </div>
        </div>

        {message && (
          <div
            className={`mb-5 rounded-md border px-4 py-3 text-sm ${
              message.type === 'ok'
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
                : 'border-rose-500/30 bg-rose-500/10 text-rose-200'
            }`}
          >
            {message.text}{' '}
            {message.slug && (
              <Link className="font-semibold underline" to={`/problems/${message.slug}`}>
                View problem →
              </Link>
            )}
          </div>
        )}

        <form className="grid gap-5" onSubmit={handleSubmit}>
          <Panel title="Details">
            <div className="grid gap-4 p-4">
              <label className="grid gap-2 text-sm font-medium text-slate-300">
                Title
                <input className={inputClass} value={form.title} required minLength={2}
                  onChange={(e) => setField('title', e.target.value)} />
              </label>
              <label className="grid gap-2 text-sm font-medium text-slate-300">
                Statement
                <textarea className={`${inputClass} min-h-28`} value={form.statement} required
                  onChange={(e) => setField('statement', e.target.value)} />
              </label>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="grid gap-2 text-sm font-medium text-slate-300">
                  Input format
                  <textarea className={`${inputClass} min-h-20`} value={form.input_format}
                    onChange={(e) => setField('input_format', e.target.value)} />
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-300">
                  Output format
                  <textarea className={`${inputClass} min-h-20`} value={form.output_format}
                    onChange={(e) => setField('output_format', e.target.value)} />
                </label>
              </div>
              <label className="grid gap-2 text-sm font-medium text-slate-300">
                Constraints
                <textarea className={`${inputClass} min-h-16`} value={form.constraints}
                  onChange={(e) => setField('constraints', e.target.value)} />
              </label>
              <div className="grid gap-4 sm:grid-cols-4">
                <label className="grid gap-2 text-sm font-medium text-slate-300">
                  Difficulty
                  <select className={inputClass} value={form.difficulty}
                    onChange={(e) => setField('difficulty', e.target.value)}>
                    <option value="easy">easy</option>
                    <option value="medium">medium</option>
                    <option value="hard">hard</option>
                  </select>
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-300">
                  Time limit (ms)
                  <input className={inputClass} type="number" min={100} max={15000} value={form.time_limit_ms}
                    onChange={(e) => setField('time_limit_ms', e.target.value)} />
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-300">
                  Memory (MB)
                  <input className={inputClass} type="number" min={16} max={1024} value={form.memory_limit_mb}
                    onChange={(e) => setField('memory_limit_mb', e.target.value)} />
                </label>
                <label className="grid gap-2 text-sm font-medium text-slate-300">
                  Tags (comma-separated)
                  <input className={inputClass} value={form.tags} placeholder="math, dp"
                    onChange={(e) => setField('tags', e.target.value)} />
                </label>
              </div>
            </div>
          </Panel>

          <Panel title="Test cases">
            <div className="grid gap-4 p-4">
              {testCases.map((c, index) => (
                <div key={index} className="rounded-md border border-slate-700 bg-[#0d1117] p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Case {index + 1}
                    </span>
                    <div className="flex items-center gap-3">
                      <label className="flex items-center gap-2 text-xs text-slate-300">
                        <input type="checkbox" checked={c.is_sample}
                          onChange={(e) => setCase(index, 'is_sample', e.target.checked)} />
                        Sample (shown to users)
                      </label>
                      {testCases.length > 1 && (
                        <button type="button" className="text-rose-300 hover:text-rose-200"
                          onClick={() => removeCase(index)} title="Remove case">
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <label className="grid gap-1 text-xs font-medium text-slate-400">
                      Input
                      <textarea className={`${inputClass} min-h-20 font-mono`} value={c.input}
                        onChange={(e) => setCase(index, 'input', e.target.value)} />
                    </label>
                    <label className="grid gap-1 text-xs font-medium text-slate-400">
                      Expected output
                      <textarea className={`${inputClass} min-h-20 font-mono`} value={c.expected_output} required
                        onChange={(e) => setCase(index, 'expected_output', e.target.value)} />
                    </label>
                  </div>
                </div>
              ))}
              <button type="button"
                className="inline-flex w-fit items-center gap-2 rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
                onClick={addCase}>
                <Plus size={16} />
                Add test case
              </button>
            </div>
          </Panel>

          <button
            className="h-11 rounded-md bg-blue-600 font-semibold text-white hover:bg-blue-500 disabled:opacity-60"
            disabled={isBusy}
          >
            {isBusy ? 'Creating…' : 'Create problem'}
          </button>
        </form>
      </section>
    </main>
  );
}

export default AdminPage;
