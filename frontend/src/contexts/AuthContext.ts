import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_BASE_URL } from '../lib/api';

const authClient = axios.create({ baseURL: API_BASE_URL });

interface AuthContextType {
  user: {
    id: number;
    email: string;
    name: string;
  } | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<AuthContextType['user']>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (token) {
          // Verify token with backend
          const response = await authClient.get('/users/me/', {
            headers: { Authorization: `Bearer ${token}` },
          });
          setUser({
            id: response.data.id,
            email: response.data.email,
            name: response.data.full_name || response.data.email.split('@')[0],
          });
        }
      } catch (err) {
        // Token invalid or expired
        localStorage.removeItem('access_token');
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await authClient.post('/auth/login/', {
        email,
        password,
      });
      const { access_token, user } = response.data;
      localStorage.setItem('access_token', access_token);
      setUser({
        id: user.id,
        email: user.email,
        name: user.full_name || user.email.split('@')[0],
      });
      navigate('/', { replace: true });
    } catch (err: any) {
      throw new Error(
        err.response?.data?.detail || 'Invalid email or password'
      );
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
    navigate('/login', { replace: true });
  };

  if (isLoading) {
    return <div className="flex items-center justify-center h-[100vh]">Loading...</div>;
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading: false,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {!user && !isLoading ? (
        <div>
          <p>Redirecting to login...</p>
          {/* In a real app, you'd use navigate('/login') here */}
        </div>
      ) : (
        children
      )}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};