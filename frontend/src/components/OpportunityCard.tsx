import { Link } from 'react-router-dom';
import { formatCurrency } from '@/utils/formatters';
import { Badge } from '@/components/UI/Badge';

interface OpportunityCardProps {
  opportunity: {
    id: number;
    title: string;
    description?: string;
    category?: string;
    price?: number;
    market_value?: number;
    status?: string;
    source?: string;
    created_at?: string;
  };
  onClick?: () => void;
}

export const OpportunityCard = ({ opportunity, onClick }: OpportunityCardProps) => {
  const handleClick = () => {
    if (onClick) onClick();
  };

  // Calculate discount percentage if market_value exists
  const discountPercent = opportunity.market_value && opportunity.price
    ? Math.max(0, Math.min(100, ((opportunity.market_value - opportunity.price) / opportunity.market_value) * 100))
    : null;

  return (
    <div
      className="group cursor-pointer hover:bg-background/50 backdrop-blur-sm border border-border rounded-lg p-4 transition-all duration-200"
      onClick={handleClick}
    >
      <div className="flex flex-col h-full">
        {/* Header with title and status/badge */}
        <div className="flex justify-between items-start mb-3">
          <h3 className="font-semibold text-text-primary line-clamp-2">
            {opportunity.title}
          </h3>
          {opportunity.status && (
            <Badge variant={getStatusVariant(opportunity.status)}>
              {opportunity.status.charAt(0).toUpperCase() + opportunity.status.slice(1)}
            </Badge>
          )}
        </div>

        {/* Description */}
        {opportunity.description && (
          <p className="text-text-secondary/80 line-clamp-3 flex-1 mb-4">
            {opportunity.description}
          </p>
        )}

        {/* Stats row */}
        <div className="flex flex-wrap gap-4 mt-auto pt-3 text-sm">
          {/* Price */}
          <div className="flex items-center space-x-2">
            <span className="text-text-secondary">Price:</span>
            <span className="font-medium text-text-primary">
              {opportunity.price !== undefined ? `$${formatCurrency(opportunity.price)}` : 'N/A'}
            </span>
            {discountPercent !== null && discountPercent > 0 && (
              <span className="text-sm bg-green-600/20 text-green-400 px-2 py-0.5 rounded">
                -{discountPercent.toFixed(0)}%
              </span>
            )}
          </div>

          {/* Category */}
          {opportunity.category && (
            <span className="flex items-center space-x-2">
              <span className="text-text-secondary">Category:</span>
              <span className="text-text-primary capitalize">{opportunity.category}</span>
            </span>
          )}

          {/* Source */}
          {opportunity.source && (
            <span className="flex items-center space-x-2">
              <span className="text-text-secondary">Source:</span>
              <span className="text-text-primary/80">{opportunity.source}</span>
            </span>
          )}
        </div>

        {/* Footer with date */}
        <div className="mt-4 pt-3 border-t border-border/50">
          <p className="text-xs text-text-secondary/60">
            Posted {formatDate(opportunity.created_at || '')}
          </p>
        </div>
      </div>
    </div>
  );
};

// Helper to format date
const formatDate = (dateString: string): string => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }).format(date);
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