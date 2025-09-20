"use client"

import { useEffect, useMemo, useState } from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useUserAuthStore } from "@/lib/user-auth-store"
import { apiClient } from "@/lib/api"
import { useRouter } from "next/navigation"

export default function UserPortalPage() {
  const { accessToken, refreshToken, isAuthenticated, refresh, logout } = useUserAuthStore()
  const [keys, setKeys] = useState<any[]>([])
  const [usage, setUsage] = useState<Record<string, { request_count: number; total_tokens: number }>>({})
  const [error, setError] = useState("")
  const router = useRouter()

  const load = async () => {
    setError("")
    try {
      if (!accessToken) throw new Error("Not authenticated")
      const [kres, ures] = await Promise.all([
        apiClient.userKeys(accessToken),
        apiClient.userUsage(accessToken),
      ])
      setKeys(kres.items || [])
      const umap: Record<string, { request_count: number; total_tokens: number }> = {}
      for (const u of ures.items || []) umap[u.key_id] = { request_count: u.request_count, total_tokens: u.total_tokens }
      setUsage(umap)
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      if (msg.includes("401") && refreshToken) {
        const ok = await refresh()
        if (ok) return load()
      }
      setError(msg)
    }
  }

  useEffect(() => {
    if (!isAuthenticated) router.push("/sign-in")
  }, [isAuthenticated, router])

  useEffect(() => {
    if (accessToken) load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken])

  const rows = useMemo(() => {
    return (keys || []).map((k) => ({
      ...k,
      usage: usage[k.id] || { request_count: 0, total_tokens: 0 },
    }))
  }, [keys, usage])

  return (
    <div className="min-h-screen p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Your API Keys</h1>
          <p className="text-muted-foreground">View keys and recent usage (30 days)</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={load}>Refresh</Button>
          <Button variant="secondary" onClick={refresh}>Refresh Token</Button>
          <Button variant="destructive" onClick={logout}>Logout</Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Keys</CardTitle>
          <CardDescription>Contact an admin to create or rotate keys.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Last4</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Expires</TableHead>
                  <TableHead>Requests (30d)</TableHead>
                  <TableHead>Tokens (30d)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.length ? rows.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.name}</TableCell>
                    <TableCell className="font-mono">{r.last4}</TableCell>
                    <TableCell>{r.status}</TableCell>
                    <TableCell className="text-sm">
                      {r.expires_at ? (
                        (() => {
                          const exp = new Date(r.expires_at as any)
                          const now = new Date()
                          const isExpired = exp.getTime() < now.getTime()
                          return (
                            <span className={isExpired ? "text-red-600" : ""}>
                              {exp.toLocaleDateString("en-GB")}
                              {isExpired ? " (expired)" : ""}
                            </span>
                          )
                        })()
                      ) : (
                        <span className="text-muted-foreground">Unlimited</span>
                      )}
                    </TableCell>
                    <TableCell>{r.usage.request_count}</TableCell>
                    <TableCell>{r.usage.total_tokens}</TableCell>
                  </TableRow>
                )) : (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground py-10">No keys</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
