module.exports = {
  mode: 'jit',
  content: ['./app/templates/**/*.html', "./node_modules/flowbite/**/*.js"],
  theme: {
    extend: {},
  },
  variants: {},
  plugins: [
    require('flowbite/plugin'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio')
]
}
