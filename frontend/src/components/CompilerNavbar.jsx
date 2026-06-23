import { ChevronDown, Code2, LogOut, Play, Save, UserCircle } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function CompilerNavbar({ language, onLanguageChange, onRun, onSave, isBusy }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <header className="sticky top-0 z-30 border-b border-slate-800 bg-[#0d1117]/95 backdrop-blur">
      <div className="flex min-h-16 flex-wrap items-center gap-3 px-4 lg:px-6">
        <div className="mr-auto flex items-center gap-5">
          <Link to="/dashboard" className="inline-flex items-center gap-3 text-xl font-bold text-white">
            <span className="grid h-9 w-9 place-items-center rounded-md bg-blue-600">
              <Code2 size={22} />
            </span>
            AlgoU
          </Link>
          <nav className="hidden items-center gap-4 text-sm font-semibold text-slate-400 sm:flex">
            <Link to="/problems" className="hover:text-slate-100">Problems</Link>
            <Link to="/submissions" className="hover:text-slate-100">My Submissions</Link>
            <Link to="/compiler" className="hover:text-slate-100">Compiler</Link>
            {user?.role === 'admin' && (
              <Link to="/admin" className="text-amber-300 hover:text-amber-200">Admin</Link>
            )}
          </nav>
        </div>

        <select
          className="h-10 rounded-md border border-slate-700 bg-[#161b22] px-3 text-sm text-slate-100 outline-none focus:border-blue-500"
          value={language}
          onChange={(event) => onLanguageChange(event.target.value)}
        >
          <option value="cpp">C++</option>
          <option value="java">Java</option>
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
        </select>

        <button
          className="inline-flex h-10 items-center gap-2 rounded-md bg-emerald-600 px-4 text-sm font-semibold text-white hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-60"
          onClick={onRun}
          disabled={isBusy}
        >
          <Play size={16} />
          Run
        </button>
        <button
          className="inline-flex h-10 items-center gap-2 rounded-md bg-blue-600 px-4 text-sm font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          onClick={onSave}
          disabled={isBusy}
        >
          <Save size={16} />
          Save
        </button>

        <details className="relative">
          <summary className="flex h-10 list-none items-center gap-2 rounded-md border border-slate-700 bg-[#161b22] px-3 text-sm text-slate-200">
            <UserCircle size={18} />
            <span className="max-w-[120px] truncate">{user?.name || 'Profile'}</span>
            <ChevronDown size={15} />
          </summary>
          <div className="absolute right-0 mt-2 w-56 rounded-md border border-slate-700 bg-[#161b22] p-2 shadow-xl">
            <div className="border-b border-slate-800 px-3 py-2 text-sm">
              <p className="font-semibold text-white">{user?.name}</p>
              <p className="truncate text-slate-400">{user?.email}</p>
            </div>
            <Link className="block rounded px-3 py-2 text-sm text-slate-300 hover:bg-slate-800" to="/dashboard">
              Dashboard
            </Link>
            <button className="flex w-full items-center gap-2 rounded px-3 py-2 text-sm text-rose-300 hover:bg-slate-800" onClick={handleLogout}>
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </details>
      </div>
    </header>
  );
}

export default CompilerNavbar;
