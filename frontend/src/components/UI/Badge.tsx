import { cn } from '@/lib/utils';

interface BadgeProps {
  variant?: 'default' | 'secondary' | 'destructive';
  className?: string;
  children: React.ReactNode;
}

export const Badge = ({
  variant = 'default',
  className = '',
  children
}: BadgeProps) => {
  const baseClasses = 'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium';

  const variantClasses = {
    default: 'border-transparent bg-primary/10 text-primary',
    secondary: 'border-border/50 bg-background/50 text-text-primary',
    destructive: 'border-red-500/20 bg-red-500/10 text-red-400',
  };

  return (
    <span className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
};