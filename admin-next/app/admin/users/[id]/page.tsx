"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ArrowLeft, RefreshCw, RotateCcw, Trash2, Key as KeyIcon, CheckCircle2Icon, AlertCircleIcon } from "lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import type { ApiKey, UserDetail } from "@/lib/types"
import { CreateKeyInlineFormSchema, UpdateUserFormSchema, formatZodError } from "@/lib/validation"
import { useBreadcrumbsStore } from "@/lib/breadcrumbs-store"

export default function UserDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const userId = params?.id

  const [user, setUser] = useState<UserDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const [editName, setEditName] = useState("")
  const [editEmail, setEditEmail] = useState("")
  const [status, setStatus] = useState<"pending" | "approved" | "disabled">("approved")

  const [creatingKey, setCreatingKey] = useState(false)
  const [newKeyName, setNewKeyName] = useState("")
  const [newKeyRole, setNewKeyRole] = useState<"user" | "admin">("user")
  const [newMonthlyQuota, setNewMonthlyQuota] = useState("")
  const [newDailyQuota, setNewDailyQuota] = useState("")
  const [newPlaintextKey, setNewPlaintextKey] = useState<string | null>(null)
  const [newUnlimited, setNewUnlimited] = useState(true)
  const [newExpiresAt, setNewExpiresAt] = useState("")
  const { setExtras, clear } = useBreadcrumbsStore()

  const fetchUser = async () => {
    if (!userId) return
    setLoading(true)
    setError("")
    try {
      const data = await apiClient.getUser(userId)
      setUser(data)
      setEditName(data.name || "")
      setEditEmail(data.email || "")
      setStatus(((data as any).status as any) || "approved")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch user")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUser()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId])

  // Update breadcrumbs with user details
  useEffect(() => {
    const label = user?.name || user?.email || (userId as string) || "User"
    setExtras([{ label }])
    return () => clear()
  }, [user?.name, user?.email, userId, setExtras, clear])

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userId) return
    setError("")
    try {
      const parsed = UpdateUserFormSchema.safeParse({ name: editName, email: editEmail })
      if (!parsed.success) {
        setError(formatZodError(parsed.error))
        return
      }
      await apiClient.updateUser(userId, { ...parsed.data, status })
      setSuccess("User updated successfully")
      fetchUser()
      setTimeout(() => setSuccess(""), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user")
    }
  }

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userId || !newKeyName.trim()) return
    setCreatingKey(true)
    setError("")
    setNewPlaintextKey(null)
    try {
      const parsed = CreateKeyInlineFormSchema.safeParse({
        name: newKeyName,
        role: newKeyRole,
        monthlyQuota: newMonthlyQuota,
        dailyQuota: newDailyQuota,
        unlimited: newUnlimited,
        expiresAt: newExpiresAt,
      })
      if (!parsed.success) {
        setError(formatZodError(parsed.error))
        return
      }
      const res = await apiClient.createKey({
        user_id: userId,
        name: parsed.data.name,
        role: parsed.data.role,
        monthly_quota_tokens: parsed.data.monthlyQuota,
        daily_request_quota: parsed.data.dailyQuota,
        expires_at: parsed.data.unlimited ? undefined : parsed.data.expiresAt,
      })
      setSuccess("API key created successfully")
      setNewPlaintextKey(res.plaintext_key ?? null)
      setNewKeyName("")
      setNewMonthlyQuota("")
      setNewDailyQuota("")
      fetchUser()
      setTimeout(() => setSuccess("") , 4000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create API key")
    } finally {
      setCreatingKey(false)
    }
  }

  const handleRotate = async (keyId: string) => {
    try {
      const res = await apiClient.rotateKey(keyId)
      setSuccess("Key rotated. Copy the new plaintext now.")
      setNewPlaintextKey(res.plaintext_key ?? null)
      fetchUser()
      setTimeout(() => setSuccess(""), 4000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to rotate key")
    }
  }

  const handleRevoke = async (keyId: string) => {
    try {
      await apiClient.revokeKey(keyId)
      setSuccess("Key revoked successfully")
      fetchUser()
      setTimeout(() => setSuccess(""), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke key")
    }
  }

  return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button variant="ghost" onClick={() => router.push("/admin/users")}
              className="p-2" aria-label="Back to dashboard">
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="p-2 bg-primary/10 rounded-lg">
              <KeyIcon className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h2 className="text-2xl font-bold tracking-tight">User Details</h2>
              {user && (
                <p className="text-muted-foreground">
                  <span className="font-mono">{user.id}</span>
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={fetchUser} disabled={loading} variant="outline" size="sm">
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {(error || success) && (
          <Alert
            variant={error ? "destructive" : "default"}
            className={error ? "" : "border-green-500 text-green-700 [&_svg]:text-green-600"}
          >
            {error ? <AlertCircleIcon className="h-4 w-4" /> : <CheckCircle2Icon className="h-4 w-4" />}
            <AlertDescription>{error || success}</AlertDescription>
          </Alert>
        )}

        {/* Edit user info */}
        <Card>
          <CardHeader>
            <CardTitle>Edit User</CardTitle>
            <CardDescription>Update basic user information.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUpdate} className="grid gap-4 max-w-xl">
              <div className="grid gap-2">
                <Label htmlFor="name">Name</Label>
                <Input id="name" value={editName} onChange={(e) => setEditName(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="status">Status</Label>
                <Select value={status} onValueChange={(v: any) => setStatus(v)}>
                  <SelectTrigger className="w-[200px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">pending</SelectItem>
                    <SelectItem value="approved">approved</SelectItem>
                    <SelectItem value="disabled">disabled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2">
                <Button type="submit">Save Changes</Button>
                {user?.email && (
                  <span className="self-center text-sm text-muted-foreground">Last updated: {user?.created_at ? new Date(user.created_at).toLocaleString() : "—"}</span>
                )}
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Keys list and actions */}
        <Card>
          <CardHeader>
            <CardTitle>API Keys</CardTitle>
            <CardDescription>Keys associated with this user.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Last4</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Expires</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {user?.keys?.length ? (
                    user.keys.map((k) => (
                      <TableRow key={k.id}>
                        <TableCell className="font-medium">{k.name}</TableCell>
                        <TableCell className="font-mono">{k.last4}</TableCell>
                        <TableCell>{k.role}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span>{k.status}</span>
                            {k.status === 'active' && k.expires_at && new Date(k.expires_at as any).getTime() < Date.now() ? (
                              <span className="inline-flex items-center rounded-md bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                                Expired
                              </span>
                            ) : null}
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          {k.expires_at ? (
                            (() => {
                              const exp = new Date(k.expires_at as any)
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
                        <TableCell className="text-sm text-muted-foreground">{k.created_at ? new Date(k.created_at).toLocaleDateString("en-GB") : "—"}</TableCell>
                        <TableCell className="flex gap-2">
                          {k.status === 'active' ? (
                            <>
                              {/* Rotate when expired */}
                              {k.expires_at && new Date(k.expires_at as any).getTime() < Date.now() && (
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className=""
                                      onClick={() => handleRotate(k.id)}
                                    >
                                      <RotateCcw className="h-4 w-4" /> Rotate
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent sideOffset={6}>Rotate key</TooltipContent>
                                </Tooltip>
                              )}
                              {/* Revoke always shown for active */}
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button size="sm" variant="destructive" onClick={() => handleRevoke(k.id)}>
                                    <Trash2 className="h-4 w-4" /> Revoke
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent sideOffset={6}>Revoke key</TooltipContent>
                              </Tooltip>
                            </>
                          ) : null}
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground py-8">No keys found</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Inline create key */}
            <div className="mt-6">
              <h3 className="font-semibold mb-2">Create New Key</h3>
              <form onSubmit={handleCreateKey} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="grid gap-2">
                  <Label htmlFor="newKeyName">Key Name</Label>
                  <Input id="newKeyName" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} required />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="newKeyRole">Role</Label>
                  <Select value={newKeyRole} onValueChange={(v: "user" | "admin") => setNewKeyRole(v)}>
                    <SelectTrigger id="newKeyRole"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="user">User</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="monthlyQuota">Monthly Tokens (optional)</Label>
                  <Input id="monthlyQuota" type="number" value={newMonthlyQuota} onChange={(e) => setNewMonthlyQuota(e.target.value)} />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="dailyQuota">Daily Requests (optional)</Label>
                  <Input id="dailyQuota" type="number" value={newDailyQuota} onChange={(e) => setNewDailyQuota(e.target.value)} />
                </div>
                <div className="grid gap-2">
                  <Label>Expiration</Label>
                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={newUnlimited} onChange={(e) => setNewUnlimited(e.target.checked)} />
                      Unlimited
                    </label>
                    {!newUnlimited && (
                      <Input type="date" value={newExpiresAt} onChange={(e) => setNewExpiresAt(e.target.value)} />
                    )}
                  </div>
                </div>
                <div className="sm:col-span-2 lg:col-span-4 flex gap-2 mt-2">
                  <Button type="submit" disabled={creatingKey}>{creatingKey ? "Creating..." : "Create Key"}</Button>
                  {newPlaintextKey && (
                    <div className="text-sm">
                      <span className="font-medium">Plaintext key:</span> <span className="font-mono break-all">{newPlaintextKey}</span>
                    </div>
                  )}
                </div>
              </form>
            </div>
          </CardContent>
        </Card>
      </div>
  )
}
