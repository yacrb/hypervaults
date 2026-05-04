import type { Config } from "tailwindcss";

const config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        vault: "#0f766e",
        cloud: "#f6f8fb"
      },
      boxShadow: {
        soft: "0 18px 60px rgba(23, 32, 51, 0.08)"
      }
    }
  }
} satisfies Config;

export default config;
