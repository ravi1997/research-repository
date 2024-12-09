/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/**/*.js"
  ],
  darkMode: 'selector',
  theme: {
    extend: {},
  },
  variants: {
    display: ['group-hover']
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

