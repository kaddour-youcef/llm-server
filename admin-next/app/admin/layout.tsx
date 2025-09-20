"use client"

import type React from "react"
import { useMemo } from "react"
import { usePathname } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { AppSidebar } from "@/components/sidebar"
import { Breadcrumbs } from "@/components/breadcrumbs"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"

type ActiveSection = "users" | "keys" | "usage" | "requests"

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  const activeSection: ActiveSection = useMemo(() => {
    if (!pathname) return "users"
    if (pathname.startsWith("/admin/keys")) return "keys"
    if (pathname.startsWith("/admin/usage")) return "usage"
    if (pathname.startsWith("/admin/requests")) return "requests"
    return "users" // default and any /admin or /admin/users paths
  }, [pathname])

  return (
    <AuthGuard>
      <SidebarProvider>
        <div className="flex h-screen w-full">
          <AppSidebar />
          <SidebarInset>
            <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
              <SidebarTrigger className="-ml-1" />
              <div className="flex-1">
                <Breadcrumbs activeSection={activeSection} />
              </div>
            </header>
            <div className="flex-1 overflow-auto p-6">{children}</div>
          </SidebarInset>
        </div>
      </SidebarProvider>
    </AuthGuard>
  )
}

