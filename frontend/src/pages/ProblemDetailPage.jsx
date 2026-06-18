import Editor from '@monaco-editor/react';
import { ArrowLeft, CheckCircle2, FlaskConical, History, ScrollText, Send, Terminal, TextCursorInput } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
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

const starterCode = {
  cpp: `#include <iostream>
using namespace std;

int main() {
    // Read input and print your answer
    return 0;
}`,
  python: `# Read input and print your answer
`,
  java: `public class Main {
    public static void main(String[] args) {
        // Read input and print your answer
    }
}`,
  javascript: `// Read input and print your answer
`,
};

const monacoLanguage = { cpp: 'cpp', python: 'python', java: 'java', javascript: 'javascript' };

const difficultyStyles = {
  easy: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  medium: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  hard: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
};

function ProblemDetailPage() {
  const { slug } = useParams();
  const [problem, setProblem] = useState(null);
  const [loadState, setLoadState] = useState('loading'); // loading | ready | error

  const [language, setLanguage] = useState('cpp');
  const [code, setCode] = useState(starterCode.cpp);
  const [stdin, setStdin] = useState('');
  const [output, setOutput] = useState('Run your code to see the output.');
  const [status, setStatus] = useState('Ready');
  const [isBusy, setIsBusy] = useState(false);

  const [result, setResult] = useState(null); // latest verdict {verdict, passed_count, ...}
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissions, setSubmissions] = useState([]);

  // Solved = the user has at least one Accepted verdict on this problem.
  const isSolved = submissions.some((sub) => sub.verdict === 'AC');

  async function loadSubmissions() {
    try {
      const { data } = await api.get(`/problems/${slug}/submissions`);
      setSubmissions(data.submissions);
    } catch {
      setSubmissions([]);
    }
  }

  useEffect(() => {
    async function loadProblem() {
      try {
        const { data } = await api.get(`/problems/${slug}`);
        setProblem(data.problem);
        // Prefill custom input with the first sample so "Run" works immediately.
        if (data.problem.sample_test_cases.length > 0) {
          setStdin(data.problem.sample_test_cases[0].input);
        }
        setLoadState('ready');
      } catch {
        setLoadState('error');
      }
    }
    loadProblem();
    loadSubmissions();
  }, [slug]);

  function handleLanguageChange(nextLanguage) {
    setLanguage(nextLanguage);
    setCode(starterCode[nextLanguage]);
    setOutput(nextLanguage === 'cpp' ? 'Run your code to see the output.' : 'Only C++ execution is supported by the backend right now.');
    setStatus('Ready');
  }

  async function handleRun() {
    setIsBusy(true);
    setStatus('Running');
    setOutput('');
    try {
      const { data } = await api.post('/run', { language, code, input: stdin });
      setOutput(data.output || '(no output)');
      setStatus('Success');
    } catch (error) {
      setOutput(error.response?.data?.detail || 'Execution failed.');
      setStatus('Failed');
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSave() {
    if (!problem) return;
    setIsBusy(true);
    setStatus('Saving');
    try {
      await api.post('/submissions', { title: `${problem.title} — solution`, language, code, output });
      setStatus('Saved');
    } catch (error) {
      setStatus(error.response?.data?.detail || 'Save failed');
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSubmit() {
    if (!problem) return;
    setIsSubmitting(true);
    setStatus('Judging');
    setResult(null);
    try {
      const { data } = await api.post(`/problems/${slug}/submit`, { language, code });
      setResult(data.result);
      setStatus(data.result.verdict === 'AC' ? 'Accepted' : data.result.verdict);
      loadSubmissions(); // refresh history with the new attempt
    } catch (error) {
      setStatus('Submit failed');
      setResult({
        verdict: 'ERR',
        passed_count: 0,
        total_count: 0,
        runtime_ms: 0,
        detail: error.response?.data?.detail || 'Could not judge the submission.',
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#0d1117] text-slate-100">
      <CompilerNavbar
        language={language}
        onLanguageChange={handleLanguageChange}
        onRun={handleRun}
        onSave={handleSave}
        isBusy={isBusy}
      />

      <section className="mx-auto max-w-7xl px-4 py-6">
        <Link to="/problems" className="mb-4 inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200">
          <ArrowLeft size={16} />
          Back to problems
        </Link>

        {loadState === 'loading' && <p className="text-sm text-slate-400">Loading problem…</p>}
        {loadState === 'error' && <p className="text-sm text-rose-300">Problem not found.</p>}

        {loadState === 'ready' && problem && (
          <div className="grid gap-5 lg:grid-cols-2">
            {/* Left: statement + samples */}
            <div className="space-y-5">
              <Panel title="Statement" icon={<ScrollText size={16} />}>
                <div className="p-5">
                  <div className="mb-3 flex items-center gap-3">
                    <h1 className="text-xl font-bold text-white">{problem.title}</h1>
                    <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold capitalize ${difficultyStyles[problem.difficulty] || difficultyStyles.easy}`}>
                      {problem.difficulty}
                    </span>
                    {isSolved && (
                      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/40 bg-emerald-500/15 px-2.5 py-0.5 text-xs font-semibold text-emerald-300">
                        <CheckCircle2 size={13} />
                        Solved
                      </span>
                    )}
                  </div>

                  {problem.tags.length > 0 && (
                    <div className="mb-3 flex flex-wrap gap-1.5">
                      {problem.tags.map((name) => (
                        <span key={name} className="rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] text-slate-400">
                          {name}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="mb-4 whitespace-pre-line text-sm leading-6 text-slate-300">{problem.statement}</p>

                  {problem.input_format && (
                    <Section label="Input">{problem.input_format}</Section>
                  )}
                  {problem.output_format && (
                    <Section label="Output">{problem.output_format}</Section>
                  )}
                  {problem.constraints && (
                    <Section label="Constraints">{problem.constraints}</Section>
                  )}

                  <p className="mt-4 text-xs text-slate-500">
                    Time limit: {problem.time_limit_ms} ms · Memory limit: {problem.memory_limit_mb} MB
                  </p>
                </div>
              </Panel>

              <Panel title="Sample Test Cases" icon={<FlaskConical size={16} />}>
                <div className="space-y-4 p-5">
                  {problem.sample_test_cases.length === 0 && (
                    <p className="text-sm text-slate-400">No sample test cases provided.</p>
                  )}
                  {problem.sample_test_cases.map((testCase, index) => (
                    <div key={testCase.id} className="rounded-md border border-slate-800">
                      <p className="border-b border-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-400">
                        Example {index + 1}
                      </p>
                      <div className="grid gap-3 p-3 sm:grid-cols-2">
                        <div>
                          <p className="mb-1 text-xs text-slate-500">Input</p>
                          <pre className="overflow-auto rounded bg-[#0d1117] p-2 font-mono text-xs text-slate-200">{testCase.input || '(empty)'}</pre>
                        </div>
                        <div>
                          <p className="mb-1 text-xs text-slate-500">Expected Output</p>
                          <pre className="overflow-auto rounded bg-[#0d1117] p-2 font-mono text-xs text-emerald-200">{testCase.expected_output}</pre>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel title="My Submissions" icon={<History size={16} />}>
                <div className="p-3">
                  {submissions.length === 0 ? (
                    <p className="px-2 py-3 text-sm text-slate-400">No submissions yet. Write a solution and hit Submit.</p>
                  ) : (
                    <ul className="divide-y divide-slate-800">
                      {submissions.map((sub) => (
                        <li key={sub.id} className="flex items-center justify-between gap-3 px-2 py-2 text-sm">
                          <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${verdictInfo(sub.verdict).style}`}>
                            {sub.verdict}
                          </span>
                          <span className="text-slate-400">{sub.passed_count}/{sub.total_count} passed</span>
                          <span className="text-slate-500">{sub.runtime_ms} ms</span>
                          <span className="ml-auto text-xs text-slate-600">{new Date(sub.created_at).toLocaleTimeString()}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </Panel>
            </div>

            {/* Right: editor + run */}
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-3 rounded-lg border border-slate-800 bg-[#161b22] px-4 py-2.5">
                <p className="text-sm font-semibold text-slate-200">Your Solution</p>
                <div className="flex items-center gap-3">
                  <p className={`text-sm font-semibold ${status === 'Failed' || status === 'Submit failed' ? 'text-rose-300' : 'text-emerald-300'}`}>{status}</p>
                  <button
                    className="inline-flex h-9 items-center gap-2 rounded-md bg-violet-600 px-4 text-sm font-semibold text-white hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-60"
                    onClick={handleSubmit}
                    disabled={isSubmitting || isBusy}
                  >
                    <Send size={15} />
                    {isSubmitting ? 'Judging…' : 'Submit'}
                  </button>
                </div>
              </div>

              <section className="overflow-hidden rounded-lg border border-slate-800 bg-[#1e1e1e]">
                <div className="h-[46vh] min-h-[360px]">
                  <Editor
                    height="100%"
                    language={monacoLanguage[language]}
                    theme="vs-dark"
                    value={code}
                    onChange={(value) => setCode(value || '')}
                    options={{
                      automaticLayout: true,
                      fontSize: 15,
                      minimap: { enabled: false },
                      scrollBeyondLastLine: false,
                      padding: { top: 16, bottom: 16 },
                    }}
                  />
                </div>
              </section>

              {result && (
                <div className={`rounded-lg border p-4 ${verdictInfo(result.verdict).style}`}>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                    <span className="text-base font-bold">{verdictInfo(result.verdict).label}</span>
                    <span className="text-sm opacity-90">{result.passed_count}/{result.total_count} test cases passed</span>
                    {result.runtime_ms > 0 && <span className="text-sm opacity-75">{result.runtime_ms} ms</span>}
                  </div>
                  {result.detail && (
                    <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words font-mono text-xs opacity-90">{result.detail}</pre>
                  )}
                </div>
              )}

              <div className="grid gap-4 sm:grid-cols-2">
                <Panel title="Input" icon={<TextCursorInput size={16} />}>
                  <textarea
                    className="h-40 w-full resize-none bg-[#0d1117] p-3 font-mono text-sm text-slate-100 outline-none placeholder:text-slate-600"
                    placeholder="Custom input"
                    value={stdin}
                    onChange={(event) => setStdin(event.target.value)}
                  />
                </Panel>
                <Panel title="Output" icon={<Terminal size={16} />}>
                  <pre className="h-40 overflow-auto bg-[#050812] p-3 font-mono text-sm leading-6 text-emerald-200">{output}</pre>
                </Panel>
              </div>

              <p className="rounded-md border border-slate-800 bg-[#161b22] px-4 py-2 text-xs text-slate-400">
                Tip: <span className="text-slate-200">Run</span> tests against your own input only.
                <span className="text-violet-300"> Submit</span> judges your code against all hidden test cases and gives a verdict.
              </p>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

function Section({ label, children }) {
  return (
    <div className="mb-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 whitespace-pre-line text-sm leading-6 text-slate-300">{children}</p>
    </div>
  );
}

export default ProblemDetailPage;
