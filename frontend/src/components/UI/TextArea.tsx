import { useState } from 'react';

interface TextAreaProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  placeholder?: string;
  rows?: number;
  className?: string;
  disabled?: boolean;
}

export const TextArea = ({
  value,
  onChange,
  placeholder = '',
  rows = 4,
  className = '',
  disabled = false
}: TextAreaProps) => {
  return (
    <textarea
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      rows={rows}
      className={`
        block w-full px-3 py-2 bg-background/70 border-border rounded-md text-text-primary
        focus:outline-none focus:ring-2 focus:ring-accent resize-y
        ${disabled ? 'cursor-not-allowed opacity-50' : ''}
      `}
      { ...(className && { className }) }
    />
  );
};