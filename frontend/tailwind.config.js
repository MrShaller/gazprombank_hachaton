/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Цвета Газпромбанка
        gazprom: {
          blue: '#1e3a8a',
          'blue-dark': '#1e2a5a',
          'blue-light': '#3b82f6',
        },
        // Цвета тональностей
        sentiment: {
          positive: '#22c55e', // Зеленый
          neutral: '#6b7280',  // Серый
          negative: '#f97316', // Оранжевый
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
