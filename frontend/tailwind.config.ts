import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0f19",
        surface: "#111827",
        "surface-border": "#1f2937",
        card: "#151d30",
        "card-hover": "#1c263e",
        accent: {
          blue: "#3b82f6",
          green: "#10b981",
          emerald: "#059669",
          amber: "#f59e0b",
          red: "#ef4444",
          purple: "#8b5cf6"
        }
      },
    },
  },
  plugins: [],
};
export default config;
