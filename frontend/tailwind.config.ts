import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#101828",
        mist: "#F4F1EA",
        ember: "#C7512D",
        pine: "#0F4C3A",
        gold: "#D4A72C",
      },
      fontFamily: {
        display: ["Iowan Old Style", "Palatino Linotype", "Book Antiqua", "Times New Roman", "serif"],
        body: ["Avenir Next", "Avenir", "Segoe UI", "Helvetica Neue", "sans-serif"],
      },
      boxShadow: {
        panel: "0 18px 40px rgba(16, 24, 40, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
