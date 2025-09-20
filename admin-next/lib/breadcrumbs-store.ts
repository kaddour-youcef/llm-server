import { create } from "zustand"

export type BreadcrumbExtra = { label: string; href?: string }

type BreadcrumbsState = {
  extras: BreadcrumbExtra[]
  setExtras: (items: BreadcrumbExtra[]) => void
  clear: () => void
}

export const useBreadcrumbsStore = create<BreadcrumbsState>((set) => ({
  extras: [],
  setExtras: (items) => set({ extras: items }),
  clear: () => set({ extras: [] }),
}))

