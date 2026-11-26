import type { Config } from "tailwindcss";
export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: { extend: {
    colors: { ink: "#0A1020", panel: "#101A30", raised: "#16223D", line: "#25345A", fog: "#E8EEF9", mute: "#8C9BBA",
      ripple: "#4DA3FF", deep: "#2F6FD6", amber: "#F2B35E", coral: "#F2736A", mint: "#58D3A4" },
    fontFamily: { sans: ["Bricolage Grotesque", "ui-sans-serif", "system-ui", "sans-serif"],
      mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"] },
  } },
  plugins: [],
} satisfies Config;
