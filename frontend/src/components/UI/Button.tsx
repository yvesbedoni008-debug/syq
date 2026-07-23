import { cn } from '@/lib/utils';

interface ButtonProps {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  isLoading?: boolean;
  width?: 'auto' | 'full';
  asChild?: boolean;
  className?: string;
  children?: React.ReactNode;
  // Pass through all button props
  type?: 'submit' | 'button' | 'reset';
  disabled?: boolean;
  onClick?: () => void;
}

const Button = React.forwardRef<
  HTMLButtonElement | HTMLAnchorElement,
  ButtonProps
>(({
  variant = 'default',
  size = 'default',
  isLoading = false,
  width = 'auto',
  asChild = false,
  className = '',
  children,
  type = 'button',
  disabled = false,
  onClick,
  ...props
}, ref) => {
  const Component = asChild ? 'a' : 'button';

  const baseClasses = 'inline-flex items-center justify-center rounded-md border font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50';

  const variantClasses = {
    default: 'border-primary bg-primary text-text-primary hover:bg-primary/80',
    destructive: 'border-destructive bg-destructive text-text-primary hover:bg-destructive/80',
    outline: 'border-border hover:bg-background/50 hover:text-text-primary',
    secondary: 'border-border bg-background/50 text-text-primary hover:bg-background',
  };

  const sizeClasses = {
    default: 'h-10 px-4 py-2 text-sm',
    sm: 'h-9 px-3 rounded-md text-xs',
    lg: 'h-11 px-6 text-base',
    icon: 'h-10 w-10',
  };

  const widthClasses = {
    auto: '',
    full: 'w-full',
  };

  return (
    <Component
      ref={ref}
      asChild={asChild}
      type={type}
      disabled={disabled || isLoading}
      onClick={onClick}
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        widthClasses[width],
        className,
        isLoading && 'opacity-70 cursor-not-allowed'
      )}
      {...props}
    >
      {isLoading ? (
        <span className="inline-block h-4 w-4 animate-spin border-2 border-current border-r-transparent rounded-full"></span>
      ) : (
        children
      )}
    </Component>
  );
});

Button.displayName = 'Button';

export { Button };