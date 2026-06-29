/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: '#0a0e17',
          card: '#111827',
          border: '#1e293b',
          accent: '#f0b90b',
          'accent-blue': '#0ea5e9',
          green: '#00c853',
          red: '#ff1744',
          text: '#e2e8f0',
          muted: '#64748b',
          hover: '#1e3a5f',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'scroll-up': 'scrollUp 0.5s ease-out',
        'pulse-slow': 'pulse 3s infinite',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'fade-in': 'fadeIn 0.5s ease-out',
        'glow': 'glow 2s infinite',
        'ticker': 'ticker 30s linear infinite',
      },
      keyframes: {
        scrollUp: {
          '0%': { transform: 'translateY(0)', opacity: '1' },
          '100%': { transform: 'translateY(-10px)', opacity: '0' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        glow: {
          '0%, 100%': { boxShadow: '0 0 5px rgba(240, 185, 11, 0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(240, 185, 11, 0.6)' },
        },
        ticker: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
      },
    },
  },
  plugins: [],
};