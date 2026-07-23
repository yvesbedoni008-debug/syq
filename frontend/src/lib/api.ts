import axios, { AxiosInstance } from 'axios';

export const API_BASE_URL =
  process.env.REACT_APP_API_URL ||
  process.env.VITE_API_URL ||
  (process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1');

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for global error handling (optional)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // You can redirect to login on 401, etc.
    return Promise.reject(error);
  }
);

// Types for API responses
export interface Opportunity {
  id: number;
  title: string;
  description?: string | null;
  category?: string | null;
  source?: string | null;
  price: number | null;
  market_value: number | null;
  status: 'active' | 'sold' | 'expired' | 'inactive';
  condition?: string | null;
  location?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OpportunityScore {
  id: number;
  opportunity_id: number;
  overall_score: number; // 0-100
  value_score: number; // 0-100
  price_score: number; // 0-100
  demand_score: number; // 0-100
  risk_score: number; // 0-100 (lower is better risk)
  risk_score_inverted: number; // 0-100 (higher is safer)
  confidence_score: number; // 0-100
  explanation: string;
  calculated_at: string;
  updated_at: string;
}

export interface AgentInsight {
  discovery: AgentAnalysis;
  market: AgentAnalysis;
  price: AgentAnalysis;
  trust: AgentAnalysis;
  risk: AgentAnalysis;
  personal: AgentAnalysis;
  strategy: AgentAnalysis;
  negotiation: AgentAnalysis;
  synthesis: {
    summary: string;
    action_recommended?: string;
    confidence_level?: number; // 0-100
  };
}

export interface AgentAnalysis {
  score: number; // 0-100
  findings: string[];
  recommendations: string[];
}

export interface TrustSignal {
  id: number;
  opportunity_id: number;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  explanation: string;
  created_at: string;
}

export interface Feedback {
  id: number;
  opportunity_id: number;
  user_id: number;
  rating: number; // 1-5
  title: string;
  description?: string | null;
  outcome?: string | null;
  would_recommend: boolean;
  created_at: string;
}

export interface MarketOverview {
  categories: Array<{
    category: string;
    opportunity_count: number;
    avg_price: number;
    min_price: number;
    max_price: number;
    price_stddev: number;
  }>;
  overall: {
    total_opportunities: number;
    avg_price: number;
    median_price: number;
    price_stddev: number;
  };
  trend_indicators: {
    upward_momentum_percent: number;
    downward_momentum_percent: number;
    note: string;
  };
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// API service
export const opportunityAPI = {
  // Opportunities
  getFeed: (params?: {
    skip?: number;
    limit?: number;
    category?: string;
    min_price?: number;
    max_price?: number;
    status?: string;
  }) =>
    apiClient.get<PaginatedResponse<Opportunity>>('/opportunities/', {
      params,
    }),

  getDetail: (id: number) =>
    apiClient.get<Opportunity>(`/opportunities/${id}/`),

  getScore: (id: number) =>
    apiClient.get<OpportunityScore>(`/opportunities/${id}/score/`),

  getAgentInsights: (id: number) =>
    apiClient.get<AgentInsights>(`/opportunities/${id}/agents/`),

  // Trust Signals
  getTrustSignalsByOpportunityId: (id: number) =>
    apiClient.get<TrustSignal[]>(`/trust-signals/opportunity/${id}/`),

  // Market Overview
  getMarketOverview: () =>
    apiClient.get<MarketOverview>('/market/overview/'),

  // Feedback
  createFeedback: (data: {
    opportunity_id: number;
    rating: number;
    title: string;
    description?: string;
    outcome?: string;
    would_recommend: boolean;
  }) => apiClient.post<Feedback>('/feedbacks/', data),

  getUserFeedback: (userId: number) =>
    apiClient.get<PaginatedResponse<Feedback>>(
      `/feedbacks/?user_id=${userId}`
    ),
};

export default apiClient;