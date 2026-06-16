import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import { useAuth } from '../context/AuthContext';

function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, login } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [message, setMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  if (isAuthenticated) return <Navigate to="/compiler" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setIsBusy(true);
    setMessage('');

    try {
      await login(form);
      navigate('/compiler');
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Login failed.');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <AuthLayout title="Login" subtitle="Access your compiler workspace and saved codes.">
      <form className="grid gap-4" onSubmit={handleSubmit}>
        <label className="grid gap-2 text-sm font-medium text-slate-300">
          Email
          <input
            className="h-11 rounded-md border border-slate-700 bg-[#0d1117] px-3 text-slate-100 outline-none focus:border-blue-500"
            type="email"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
          />
        </label>
        <label className="grid gap-2 text-sm font-medium text-slate-300">
          Password
          <input
            className="h-11 rounded-md border border-slate-700 bg-[#0d1117] px-3 text-slate-100 outline-none focus:border-blue-500"
            type="password"
            value={form.password}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
          />
        </label>
        <button className="mt-2 h-11 rounded-md bg-blue-600 font-semibold text-white hover:bg-blue-500 disabled:opacity-60" disabled={isBusy}>
          {isBusy ? 'Logging in...' : 'Login'}
        </button>
      </form>
      {message && <p className="mt-4 rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">{message}</p>}
      <p className="mt-6 text-sm text-slate-400">
        New to AlgoU? <Link className="font-semibold text-blue-400 hover:text-blue-300" to="/register">Create an account</Link>
      </p>
    </AuthLayout>
  );
}

export default LoginPage;
