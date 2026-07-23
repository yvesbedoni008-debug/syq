import { useState, useEffect } from 'react';
import { opportunityAPI } from '@/lib/api';
import { TrustSignalBadge } from '@/components/TrustSignalBadge';
import { Spinner } from '@/components/UI/Spinner';

interface TrustSignalsProps {
  opportunityId: number;
}

export const TrustSignals = ({ opportunityId }: TrustSignalsProps) => {
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSignals = async () => {
      try {
        setLoading(true);
        const response = await opportunityAPI.getTrustSignalsByOpportunityId(opportunityId);
        setSignals(response.data || []);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load trust signals');
        console.error('Error fetching trust signals:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSignals();
  }, [opportunityId]);

  if (loading) return (
    <div className="flex flex-col items-center py-8">
      <div className="space-x-3">
        <Spinner size="sm" />
        <Spinner size="sm" />
        <Spinner size="sm" />
      </div>
      <p className="mt-2 text-text-secondary">Loading trust signals...</p>
    </div>
  );

  if (error) return (
    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-md text-red-400">
      {error}
    </div>
  );

  if (signals.length === 0) return (
    <div className="text-center py-6">
      <p className="text-text-secondary">No trust signals available for this opportunity.</p>
    </div>
  );

  return (
    <div className="space-y-4">
      <h2 className="font-semibold text-text-primary mb-2">Trust Signals</h2>
      <div className="flex flex-wrap gap-2">
        {signals.map((signal, index) => (
          <TrustSignalBadge key={index} signal={signal} />
        ))}
      </div>
    </div>
  );
};

// TrustSignalBadge component
const TrustSignalBadge = ({ signal }: { signal: any }) => {
  // Determine color based on severity
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-red-500/20 text-red-400';
      case 'high': return 'bg-orange-500/20 text-orange-400';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400';
      case 'low': return 'bg-green-500/20 text-green-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  return (
    <div className={`px-3 py-1.5 rounded text-xs font-medium ${getSeverityColor(signal.severity || 'low')}`}>
      {signal.type || 'Unknown'}: {signal.explanation || 'No details'}
    </div>
  );
};