module.exports = {
  mode: 'jit',
  content: [
    '../templates/**/*.html',
    './node_modules/flowbite/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          700: '#166534'
        }
      }
    }
  },
  variants: {},
  plugins: [
    require('flowbite/plugin'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio')
  ]
}