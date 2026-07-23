import { cn } from '@/lib/utils';
import { useState } from 'react';

interface InputProps {
  type?: string;
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
  className?: string;
  required?: boolean;
  autoFocus?: boolean;
  disabled?: boolean;
  // Allow spreading other props (like id, name, etc.)
  [key: string]: any;
}

export const Input = ({
  type = 'text',
  label,
  placeholder = '',
  value,
  onChange,
  error,
  className = '',
  required = false,
  autoFocus = false,
  disabled = false,
  ...rest
}: InputProps) => {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className="space-y-1">
      {label && (
        <label
          className={cn(
            'block text-sm font-medium text-text-secondary',
            { 'text-text-primary/70': isFocused || !!value },
            'transition-colors'
          )}
        >
          {label}
          {required && <span className="text-destructive">*</span>}
        </label>
      )}
      <div className="relative">
        <input
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={(e) => {
            onChange(e);
            setIsFocused(true);
          }}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          className={cn(
            'block w-full rounded-md border border-input bg-background/80 px-3 py-2 text-sm font-normal text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent',
            { 'border-destructive': !!error },
            className
          )}
          autoFocus={autoFocus}
          disabled={disabled}
          {...rest}
        />
        {error && (
          <p className="mt-1 text-sm text-destructive">
            {error}
          </p>
        )}
      </div>
    </div>
  );
};