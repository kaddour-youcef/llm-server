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
      className="
        w-full 
        bg-transparent 
        border-sidebar-border 
        text-sidebar-foreground 
        hover:bg-sidebar-accent
        group-data-[collapsible=icon]:w-auto 
        group-data-[collapsible=icon]:px-2
      "
    >
      {theme === "light" ? (
        <Moon className="h-4 w-4" />
      ) : (
        <Sun className="h-4 w-4" />
      )}
      {/* Hide text when collapsed */}
      <span className="ml-2 group-data-[collapsible=icon]:hidden">
        {theme === "light" ? "Dark Mode" : "Light Mode"}
      </span>
    </Button>
  )
}
