"use client"

import { useState } from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Link from "next/link"
import { useUserAuthStore } from "@/lib/user-auth-store"

export default function SelfRegisterPage() {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const { register, isBusy } = useUserAuthStore()

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    const ok = await register(name, email, password)
    if (ok) {
      setSuccess("Registered. Please wait for admin approval.")
    } else {
      setError("Registration failed. Email may be taken.")
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create your account</CardTitle>
          <CardDescription>Register and wait for admin approval</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-3">
            <div className="grid gap-2">
              <Label htmlFor="name">Full Name</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            {error && (
              <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>
            )}
            {success && (
              <Alert className="border-green-500 text-green-700"><AlertDescription>{success}</AlertDescription></Alert>
            )}
            <Button type="submit" className="w-full" disabled={isBusy}>Register</Button>
          </form>
          <p className="text-sm text-muted-foreground mt-3">Already registered? <Link href="/sign-in" className="text-primary">Sign in</Link></p>
        </CardContent>
      </Card>
    </div>
  )
}

