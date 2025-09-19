"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { LogOut, Users, Key, BarChart3, FileText } from "lucide-react"
import { useAuthStore } from "@/lib/auth-store"
import { UsersManagement } from "./users-management"
import { KeysManagement } from "./keys-management"
import { UsageAnalytics } from "./usage-analytics"
import { RequestLogs } from "./request-logs"
import { ThemeToggle } from "./theme-toggle"
import { cn } from "@/lib/utils"

type ActiveSection = "users" | "keys" | "usage" | "requests"

export function Dashboard() {
  const { logout } = useAuthStore()
  const [activeSection, setActiveSection] = useState<ActiveSection>("users")

  const navigationItems = [
    { id: "users" as const, label: "Users", icon: Users },
    { id: "keys" as const, label: "API Keys", icon: Key },
    { id: "usage" as const, label: "Usage Analytics", icon: BarChart3 },
    { id: "requests" as const, label: "Request Logs", icon: FileText },
  ]

  const renderContent = () => {
    switch (activeSection) {
      case "users":
        return <UsersManagement />
      case "keys":
        return <KeysManagement />
      case "usage":
        return <UsageAnalytics />
      case "requests":
        return <RequestLogs />
      default:
        return <UsersManagement />
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <aside className="w-64 bg-sidebar border-r border-sidebar-border flex flex-col">
        {/* Logo/Header */}
        <div className="p-6 border-b border-sidebar-border">
          <h1 className="text-xl font-bold text-sidebar-foreground">API Management</h1>
          <p className="text-sm text-sidebar-foreground/70">Admin Dashboard</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon
              const isActive = activeSection === item.id
              return (
                <li key={item.id}>
                  <button
                    onClick={() => setActiveSection(item.id)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors",
                      isActive
                        ? "bg-sidebar-primary text-sidebar-primary-foreground"
                        : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </button>
                </li>
              )
            })}
          </ul>
        </nav>

        <div className="p-4 border-t border-sidebar-border">
          <div className="mb-3">
            <ThemeToggle />
          </div>

          <div className="flex items-center gap-3 mb-3">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-sidebar-primary text-sidebar-primary-foreground text-xs">AD</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">Administrator</p>
              <p className="text-xs text-sidebar-foreground/70">System Admin</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={logout}
            className="w-full gap-2 bg-transparent border-sidebar-border text-sidebar-foreground hover:bg-sidebar-accent"
          >
            <LogOut className="h-3 w-3" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6">{renderContent()}</div>
      </main>
    </div>
  )
}
