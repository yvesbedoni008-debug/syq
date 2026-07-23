import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { opportunityAPI } from '@/lib/api';
import { Card } from '@/components/UI/Card';
import { Badge } from '@/components/UI/Badge';
import { formatCurrency } from '@/utils/formatters';
import { SkeletonLoader } from '@/components/UI/SkeletonLoader';
import { AgentInsights } from '@/components/AgentInsights';
import { FeedbackForm } from '@/components/FeedbackForm';
import { TrustSignals } from '@/components/TrustSignals';

export const OpportunityDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const opportunityId = parseInt(id, 10);
  const navigate = useNavigate();

  const [opportunity, setOpportunity] = useState<any>(null);
  const [score, setScore] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadOpportunity = async () => {
      try {
        setLoading(true);
        // Fetch opportunity details
        const oppResponse = await opportunityAPI.getDetail(opportunityId);
        setOpportunity(oppResponse.data);

        // Fetch score
        const scoreResponse = await opportunityAPI.getScoreByOpportunityId(opportunityId);
        setScore(scoreResponse.data);

        // In a real app, we might also fetch agents insights, trust signals, etc.
        // But we'll load those in their respective components
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load opportunity');
        console.error('Error loading opportunity detail:', err);
      } finally {
        setLoading(false);
      }
    };

    if (!isNaN(opportunityId)) {
      loadOpportunity();
    }
  }, [opportunityId]);

  if (loading) return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center px-4">
      <div className="space-y-6">
        {/* Skeleton for opportunity header */}
        <div className="w-full">
          <SkeletonLoader width="80%" height="1.5rem" className="mb-2" />
          <SkeletonLoader width="60%" height="1rem" className="mb-2" />
          <SkeletonLoader width="40%" height="1rem" className="mb-2" />
        </div>
        {/* Skeleton for overview */}
        <div className="grid grid-cols-2 gap-4">
          <SkeletonLoader width="100%" height="4rem" />
          <SkeletonLoader width="100%" height="4rem" />
          <SkeletonLoader width="100%" height="4rem" />
          <SkeletonLoader width="100%" height="4rem" />
        </div>
        {/* Skeleton for score section */}
        <div className="space-y-4">
          <SkeletonLoader width="100%" height="2rem" className="mb-2" />
          <SkeletonLoader width="50%" height="1.5rem" className="mb-2" />
          <SkeletonLoader width="50%" height="1.5rem" className="mb-2" />
          <SkeletonLoader width="100%" height="4rem" className="mb-2" />
        </div>
      </div>
    </div>
  );

  if (error) return (
    <div className="p-6 text-center">
      <h2 className="text-xl font-bold mb-4 text-destructive">Error loading opportunity</h2>
      <p className="text-text-secondary">{error}</p>
      <button onClick={() => navigate(-1)} className="mt-4 px-4 py-2 bg-accent hover:bg-accent/80 text-text-primary rounded-md">
        Go Back
      </button>
    </div>
  );

  if (!opportunity) return (
    <div className="p-6 text-center">
      <h2 className="text-xl font-bold mb-4 text-text-secondary">Opportunity not found</h2>
      <button onClick={() => navigate(-1)} className="mt-4 px-4 py-2 bg-accent hover:bg-accent/80 text-text-primary rounded-md">
        Go Back
      </button>
    </div>
  );

  return (
    <div className="min-h-[calc(100vh-200px)] py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-text-primary">{opportunity.title}</h1>
            <div className="flex flex-wrap gap-3 mt-2">
              {opportunity.status && (
                <Badge variant={getStatusVariant(opportunity.status)}>
                  {opportunity.status.charAt(0).toUpperCase() + opportunity.status.slice(1)}
                </Badge>
              )}
              {opportunity.category && (
                <span className="px-3 py-1 bg-muted/50 rounded-md text-sm text-text-secondary capitalize">
                  {opportunity.category}
                </span>
              )}
              {opportunity.source && (
                <span className="px-3 py-1 bg-muted/50 rounded-md text-sm text-text-secondary">
                  {opportunity.source}
                </span>
              )}
            </div>
          </div>
          <div className="text-right">
            <button
              onClick={() => navigate(-1)}
              className="px-4 py-2 bg-border/50 hover:bg-border/100 text-text-sm rounded-md"
            >
              Back to List
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main content */}
          <div className="col-span-2">
            {/* Overview Section */}
            <section className="mb-6">
              <div className="space-y-4">
                <div className="border-b border-border/50 pb-4">
                  <h2 className="text-lg font-semibold text-text-primary">Overview</h2>
                  <p className="text-text-secondary">{opportunity.description || 'No description available.'}</p>
                </div>

                <div className="grid grid-cols-2 gap-4 md:grid-cols-4 text-sm">
                  <div>
                    <p className="text-text-secondary">Price</p>
                    <p className="text-text-primary font-medium">
                      {opportunity.price !== undefined ? `$${formatCurrency(opportunity.price)}` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-text-secondary">Market Value</p>
                    <p className="text-text-primary font-medium">
                      {opportunity.market_value !== undefined ? `$${formatCurrency(opportunity.market_value)}` : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-text-secondary">Condition</p>
                    <p className="text-text-primary">{opportunity.condition || 'Not specified'}</p>
                  </div>
                  <div>
                    <p className="text-text-secondary">Location</p>
                    <p className="text-text-primary">{opportunity.location || 'Not specified'}</p>
                  </div>
                </div>
              </div>
            </section>

            {/* SYQ Score Section */}
            {score && (
              <section className="mb-6">
                <div className="border-b border-border/50 pb-4">
                  <h2 className="text-lg font-semibold text-text-primary">SYQ Score Analysis</h2>
                </div>
                <div className="space-y-4">
                  {/* Score breakdown would go here - simplified for now */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <p className="text-text-secondary">Overall Score</p>
                      <p className="text-3xl font-bold text-text-primary">{score.overall_score}/100</p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-xs text-text-secondary">Value: {score.value_score}/100</p>
                      <p className="text-xs text-text-secondary">Price: {score.price_score}/100</p>
                      <p className="text-xs text-text-secondary">Demand: {score.demand_score}/100</p>
                      <p className="text-xs text-text-secondary">Safety: {score.risk_score_inverted}/100</p>
                      <p className="text-xs text-text-secondary">Confidence: {score.confidence_score}/100</p>
                    </div>
                  </div>
                  <div className="bg-background/50 backdrop-blur-sm border border-border rounded-lg p-4 mt-4">
                    <h3 className="font-semibold text-text-primary mb-2">Explanation</h3>
                    <p className="text-text-secondary">{score.explanation || 'No detailed explanation available.'}</p>
                  </div>
                </div>
              </section>
            )}

            {/* Agent Insights */}
            <section className="mb-6">
              <AgentInsights opportunityId={opportunityId} />
            </section>

            {/* Trust Signals */}
            <section className="mb-6">
              <TrustSignals opportunityId={opportunityId} />
            </section>

            {/* Feedback Section */}
            <section>
              <h2 className="mb-4 text-xl font-semibold text-text-primary">Share Your Experience</h2>
              <FeedbackForm opportunityId={opportunityId} />
            </section>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            {/* Quick Actions */}
            <Card title="Quick Actions">
              <div className="space-y-4">
                <button
                  onClick={() => {/* Save to watchlist */}}
                  className="w-full flex items-center justify-start px-4 py-2 text-left border border-border/50 rounded-lg hover:bg-accent/10"
                >
                  <span className="mr-3">💾</span>
                  Save to Watchlist
                </button>
                <button
                  onClick={() => {/* Share */}}
                  className="w-full flex items-center justify-start px-4 py-2 text-left border border-border/50 rounded-lg hover:bg-accent/10"
                >
                  <span className="mr-3">📤</span>
                  Share Opportunity
                </button>
                <button
                  onClick={() => {/* Start negotiation */}}
                  className="w-full flex items-center justify-start px-4 py-2 text-left border border-border/50 rounded-lg hover:bg-accent/10"
                >
                  <span className="mr-3">💬</span>
                  Start Negotiation
                </button>
                <button
                  onClick={() => {/* Create mission */}}
                  className="w-full flex items-center justify-start px-4 py-2 text-left border border-border/50 rounded-lg hover:bg-accent/10"
                >
                  <span className="mr-3">🎯</span>
                  Create Mission from this
                </button>
              </div>
            </Card>

            {/* Similar Opportunities */}
            <Card title="Similar Opportunities">
              {/* In real app, this would fetch from API */}
              <div className="space-y-3">
                <div className="text-text-center py-4">
                  <p className="text-text-secondary">Similar opportunities will appear here based on AI analysis</p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper to get badge variant based on status
const getStatusVariant = (status: string): 'default' | 'secondary' | 'destructive' => {
  switch (status.toLowerCase()) {
    case 'active': return 'default';
    case 'sold': return 'secondary';
    case 'expired': return 'destructive';
    case 'inactive': return 'secondary';
    default: return 'default';
  }
};