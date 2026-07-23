export const Spinner = ({ size = 'sm' }: { size?: 'xs' | 'sm' | 'md' | 'lg' }) => {
  const sizeMap = {
    xs: 'h-3 w-3',
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  };

  return (
    <div className={`animate-spin rounded-full border-2 border-solid border-current border-t-transparent ${sizeMap[size]}`}>
      <span className="sr-only">Loading...</span>
    </div>
  );
};