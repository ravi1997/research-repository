/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/**/*.js",
    "./node_modules/flowbite/**/*.js"
  ],
  darkMode: 'selector',
  theme: {
    extend: {
      keyframes: {
        spin: {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        spin: 'spin 1s linear infinite',
      },
    },
  },
  variants: {
    display: ['group-hover']
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('flowbite/plugin')({
      charts:true,
    }),
  ],
}

