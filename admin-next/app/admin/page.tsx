"use client"

import { AuthGuard } from "@/components/auth-guard"
import { Dashboard } from "@/components/dashboard"

export default function AdminHomePage() {
  return (
    <AuthGuard>
      <Dashboard />
    </AuthGuard>
  )
}

