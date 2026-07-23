/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors inspired by bymonolog's dark aesthetic
        'bg-primary': '#000000',
        'bg-secondary': '#0a0a0a',
        'text-primary': '#f8fafc',
        'text-secondary': '#94a3b8',
        'accent': '#60a5fa', // soft blue for AI/tech feel
        'accent-hover': '#3b82f6',
        'muted': '#1e293b',
        'border': '#334155',
      },
      fontFamily: {
        // Using Inter for neutrality and readability, common in modern UIs
        'sans': ['Inter var', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      typography: ({ theme }) => ({
        DEFAULT: {
          css: {
            color: theme('colors.text.primary'),
            '[class~="lead"]': {
              color: theme('colors.text.secondary'),
            },
            a: {
              color: theme('colors.accent'),
              '&:hover': {
                color: theme('colors.accent.hover'),
              },
            },
            strong: {
              color: theme('colors.text.primary'),
            },
            'ol > li::before': {
              backgroundColor: theme('colors.accent'),
            },
            'ul > li::before': {
              backgroundColor: theme('colors.accent'),
            },
            hr: {
              borderColor: theme('colors.border'),
            },
            blockquote: {
              color: theme('colors.text.secondary'),
              borderLeftColor: theme('colors.border'),
            },
          },
        },
        dark: {
          css: {
            color: theme('colors.text.primary'),
            '[class~="lead"]': {
              color: theme('colors.text.secondary'),
            },
            a: {
              color: theme('colors.accent'),
              '&:hover': {
                color: theme('colors.accent.hover'),
              },
            },
            strong: {
              color: theme('colors.text.primary'),
            },
            'ol > li::before': {
              backgroundColor: theme('colors.accent'),
            },
            'ul > li::before': {
              backgroundColor: theme('colors.accent'),
            },
            hr: {
              borderColor: theme('colors.border'),
            },
            blockquote: {
              color: theme('colors.text.secondary'),
              borderLeftColor: theme('colors.border'),
            },
          },
        },
      }),
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}