export const colors = {
  primary: "#059669",
  primaryDark: "#047857",
  primaryLight: "#d1fae5",
  bg: "#f0fdf4",
  card: "#ffffff",
  text: "#064e3b",
  textMuted: "#6b7280",
  border: "#d1d5db",
  danger: "#dc2626",
  warning: "#d97706",
  white: "#ffffff",
};

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
};

export const gradients = {
  primary: ["#059669", "#047857"] as const,
  hero: ["#065f46", "#047857", "#059669"] as const,
  accent: ["#34d399", "#059669"] as const,
  soft: ["#d1fae5", "#a7f3d0"] as const,
  dark: ["#064e3b", "#065f46"] as const,
};

export const shadow = {
  shadowColor: "#047857",
  shadowOffset: { width: 0, height: 6 },
  shadowOpacity: 0.16,
  shadowRadius: 14,
  elevation: 4,
};

export const glow = {
  shadowColor: "#047857",
  shadowOffset: { width: 0, height: 8 },
  shadowOpacity: 0.35,
  shadowRadius: 18,
  elevation: 8,
};

export const glass = {
  bg: "rgba(255,255,255,0.45)",
  overlay: "rgba(255,255,255,0.3)",
  border: "rgba(255,255,255,0.85)",
  darkBg: "rgba(4,120,87,0.82)",
  darkBorder: "rgba(255,255,255,0.25)",
  tintBg: "rgba(255,255,255,0.55)",
  chipBg: "rgba(255,255,255,0.6)",
};
