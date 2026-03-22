export default {
  content: ['./index.html', './src/**/*.{svelte,js,ts}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Segoe UI', 'sans-serif'],
      },
      colors: {
        // Mac-inspired grays
        surface: {
          50:  '#f5f5f7',
          100: '#e8e8ed',
          200: '#d2d2d7',
          300: '#aeaeb2',
          400: '#8e8e93',
          500: '#636366',
          600: '#48484a',
          700: '#3a3a3c',
          800: '#2c2c2e',
          900: '#1c1c1e',
        },
        accent: '#0071e3',  // Apple blue
      },
      borderRadius: {
        mac: '10px',
      },
    },
  },
  plugins: [],
}
