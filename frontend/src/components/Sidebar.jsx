import { Clock3, FileCode2, History } from 'lucide-react';
import Panel from './Panel';

function Sidebar({ submissions, history, activeSubmissionId, onOpenSubmission }) {
  return (
    <aside className="hidden w-72 shrink-0 border-r border-slate-800 bg-[#0d1117] p-4 xl:block">
      <Panel title="Saved Codes" icon={<FileCode2 size={16} />} className="mb-4">
        <div className="max-h-72 overflow-auto p-2">
          {submissions.length === 0 && <p className="px-2 py-3 text-sm text-slate-500">No saved codes yet.</p>}
          {submissions.map((submission) => (
            <button
              className={`mb-2 w-full rounded-md border px-3 py-2 text-left text-sm ${
                activeSubmissionId === submission.id
                  ? 'border-blue-500 bg-blue-500/10 text-blue-200'
                  : 'border-slate-800 bg-[#0d1117] text-slate-300 hover:border-slate-700'
              }`}
              key={submission.id}
              onClick={() => onOpenSubmission(submission)}
            >
              <span className="block truncate font-semibold">{submission.title}</span>
              <span className="text-xs text-slate-500">{submission.language.toUpperCase()}</span>
            </button>
          ))}
        </div>
      </Panel>

      <Panel title="Execution History" icon={<History size={16} />}>
        <div className="max-h-72 overflow-auto p-2">
          {history.length === 0 && <p className="px-2 py-3 text-sm text-slate-500">Runs appear here.</p>}
          {history.map((item) => (
            <div className="mb-2 rounded-md border border-slate-800 bg-[#0d1117] px-3 py-2 text-sm" key={item.id}>
              <p className="flex items-center gap-2 font-semibold text-slate-300">
                <Clock3 size={14} />
                {item.status}
              </p>
              <p className="mt-1 text-xs text-slate-500">{item.language.toUpperCase()} · {item.time}</p>
            </div>
          ))}
        </div>
      </Panel>
    </aside>
  );
}

export default Sidebar;
