import { cn } from '@/lib/utils';

interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
  disabled?: boolean;
  children: React.ReactNode;
}

export const Select = ({
  value,
  onChange,
  className = '',
  disabled = false,
  children
}: SelectProps) => {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={cn(
        'block w-full px-3 py-2 bg-background/70 border-border rounded-md text-text-primary focus:outline-none focus:ring-2 focus:ring-accent',
        { 'cursor-not-allowed opacity-50': disabled },
        className
      )}
      disabled={disabled}
    >
      {children}
    </select>
  );
};