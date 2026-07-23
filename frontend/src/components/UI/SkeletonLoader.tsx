import { cn } from '@/lib/utils';

export const SkeletonLoader = ({
  width = '100%',
  height = '1rem',
  margin = '0',
  radius = '0.25rem',
  count = 1,
}: {
  width?: string | number;
  height?: string | number;
  margin?: string;
  radius?: string | number;
  count?: number;
}) => {
  return (
    <div className={cn('flex flex-col space-y-2', { mb: typeof margin === 'string' ? margin : `${margin}px` })}>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className={cn(
            'h-[height] w-[width] rounded-[radius] bg-gradient-to-r from-gray-600 via-gray-700 to-gray-600 bg-[length:200%_100%] animate-[loading_1.5s_ease_in_out_infinite]',
            {
              width: typeof width === 'number' ? `${width}px` : width,
              height: typeof height === 'number' ? `${height}px` : height,
              radius: typeof radius === 'number' ? `${radius}px` : radius,
            }
          )}
          style={{
            backgroundSize: '200% 100%',
            animation: 'loading 1.5s ease-in-out infinite',
          }}
        ></div>
      ))}
    </div>
  );
};

// Add keyframes for animation (you might want to add this to your CSS globally)
// For simplicity, we'll include inline style but ideally this goes in index.css or tailwind
const style = document.createElement('style');
style.textContent = `
  @keyframes loading {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }
`;
document.head.appendChild(style);