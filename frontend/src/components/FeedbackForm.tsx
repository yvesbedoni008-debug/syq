import { useState } from 'react';
import { Button } from '@/components/UI/Button';
import { Input } from '@/components/UI/Input';
import { TextArea } from '@/components/UI/TextArea';
import { Select } from '@/components/UI/Select';
import { opportunityAPI } from '@/lib/api';

export const FeedbackForm = ({ opportunityId }: { opportunityId: number }) => {
  const [formData, setFormData] = useState({
    rating: 5,
    title: '',
    description: '',
    outcome: '',
    would_recommend: true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await opportunityAPI.createFeedback({
        opportunity_id: opportunityId,
        ...formData,
      });
      setSuccess(true);
      setFormData({
        rating: 5,
        title: '',
        description: '',
        outcome: '',
        would_recommend: true,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit feedback');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="text-center py-8">
        <div className="flex items-center justify-center mb-4">
          <div className="h-12 w-12 flex items-center justify-center bg-green-600/20 text-green-400 rounded-full">
            ✓
          </div>
        </div>
        <h3 className="font-semibold text-text-primary mb-2">Thank you for your feedback!</h3>
        <p className="text-text-secondary">Your insights help improve the SYQ Intelligence Platform for everyone.</p>
        <Button onClick={() => window.location.reload()} variant="outline">
          Submit Another Feedback
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1">
          Title
        </label>
        <Input
          type="text"
          value={formData.title}
          onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
          placeholder="Brief summary of your experience"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1">
          Description
        </label>
        <TextArea
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          placeholder="What went well? What could be improved?"
          rows={4}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Rating (1-5)
          </label>
          <div className="flex">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, rating: star }))}
                className={`
                  p-1 hover:bg-muted/50
                  ${formData.rating >= star ? 'text-yellow-400' : 'text-text-secondary/50'}
                `}
              >
                ⭐
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Outcome
          </label>
          <Input
            type="text"
            value={formData.outcome}
            onChange={(e) => setFormData(prev => ({ ...prev, outcome: e.target.value }))}
            placeholder="e.g., Made profit, Found better deal, etc."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Would recommend?
          </label>
          <Select
            value={formData.would_recommend ? 'yes' : 'no'}
            onChange={(value) => setFormData(prev => ({ ...prev, would_recommend: value === 'yes' }))}
          >
            <option value="yes">Yes, definitely</option>
            <option value="no">No, I would not recommend</option>
          </select>
        </div>
      </div>

      <div className="pt-4 border-t border-border/50">
        <Button
          type="submit"
          isLoading={loading}
          width="full"
        >
          {loading ? 'Submitting...' : 'Submit Feedback'}
        </button>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-md text-red-400">
          {error}
        </div>
      )}
    </form>
  );
};