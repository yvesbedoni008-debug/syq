import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { DashboardPage } from '@/pages/Dashboard';
import { OpportunitiesPage } from '@/pages/Opportunities';
import { OpportunityDetailPage } from '@/pages/OpportunityDetail';
import { MissionsPage } from '@/pages/Missions';
import { FeedbackPage } from '@/pages/Feedback';
import { LoginPage } from '@/pages/LoginPage';
import { useAuth } from '@/contexts/AuthContext';
import ErrorBoundary from '@/components/ErrorBoundary';

function App() {
  const { user } = useAuth();

  const ErrorFallback = () => (
    <div className="min-h-[calc(100vh-160px)] flex flex-col items-center justify-center py-8 px-6">
      <div className="text-center bg-white/5 dark:bg-gray-800/50 backdrop-blur-sm rounded-xl p-8 max-w-xl w-full">
        <h2 className="text-2xl font-bold mb-4 text-destructive">Something went wrong</h2>
        <p className="mb-6 text-text-secondary">
          We encountered an unexpected error. Please try again later or contact support if the issue persists.
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-3 bg-accent hover:bg-accent/80 text-text-primary rounded-md transition-colors duration-200"
        >
          Reload Page
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background text-text-primary transition-colors duration-200">
      <Router>
        <Header />
        <main className="flex-1">
          <ErrorBoundary fallback={<ErrorFallback />}>
            <Routes>
              <Route
                path="/login"
                element={
                  user ? <Navigate replace to="/" /> : <LoginPage />
                }
              />
              <Route
                path="/"
                element={
                  user ? <DashboardPage /> : <Navigate replace to="/login" />
                }
              />
              <Route
                path="/opportunities"
                element={
                  user ? <OpportunitiesPage /> : <Navigate replace to="/login" />
                }
              />
              <Route
                path="/opportunities/:id"
                element={
                  user ? <OpportunityDetailPage /> : <Navigate replace to="/login" />
                }
              />
              <Route
                path="/missions"
                element={
                  user ? <MissionsPage /> : <Navigate replace to="/login" />
                }
              />
              <Route
                path="/feedback"
                element={
                  user ? <FeedbackPage /> : <Navigate replace to="/login" />
                }
              />
              <Route
                path="*"
                element={<Navigate replace to="/login" />}
              />
            </Routes>
          </ErrorBoundary>
        </main>
        <Footer />
      </Router>
    </div>
  );
}

export default App;