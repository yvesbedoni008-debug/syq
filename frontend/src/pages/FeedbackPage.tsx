import { useState } from 'react';
import { Button } from '@/components/UI/Button';
import { Input } from '@/components/UI/Input';
import { Card } from '@/components/UI/Card';
import { textareaAPI } from '@/lib/api'; // We'll create this or use opportunityAPI

export const FeedbackPage = () => {
  const [formState, setFormState] = useState({
    opportunity_id: '',
    rating: 5,
    comment: '',
    outcome: '',
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      // In real app, this would call an API endpoint
      console.log('Submitting feedback:', formState);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSuccess(true);
      // Reset form after success
      setFormState({
        opportunity_id: '',
        rating: 5,
        comment: '',
        outcome: '',
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit feedback');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-xl mx-auto py-8 px-4">
        <Card className="text-center">
          <h2 className="mb-4 text-xl font-semibold text-text-primary">Thank you!</h2>
          <p className="text-text-secondary">Your feedback has been submitted and will help improve the platform.</p>
          <Button onClick={() => setSuccess(false)} variant="outline">
            Give more feedback
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-200px)] py-8">
      <div className="max-w-xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Share Your Feedback</h1>
            <p className="text-text-secondary">Help us improve by sharing your experience with recent opportunities.</p>
          </div>

          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded-lg">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Opportunity ID (optional)
              </label>
              <Input
                type="number"
                value={formState.opportunity_id}
                onChange={(e) => setFormState({ ...formState, opportunity_id: e.target.value })}
                placeholder="Enter opportunity ID"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Rating (1-5 stars)
              </label>
              <div className="flex space-x-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setFormState({ ...formState, rating: star })}
                    className={`flex-1 p-2 text-center border border-border/50 rounded-lg hover:bg-muted/50 ${formState.rating >= star ? 'bg-accent/20 text-accent' : 'text-text-secondary'}`}
                  >
                    {star}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                What was the outcome?
              </label>
              <Input
                type="text"
                value={formState.outcome}
                onChange={(e) => setFormState({ ...formState, outcome: e.target.value })}
                placeholder="e.g., Made profit, Found better deal, Decided not to pursue, etc."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Additional comments
              </label>
              <textarea
                value={formState.comment}
                onChange={(e) => setFormState({ ...formState, comment: e.target.value })}
                className="block w-full px-4 py-2 bg-background/70 border-border rounded-md text-text-primary focus:outline-none focus:ring-2 focus:ring-accent resize-y"
                rows={4}
                placeholder="Share any details about your experience..."
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`w-flex flex-col items-center justify-center gap-2 px-6 py-3 text-sm font-medium transition-all duration-200
                ${loading
                  ? 'bg-muted/50 cursor-not-allowed'
                  : 'bg-accent hover:bg-accent/80 text-text-primary'}
              `}
            >
              {loading ? (
                <>
                  <span className="animate-spin h-4 w-4 border-b-2 border-current"></span>
                  <span className="ml-2">Submitting...</span>
                </>
              ) : (
                <>
                  Submit Feedback
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};