import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import { useAuth } from '../context/AuthContext';

function RegisterPage() {
  const navigate = useNavigate();
  const { isAuthenticated, register } = useAuth();
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [message, setMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  if (isAuthenticated) return <Navigate to="/compiler" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setIsBusy(true);
    setMessage('');

    try {
      await register(form);
      navigate('/compiler');
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Registration failed.');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <AuthLayout title="Register" subtitle="Create your account to save programs and request AI reviews.">
      <form className="grid gap-4" onSubmit={handleSubmit}>
        <label className="grid gap-2 text-sm font-medium text-slate-300">
          Name
          <input
            className="h-11 rounded-md border border-slate-700 bg-[#0d1117] px-3 text-slate-100 outline-none focus:border-blue-500"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
          />
        </label>
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
          {isBusy ? 'Creating account...' : 'Create Account'}
        </button>
      </form>
      {message && <p className="mt-4 rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">{message}</p>}
      <p className="mt-6 text-sm text-slate-400">
        Already have an account? <Link className="font-semibold text-blue-400 hover:text-blue-300" to="/login">Login</Link>
      </p>
    </AuthLayout>
  );
}

export default RegisterPage;
