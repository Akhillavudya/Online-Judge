import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import CompilerPage from './pages/CompilerPage';
import ProblemsPage from './pages/ProblemsPage';
import ProblemDetailPage from './pages/ProblemDetailPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/compiler" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/dashboard"
        element={(
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/compiler"
        element={(
          <ProtectedRoute>
            <CompilerPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/problems"
        element={(
          <ProtectedRoute>
            <ProblemsPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/problems/:slug"
        element={(
          <ProtectedRoute>
            <ProblemDetailPage />
          </ProtectedRoute>
        )}
      />
      <Route path="*" element={<Navigate to="/compiler" replace />} />
    </Routes>
  );
}

export default App;
