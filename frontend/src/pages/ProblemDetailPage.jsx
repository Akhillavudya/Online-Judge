import Editor from '@monaco-editor/react';
import { ArrowLeft, FlaskConical, ScrollText, Terminal, TextCursorInput } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import CompilerNavbar from '../components/CompilerNavbar';
import Panel from '../components/Panel';
import { api } from '../lib/api';

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
                  </div>
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
            </div>

            {/* Right: editor + run */}
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-[#161b22] px-4 py-2.5">
                <p className="text-sm font-semibold text-slate-200">Your Solution</p>
                <p className={`text-sm font-semibold ${status === 'Failed' ? 'text-rose-300' : 'text-emerald-300'}`}>{status}</p>
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
                Tip: use <span className="text-slate-200">Run</span> to test against your own input. Automatic judging
                against all hidden test cases (verdicts like Accepted / Wrong Answer) arrives in Phase 2.
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
