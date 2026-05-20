import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Sarabun', 'Inter', 'sans-serif'],
      },
      colors: {
        sidebar: {
          DEFAULT: '#1e3a5f',
          dark: '#0f1f33'
        }
      }
    },
  },
  plugins: [],
};
export default config;
