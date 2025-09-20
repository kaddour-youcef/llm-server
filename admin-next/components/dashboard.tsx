"use client"

import { useState } from "react"
import { AppSidebar } from "./sidebar"
import { Breadcrumbs } from "./breadcrumbs"
import { UsersManagement } from "./users-management"
import { KeysManagement } from "./keys-management"
import { UsageAnalytics } from "./usage-analytics"
import { RequestLogs } from "./request-logs"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"

type ActiveSection = "users" | "keys" | "usage" | "requests"

export function Dashboard() {
  const [activeSection, setActiveSection] = useState<ActiveSection>("users")

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
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <AppSidebar activeSection={activeSection} onSectionChange={setActiveSection} />

        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
            <SidebarTrigger className="-ml-1" />
            <div className="flex-1">
              <Breadcrumbs activeSection={activeSection} />
            </div>
          </header>
          <div className="flex-1 overflow-auto p-6">{renderContent()}</div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}
