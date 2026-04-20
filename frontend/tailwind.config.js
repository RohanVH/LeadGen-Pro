/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        mist: "#f8fafc",
        slateglass: "#e2e8f0",
        accent: "#0f766e",
        accepthigh: "#b91c1c",
        acceptlow: "#065f46",
      },
      fontFamily: {
        sans: ["Manrope", "sans-serif"],
        display: ["Space Grotesk", "sans-serif"],
      },
      boxShadow: {
        card: "0 8px 30px rgba(15, 23, 42, 0.08)",
        glow: "0 0 0 1px rgba(99, 102, 241, 0.08), 0 20px 50px -12px rgba(79, 70, 229, 0.15)",
        "glow-lg": "0 0 0 1px rgba(99, 102, 241, 0.06), 0 25px 60px -15px rgba(79, 70, 229, 0.2)",
      },
      backgroundImage: {
        "mesh-light":
          "radial-gradient(at 0% 0%, rgba(79, 70, 229, 0.14) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(124, 58, 237, 0.1) 0px, transparent 48%), radial-gradient(at 100% 100%, rgba(14, 165, 233, 0.06) 0px, transparent 45%)",
        "mesh-dark":
          "radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.18) 0px, transparent 50%), radial-gradient(at 100% 30%, rgba(124, 58, 237, 0.12) 0px, transparent 50%), radial-gradient(at 50% 100%, rgba(14, 165, 233, 0.08) 0px, transparent 45%)",
      },
    },
  },
  plugins: [],
};
