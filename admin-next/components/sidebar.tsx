"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { LogOut, Users, Key, BarChart3, FileText } from "lucide-react"
import { useAuthStore } from "@/lib/auth-store"
import { ThemeToggle } from "./theme-toggle"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function AppSidebar() {
  const { logout } = useAuthStore()
  const pathname = usePathname()

  const navigationItems = [
    { href: "/admin/users", label: "Users", icon: Users },
    { href: "/admin/keys", label: "API Keys", icon: Key },
    { href: "/admin/organizations", label: "Organizations", icon: BarChart3 },
    { href: "/admin/teams", label: "Teams", icon: Users },
    { href: "/admin/usage", label: "Usage Analytics", icon: BarChart3 },
    { href: "/admin/requests", label: "Request Logs", icon: FileText },
  ]

  return (
    <Sidebar variant="sidebar" collapsible="icon">
      <SidebarHeader>
        <div className="flex flex-col gap-2 px-2 py-2">
          <h1 className="text-lg font-bold group-data-[collapsible=icon]:hidden">API Management</h1>
          <p className="text-sm text-muted-foreground group-data-[collapsible=icon]:hidden">Admin Dashboard</p>
          {/* Show only icon when collapsed */}
          <div className="hidden group-data-[collapsible=icon]:flex items-center justify-center">
            <div className="h-8 w-8 rounded bg-primary/10 flex items-center justify-center">
              <span className="text-sm font-bold text-primary">AM</span>
            </div>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigationItems.map((item) => {
                const Icon = item.icon
                const isActive = pathname?.startsWith(item.href)
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton asChild isActive={!!isActive} tooltip={item.label}>
                      <Link href={item.href}>
                        <Icon className="h-4 w-4" />
                        <span>{item.label}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div className="flex flex-col gap-2 p-2">
          <div className="group-data-[collapsible=icon]:flex group-data-[collapsible=icon]:justify-center">
            <ThemeToggle />
          </div>

          <div className="flex items-center gap-3 p-2 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:p-1">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="text-xs">AD</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0 group-data-[collapsible=icon]:hidden">
              <p className="text-sm font-medium truncate">Administrator</p>
              <p className="text-xs text-muted-foreground">System Admin</p>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={logout}
            className="w-full gap-2 bg-transparent group-data-[collapsible=icon]:w-auto group-data-[collapsible=icon]:px-2"
            title="Logout"
          >
            <LogOut className="h-3 w-3" />
            <span className="group-data-[collapsible=icon]:hidden">Logout</span>
          </Button>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
