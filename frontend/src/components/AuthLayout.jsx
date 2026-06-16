import { Code2 } from 'lucide-react';
import { Link } from 'react-router-dom';

function AuthLayout({ children, title, subtitle }) {
  return (
    <main className="min-h-screen bg-[#0d1117] text-slate-100">
      <div className="mx-auto grid min-h-screen max-w-6xl items-center gap-10 px-5 py-10 lg:grid-cols-[1fr_420px]">
        <section className="hidden lg:block">
          <Link to="/compiler" className="mb-10 inline-flex items-center gap-3 text-2xl font-bold">
            <span className="grid h-11 w-11 place-items-center rounded-lg bg-blue-600 text-white">
              <Code2 size={25} />
            </span>
            AlgoU
          </Link>
          <h1 className="max-w-xl text-5xl font-bold leading-tight text-white">
            Practice, run, save, and review code in one focused workspace.
          </h1>
          <p className="mt-5 max-w-lg text-lg leading-8 text-slate-400">
            A dark coding platform layout with compiler execution, saved submissions,
            and AI review for quality and complexity feedback.
          </p>
        </section>

        <section className="rounded-lg border border-slate-800 bg-[#161b22] p-6 shadow-2xl shadow-black/30">
          <div className="mb-8 lg:hidden">
            <Link to="/compiler" className="inline-flex items-center gap-3 text-2xl font-bold">
              <span className="grid h-10 w-10 place-items-center rounded-lg bg-blue-600 text-white">
                <Code2 size={23} />
              </span>
              AlgoU
            </Link>
          </div>
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white">{title}</h2>
            <p className="mt-2 text-sm text-slate-400">{subtitle}</p>
          </div>
          {children}
        </section>
      </div>
    </main>
  );
}

export default AuthLayout;
