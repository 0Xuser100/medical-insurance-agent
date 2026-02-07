import { create } from "zustand";
import { persist } from "zustand/middleware";

interface LanguageState {
  locale: "en" | "ar";
  setLocale: (locale: "en" | "ar") => void;
}

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set) => ({
      locale: "en",
      setLocale: (locale) => set({ locale }),
    }),
    { name: "language-preference" },
  ),
);
