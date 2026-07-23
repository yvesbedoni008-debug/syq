import { cn } from '@/lib/utils';

interface CardProps {
  title?: string;
  className?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export const Card = ({
  title,
  className = '',
  children,
  footer
}: CardProps) => {
  return (
    <div className={cn(
      'border border-border/50 rounded-lg bg-background/80 backdrop-blur-sm',
      className
    )}>
      {title && (
        <div className="px-4 py-3 font-semibold text-text-primary border-b border-border/50">
          {title}
        </div>
      )}
      <div className="p-4">{children}</div>
      {footer && (
        <div className="px-4 py-3 text-xs border-t border-border/50">
          {footer}
        </div>
      )}
    </div>
  );
};