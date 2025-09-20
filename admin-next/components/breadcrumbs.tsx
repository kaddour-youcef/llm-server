"use client"

import React from "react"
import { ChevronRight, Home } from "lucide-react"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { useBreadcrumbsStore } from "@/lib/breadcrumbs-store"

type ActiveSection = "users" | "keys" | "usage" | "requests"

interface BreadcrumbsProps {
  activeSection: ActiveSection
}

const sectionLabels: Record<ActiveSection, string> = {
  users: "Users Management",
  keys: "API Keys Management",
  usage: "Usage Analytics",
  requests: "Request Logs",
}

export function Breadcrumbs({ activeSection }: BreadcrumbsProps) {
  const extras = useBreadcrumbsStore((s) => s.extras)

  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink href="/admin" className="flex items-center gap-1">
            <Home className="h-3 w-3" />
            Dashboard
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator>
          <ChevronRight className="h-4 w-4" />
        </BreadcrumbSeparator>
        <BreadcrumbItem>
          <BreadcrumbLink href={activeSection === "users" ? "/admin/users" : activeSection === "keys" ? "/admin/keys" : activeSection === "usage" ? "/admin/usage" : "/admin/requests"}>
            {sectionLabels[activeSection]}
          </BreadcrumbLink>
        </BreadcrumbItem>

        {extras?.length
          ? extras.map((item, idx) => (
              <React.Fragment key={idx}>
                <BreadcrumbSeparator>
                  <ChevronRight className="h-4 w-4" />
                </BreadcrumbSeparator>
                <BreadcrumbItem>
                  {item.href ? (
                    <BreadcrumbLink href={item.href}>{item.label}</BreadcrumbLink>
                  ) : (
                    <BreadcrumbPage>{item.label}</BreadcrumbPage>
                  )}
                </BreadcrumbItem>
              </React.Fragment>
            ))
          : null}
      </BreadcrumbList>
    </Breadcrumb>
  )
}
