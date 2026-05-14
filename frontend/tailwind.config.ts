import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#05070d",
        midnight: "#080f1c",
        glass: "rgba(255,255,255,0.07)",
      },
      boxShadow: {
        glow: "0 0 38px rgba(20, 184, 166, 0.22)",
        "glow-blue": "0 0 42px rgba(59, 130, 246, 0.24)",
      },
      backgroundImage: {
        "life-grid":
          "linear-gradient(rgba(255,255,255,0.055) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.055) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
} satisfies Config;
