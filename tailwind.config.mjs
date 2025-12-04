/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,ts,tsx,vue,svelte}'],
  theme: {
    extend: {
      colors: {
        inkq: {
          gray: {
            0: '#ffffff',
            1: '#f5f5f5',
            2: '#e5e5e5',
            3: '#d4d4d4',
            4: '#a3a3a3',
            5: '#737373',
            6: '#404040',
            7: '#0a0a0a',
          },
        },
      },
    },
  },
  plugins: [],
};

