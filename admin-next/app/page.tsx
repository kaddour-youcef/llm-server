"use client"

import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Key, Shield } from "lucide-react"

export default function LandingPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="grid gap-6 w-full max-w-4xl sm:grid-cols-2">
        <Card className="border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Shield className="h-5 w-5" /> Admin Dashboard</CardTitle>
            <CardDescription>Manage users, API keys, usage and requests</CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Link href="/admin" className="w-full"><Button className="w-full">Go to Admin</Button></Link>
          </CardContent>
        </Card>
        <Card className="border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Key className="h-5 w-5" /> User Portal</CardTitle>
            <CardDescription>Sign in to view your keys and usage</CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Link href="/sign-in" className="w-full sm:w-auto"><Button className="w-full sm:w-auto">Sign In</Button></Link>
            <Link href="/self-register" className="w-full sm:w-auto"><Button variant="outline" className="w-full sm:w-auto">Register</Button></Link>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
