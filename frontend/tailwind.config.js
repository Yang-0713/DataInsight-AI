/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#17213a',
        brand: '#5b5cf0',
      },
    },
  },
  plugins: [],
}

