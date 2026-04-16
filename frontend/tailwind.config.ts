import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'owl': '#8B7355',
        'owl-light': '#D4A574',
      }
    },
  },
  plugins: [],
}

export default config
