import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function ProtectedRoute({ children, adminOnly = false }) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#0d1117] text-slate-200">
        Loading workspace...
      </main>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  // Admin-only routes: a logged-in non-admin is sent back to the problem list.
  // (The backend still enforces this independently — the UI guard is just UX.)
  if (adminOnly && user?.role !== 'admin') return <Navigate to="/problems" replace />;

  return children;
}

export default ProtectedRoute;
