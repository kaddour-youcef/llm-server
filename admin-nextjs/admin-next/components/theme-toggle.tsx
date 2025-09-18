"use client"

import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useThemeStore } from "@/lib/theme-store"

export function ThemeToggle() {
  const { theme, toggleTheme } = useThemeStore()

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={toggleTheme}
      className="bg-transparent border-sidebar-border text-sidebar-foreground hover:bg-sidebar-accent"
    >
      {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
    </Button>
  )
}
