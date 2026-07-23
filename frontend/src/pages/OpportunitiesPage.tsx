import { useEffect, useState, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { opportunityAPI } from '@/lib/api';
import { OpportunityCard } from '@/components/OpportunityCard';
import { SkeletonLoader } from '@/components/UI/SkeletonLoader';

export const OpportunitiesPage = () => {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    category: '',
    min_price: '',
    max_price: '',
    status: '',
  });
  const navigate = useNavigate();
  const wsRef = useRef<WebSocket | null>(null);

  const fetchOpportunities = async () => {
    try {
      setLoading(true);
      const response = await opportunityAPI.getFeed(filters);
      setOpportunities(response.data.results || response.data || []); // Adjust based on actual API response
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load opportunities');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpportunities();
  }, [filters]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/opportunities`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected for opportunity updates');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type && ['opportunity_created', 'opportunity_updated', 'opportunity_deleted'].includes(data.type)) {
          // Refresh the list when any opportunity changes
          fetchOpportunities();
        }
      } catch (e) {
        console.warn('Failed to parse WebSocket message', e);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      wsRef.current = null;
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, []); // Empty deps to run once

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleClearFilters = () => {
    setFilters({
      category: '',
      min_price: '',
      max_price: '',
      status: '',
    });
  };

  if (loading) return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center py-12">
      <div className="space-y-4">
        {[...Array(6)].map((_, index) => (
          <SkeletonLoader
            key={index}
            width={index % 2 === 0 ? '70%' : '100%'}
            height="1.5rem"
            className="mb-1"
          />
        ))}
      </div>
    </div>
  );

  if (error) return (
    <div className="p-6 text-center">
      <h2 className="text-xl font-bold mb-4 text-destructive">Error loading opportunities</h2>
      <p className="text-text-secondary">{error}</p>
      <button onClick={fetchOpportunities} className="mt-4 px-4 py-2 bg-accent hover:bg-accent/80 text-text-primary rounded-md">
        Retry
      </button>
    </div>
  );

  return (
    <div className="min-h-[calc(100vh-200px)] py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-col sm:flex-row sm:items-start sm:justify-between">
          <h1 className="text-2xl font-bold text-text-primary">Opportunity Feed</h1>
          <div className="flex space-x-3 mt-4 sm:mt-0">
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 bg-muted hover:bg-muted/80 text-text-sm rounded-md"
            >
              Clear Filters
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-background/50 backdrop-blur-sm border border-border rounded-lg p-4 mb-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4 sm:gap-6">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">Category</label>
              <select
                name="category"
                value={filters.category}
                onChange={handleFilterChange}
                className="w-full px-3 py-2 bg-background/70 border-border rounded-md text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
              >
                <option value="">All Categories</option>
                <option value="Electronics">Electronics</option>
                <option value="Vehicles">Vehicles</option>
                <option value="Real Estate">Real Estate</option>
                <option value="Collectibles">Collectibles</option>
                <option value="Fashion">Fashion</option>
                <option value="Home & Garden">Home & Garden</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">Min Price ($)</label>
              <input
                name="min_price"
                type="number"
                value={filters.min_price}
                onChange={handleFilterChange}
                className="w-full px-3 py-2 bg-background/70 border-border rounded-md text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="Min"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">Max Price ($)</label>
              <input
                name="max_price"
                type="number"
                value={filters.max_price}
                onChange={handleFilterChange}
                className="w-full px-3 py-2 bg-background/70 border-border rounded-md text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="Max"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">Status</label>
              <select
                name="status"
                value={filters.status}
                onChange={handleFilterChange}
                className="w-full px-3 py-2 bg-background/70 border-border rounded-md text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
              >
                <option value="">All Statuses</option>
                <option value="active">Active</option>
                <option value="sold">Sold</option>
                <option value="expired">Expired</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
        </div>

        {/* Results count */}
        <div className="mb-4 flex items-center justify-between">
          <p className="text-sm text-text-secondary">
            Showing {opportunities.length} opportunities
          </p>
        </div>

        {/* Opportunities grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {opportunities.map(opp => (
            <OpportunityCard
              key={opp.id}
              opportunity={opp}
              onClick={() => navigate(`/opportunities/${opp.id}`)}
            />
          ))}
          {opportunities.length === 0 && (
            <div className="col-span-full text-center py-12">
              <p className="text-text-secondary">No opportunities match your filters.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};