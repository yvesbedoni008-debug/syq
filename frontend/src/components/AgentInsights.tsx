import { useState, useEffect } from 'react';
import { opportunityAPI } from '@/lib/api';
import { AgentCard } from '@/components/AgentCard';
import { SkeletonLoader } from '@/components/UI/SkeletonLoader';

interface AgentInsightsProps {
  opportunityId: number;
}

export const AgentInsights = ({ opportunityId }: AgentInsightsProps) => {
  const [insights, setInsights] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        setLoading(true);
        const response = await opportunityAPI.getAgentInsights(opportunityId);
        setInsights(response.data);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load agent insights');
        console.error('Error fetching agent insights:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, [opportunityId]);

  if (loading) return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 py-8">
      {/* 8 skeleton cards for agents */}
      {[...Array(8)].map((_, index) => (
        <AgentSkeleton key={index} />
      ))}
    </div>
  );

  if (error) return (
    <div className="p-6 text-center">
      <h2 className="text-xl font-bold mb-4 text-destructive">Error Loading Insights</h2>
      <p className="text-text-secondary">{error}</p>
    </div>
  );

  if (!insights) return (
    <div className="text-center py-8">
      <p className="text-text-secondary">No agent insights available for this opportunity.</p>
    </div>
  );

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-text-primary mb-4">AI Agent Analysis</h2>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Discovery Agent */}
        <AgentCard
          title="Discovery Agent"
          description="Analyzes sourcing quality, listing authenticity, and opportunity discovery quality"
          score={insights.discovery?.score || 0}
          findings={insights.discovery?.findings || []}
          recommendations={insights.discovery?.recommendations || []}
          icon="🔍"
        />

        {/* Market Agent */}
        <AgentCard
          title="Market Agent"
          description="Evaluates market demand, trends, and comparables"
          score={insights.market?.score || 0}
          findings={insights.market?.findings || []}
          recommendations={insights.market?.recommendations || []}
          icon="📊"
        />

        {/* Price Agent */}
        <AgentCard
          title="Price Agent"
          description="Assesses pricing fairness, valuation models, and negotiation potential"
          score={insights.price?.score || 0}
          findings={insights.price?.findings || []}
          recommendations={insights.price?.recommendations || []}
          icon="💰"
        />

        {/* Trust Agent */}
        <AgentCard
          title="Trust Agent"
          description="Evaluates seller reliability, platform trust signals, and risk factors"
          score={insights.trust?.score || 0}
          findings={insights.trust?.findings || []}
          recommendations={insights.trust?.recommendations || []}
          icon="🛡️"
        />

        {/* Risk Agent */}
        <AgentCard
          title="Risk Agent"
          description="Identifies potential risks, fraud indicators, and mitigation strategies"
          score={insights.risk?.score || 0}
          findings={insights.risk?.findings || []}
          recommendations={insights.risk?.recommendations || []}
          icon="⚠️"
        />

        {/* Personal Agent */}
        <AgentCard
          title="Personal Agent"
          description="Matches opportunity to your preferences, budget, and risk tolerance"
          score={insights.personal?.score || 0}
          findings={insights.personal?.findings || []}
          recommendations={insights.personal?.recommendations || []}
          icon="👤"
        />

        {/* Strategy Agent */}
        <AgentCard
          title="Strategy Agent"
          description="Recommends optimal acquisition and disposition strategies"
          score={insights.strategy?.score || 0}
          findings={insights.strategy?.findings || []}
          recommendations={insights.strategy?.recommendations || []}
          icon="♟️"
        />

        {/* Negotiation Agent */}
        <AgentCard
          title="Negotiation Agent"
          description="Provides negotiation tactics, price anchors, and deal structuring advice"
          score={insights.negotiation?.score || 0}
          findings={insights.negotiation?.findings || []}
          recommendations={insights.negotiation?.recommendations || []}
          icon="🤝"
        />
      </div>

      {/* Synthesis and Recommendation */}
      {insights.synthesis && (
        <div className="bg-background/50 backdrop-blur-sm border border-border rounded-lg p-6">
          <h3 className="font-semibold text-text-primary mb-4">Strategic Recommendation</h3>
          <p className="text-text-secondary mb-4">{insights.synthesis.summary || 'No summary available.'}</p>

          {insights.synthesis.action_recommended && (
            <div className="space-y-3">
              <p className="font-medium text-text-primary">Recommended Action:</p>
              <p className="text-text-secondary">{insights.synthesis.action_recommended}</p>
            </div>
          )}

          {insights.synthesis.confidence_level && (
            <div className="flex items-center mt-4">
              <span className="mr-3">Confidence:</span>
              <div className="flex-1">
                <div className="w-full bg-border/50 rounded-full h-2.5">
                  <div className={`h-2.5 bg-accent rounded-full transition-all width-[${insights.synthesis.confidence_level}%]`}></div>
                </div>
              </div>
              <span className="ml-3 text-xs">{`${insights.synthesis.confidence_level}%`}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Skeleton for an agent card
const AgentSkeleton = () => (
  <div className="border border-border/50 rounded-lg bg-background/80 backdrop-blur-sm p-4">
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center space-x-3">
        <SkeletonLoader width="20%" height="1.5rem" className="mr-3" />
        <div>
          <SkeletonLoader width="60%" height="1.25rem" className="mb-1" />
          <SkeletonLoader width="40%" height="1rem" />
        </div>
      </div>
      <div className="text-right">
        <SkeletonLoader width="25%" height="1.75rem" className="mb-1" />
        <SkeletonLoader width="25%" height="1rem" className="text-text-secondary/60 text-xs" />
      </div>
    </div>

    {/** Findings placeholder */}
    <div className="mt-3">
      <SkeletonLoader width="60%" height="1rem" className="mb-1" />
      <SkeletonLoader width="40%" height="1rem" className="mb-1" />
      <SkeletonLoader width="50%" height="1rem" className="mb-1" />
    </div>

    {/** Recommendations placeholder */}
    <div className="mt-3 pt-3 border-t border-border/50">
      <SkeletonLoader width="60%" height="1rem" className="mb-1" />
      <SkeletonLoader width="40%" height="1rem" className="mb-1" />
      <SkeletonLoader width="50%" height="1rem" className="mb-1" />
    </div>
  </div>
);