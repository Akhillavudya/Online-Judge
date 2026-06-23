import Editor from '@monaco-editor/react';
import { Bot, Cpu, FileText, Lightbulb, Terminal, TextCursorInput } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import CompilerNavbar from '../components/CompilerNavbar';
import Panel from '../components/Panel';
import Sidebar from '../components/Sidebar';
import { api } from '../lib/api';

const starterCode = {
  cpp: `#include <iostream>
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << "Sum: " << a + b << endl;
    return 0;
}`,
  java: `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, Java");
    }
}`,
  python: `a, b = map(int, input().split())
print("Sum:", a + b)`,
  javascript: `const input = "5 7".trim().split(/\\s+/).map(Number);
console.log("Sum:", input[0] + input[1]);`,
};

const monacoLanguage = {
  cpp: 'cpp',
  java: 'java',
  python: 'python',
  javascript: 'javascript',
};

const fileExtension = {
  cpp: 'cpp',
  java: 'java',
  python: 'py',
  javascript: 'js',
};

// Languages the backend can actually run today (Phase 5: C++ + Python).
const runnableLanguages = new Set(['cpp', 'python']);

function fallbackReview(language) {
  return {
    quality: `The ${language.toUpperCase()} code is readable. Keep variable names clear and validate input before using it.`,
    time: 'Time Complexity: O(1) for the starter sum example.',
    space: 'Space Complexity: O(1), because it only stores a few scalar values.',
    tips: 'Optimization tips: handle missing input, avoid unnecessary globals, and split larger logic into small functions.',
  };
}

function CompilerPage() {
  const [language, setLanguage] = useState('cpp');
  const [fileName, setFileName] = useState('main.cpp');
  const [code, setCode] = useState(starterCode.cpp);
  const [stdin, setStdin] = useState('5 7');
  const [output, setOutput] = useState('Run your code to see output.');
  const [status, setStatus] = useState('Ready');
  const [submissions, setSubmissions] = useState([]);
  const [activeSubmissionId, setActiveSubmissionId] = useState(null);
  const [history, setHistory] = useState([]);
  const [review, setReview] = useState(fallbackReview('cpp'));
  const [isBusy, setIsBusy] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);

  const currentFileName = useMemo(() => {
    if (fileName.includes('.')) return fileName;
    return `${fileName}.${fileExtension[language]}`;
  }, [fileName, language]);

  useEffect(() => {
    loadSubmissions();
  }, []);

  function handleLanguageChange(nextLanguage) {
    setLanguage(nextLanguage);
    setCode(starterCode[nextLanguage]);
    setFileName(`main.${fileExtension[nextLanguage]}`);
    setActiveSubmissionId(null);
    setOutput(runnableLanguages.has(nextLanguage)
      ? 'Run your code to see output.'
      : 'Only C++ and Python can be run right now.');
    setStatus('Ready');
    setReview(fallbackReview(nextLanguage));
  }

  async function loadSubmissions() {
    try {
      const { data } = await api.get('/submissions');
      setSubmissions(data.submissions);
    } catch {
      setSubmissions([]);
    }
  }

  async function handleRun() {
    setIsBusy(true);
    setStatus('Running');
    setOutput('');

    try {
      const { data } = await api.post('/run', { language, code, input: stdin });
      setOutput(data.output || '(no output)');
      setStatus('Success');
      setHistory((items) => [
        { id: crypto.randomUUID(), language, status: 'Success', time: new Date().toLocaleTimeString() },
        ...items,
      ].slice(0, 8));
    } catch (error) {
      const detail = error.response?.data?.detail || 'Execution failed.';
      setOutput(detail);
      setStatus('Failed');
      setHistory((items) => [
        { id: crypto.randomUUID(), language, status: 'Failed', time: new Date().toLocaleTimeString() },
        ...items,
      ].slice(0, 8));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSave() {
    setIsBusy(true);
    setStatus('Saving');

    const payload = {
      title: currentFileName,
      language,
      code,
      output,
    };

    try {
      if (activeSubmissionId) {
        await api.put(`/submissions/${activeSubmissionId}`, payload);
      } else {
        const { data } = await api.post('/submissions', payload);
        setActiveSubmissionId(data.submission.id);
      }
      await loadSubmissions();
      setStatus('Saved');
    } catch (error) {
      setStatus(error.response?.data?.detail || 'Save failed');
    } finally {
      setIsBusy(false);
    }
  }

  async function handleReview() {
    setIsReviewing(true);

    try {
      const { data } = await api.post('/ai/review', { language, code, input: stdin, output });
      setReview({
        quality: data.review,
        time: 'Time Complexity: See Gemini review above. Add explicit complexity notes in your solution comments for best judging.',
        space: 'Space Complexity: See Gemini review above. Watch auxiliary containers and recursion depth.',
        tips: 'Optimization tips: compare against constraints, reduce repeated work, and prefer standard library algorithms when they simplify intent.',
      });
    } catch (error) {
      setReview({
        ...fallbackReview(language),
        quality: error.response?.data?.detail || 'AI review failed. Check GEMINI_API_KEY in the backend .env file.',
      });
    } finally {
      setIsReviewing(false);
    }
  }

  function openSubmission(submission) {
    setActiveSubmissionId(submission.id);
    setFileName(submission.title);
    setLanguage(submission.language);
    setCode(submission.code);
    setOutput(submission.output || 'Saved file loaded.');
    setStatus('Loaded');
    setReview(fallbackReview(submission.language));
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

      <div className="flex min-h-[calc(100vh-4rem)]">
        <Sidebar
          submissions={submissions}
          history={history}
          activeSubmissionId={activeSubmissionId}
          onOpenSubmission={openSubmission}
        />

        <section className="min-w-0 flex-1 p-3 lg:p-5">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 bg-[#161b22] px-4 py-3">
            <div className="flex min-w-0 items-center gap-2">
              <FileText className="shrink-0 text-blue-400" size={18} />
              <input
                className="min-w-0 bg-transparent text-sm font-semibold text-slate-100 outline-none"
                value={fileName}
                onChange={(event) => setFileName(event.target.value)}
              />
            </div>
            <p className={`text-sm font-semibold ${status === 'Failed' ? 'text-rose-300' : 'text-emerald-300'}`}>{status}</p>
          </div>

          <section className="overflow-hidden rounded-lg border border-slate-800 bg-[#1e1e1e]">
            <div className="h-[58vh] min-h-[420px]">
              <Editor
                height="100%"
                language={monacoLanguage[language]}
                path={currentFileName}
                theme="vs-dark"
                value={code}
                onChange={(value) => setCode(value || '')}
                options={{
                  automaticLayout: true,
                  fontSize: 15,
                  fontFamily: 'Cascadia Code, Fira Code, Consolas, monospace',
                  minimap: { enabled: true },
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  padding: { top: 16, bottom: 16 },
                }}
              />
            </div>
          </section>

          <section className="mt-4 grid gap-4 lg:grid-cols-3">
            <Panel title="Input" icon={<TextCursorInput size={16} />}>
              <textarea
                className="h-52 w-full resize-none bg-[#0d1117] p-4 font-mono text-sm text-slate-100 outline-none placeholder:text-slate-600"
                placeholder="Custom input"
                value={stdin}
                onChange={(event) => setStdin(event.target.value)}
              />
            </Panel>

            <Panel title="Output" icon={<Terminal size={16} />}>
              <pre className="h-52 overflow-auto bg-[#050812] p-4 font-mono text-sm leading-6 text-emerald-200">
                {output}
              </pre>
            </Panel>

            <Panel
              title="AI Review"
              icon={<Bot size={16} />}
              actions={(
                <button
                  className="rounded-md border border-violet-500/50 px-3 py-1 text-xs font-semibold text-violet-200 hover:bg-violet-500/10 disabled:opacity-60"
                  onClick={handleReview}
                  disabled={isReviewing}
                >
                  {isReviewing ? 'Reviewing' : 'Ask AI'}
                </button>
              )}
            >
              <div className="h-52 overflow-auto bg-[#0d1117] p-4 text-sm leading-6 text-slate-300">
                <p className="mb-3 flex gap-2"><Lightbulb className="mt-1 shrink-0 text-amber-300" size={15} />{review.quality}</p>
                <p className="mb-3 flex gap-2"><Cpu className="mt-1 shrink-0 text-blue-300" size={15} />{review.time}</p>
                <p className="mb-3 flex gap-2"><Cpu className="mt-1 shrink-0 text-emerald-300" size={15} />{review.space}</p>
                <p className="flex gap-2"><Lightbulb className="mt-1 shrink-0 text-violet-300" size={15} />{review.tips}</p>
              </div>
            </Panel>
          </section>
        </section>
      </div>
    </main>
  );
}

export default CompilerPage;
