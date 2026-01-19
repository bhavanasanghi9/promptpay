import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./hooks/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0B0F14",
        card: "#111827",
        border: "#1F2937",
        fg: "#E5E7EB",
        muted: "#9CA3AF",
        accent: "#2DD4BF",
        success: "#22C55E",
        warn: "#FACC15",
        danger: "#EF4444"
      }
    }
  },
  plugins: []
};
export default config;
