/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2563eb',
          dark: '#1d4ed8',
        },
        secondary: {
          DEFAULT: '#64748b',
          dark: '#475569',
        },
        dark: {
          DEFAULT: '#0f172a',
          light: '#1e293b',
        },
        light: {
          DEFAULT: '#f8fafc',
          dark: '#1e293b',
        },
        muted: {
          DEFAULT: '#64748b',
          dark: '#94a3b8',
        },
      },
    },
  },
  plugins: [],
}
