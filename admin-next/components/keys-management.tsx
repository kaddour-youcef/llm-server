"use client"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { RefreshCw, Plus, Copy, RotateCcw, Trash2, Eye, EyeOff, Key, AlertCircleIcon, CheckCircle2Icon } from "lucide-react"
import { apiClient } from "@/lib/api"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CreateKeyModal } from "./modals/create-key-modal"
import type { ApiKey } from "@/lib/types"
export function KeysManagement() {
  const [keys, setKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [newKey, setNewKey] = useState("")
  const [showNewKey, setShowNewKey] = useState(false)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [total, setTotal] = useState(0)
  const [sortBy, setSortBy] = useState<"created_at" | "name" | "user_id" | "role" | "status">("created_at")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "revoked">("all")
  const [query, setQuery] = useState("")
  const [debouncedQuery, setDebouncedQuery] = useState("")

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query.trim()), 300)
    return () => clearTimeout(t)
  }, [query])

  const fetchKeys = async () => {
    setLoading(true)
    setError("")
    try {
      const data = await apiClient.getKeys({
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_dir: sortDir,
        status: statusFilter === "all" ? undefined : statusFilter,
        q: debouncedQuery || undefined,
      })
      const items = Array.isArray((data as any)?.items) ? (data as any).items : Array.isArray(data) ? data : []
      const totalCount = typeof (data as any)?.total === "number" ? (data as any).total : items.length
      setKeys(items)
      setTotal(totalCount)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch keys")
    } finally {
      setLoading(false)
    }
  }

  const handleCreateSuccess = (res?: { plaintext_key?: string }) => {
    if (res?.plaintext_key) {
      setNewKey(res.plaintext_key)
      setShowNewKey(false) // dont show key right after creation
    }
    setSuccess("API key created successfully")
    fetchKeys()
    setTimeout(() => setSuccess(""), 3000)
  }
  
  

  const revokeKey = async (keyId: string) => {
    try {
      await apiClient.revokeKey(keyId)
      setSuccess("Key revoked successfully")
      fetchKeys()
      setTimeout(() => setSuccess(""), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke key")
    }
  }

  const rotateKey = async (keyId: string) => {
    try {
      const result = await apiClient.rotateKey(keyId)
      setNewKey(result.plaintext_key || "")
      setSuccess("Key rotated successfully")
      fetchKeys()
      setTimeout(() => setSuccess(""), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to rotate key")
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setSuccess("Copied to clipboard")
    setTimeout(() => setSuccess(""), 2000)
  }

  useEffect(() => {
    fetchKeys()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, sortBy, sortDir, statusFilter, debouncedQuery])

  useEffect(() => {
    if (createModalOpen) {
      setNewKey("")
      setShowNewKey(false)
    }
  }, [createModalOpen])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Key className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold tracking-tight">API Keys Management</h2>
            <p className="text-muted-foreground">Manage API keys, quotas, and permissions</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={fetchKeys} disabled={loading} variant="outline" size="sm">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button onClick={() => setCreateModalOpen(true)} size="sm">
            <Plus className="h-4 w-4" />
            Create Key
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        <div className="w-full sm:w-auto">
          <Input
            placeholder="Search keys by name, last4, role, or user id..."
            value={query}
            onChange={(e) => { setQuery(e.target.value); setPage(1) }}
            className="h-9 w-full sm:w-[360px]"
          />
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span>Status</span>
          <Select value={statusFilter} onValueChange={(v: any) => { setStatusFilter(v); setPage(1) }}>
            <SelectTrigger className="h-8 w-[130px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="revoked">Revoked</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span>Sort by</span>
          <Select value={sortBy} onValueChange={(v: any) => { setSortBy(v); setPage(1) }}>
            <SelectTrigger className="h-8 w-[150px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="created_at">Created</SelectItem>
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="user_id">User ID</SelectItem>
              <SelectItem value="role">Role</SelectItem>
              <SelectItem value="status">Status</SelectItem>
            </SelectContent>
          </Select>
          <Select value={sortDir} onValueChange={(v: any) => { setSortDir(v); setPage(1) }}>
            <SelectTrigger className="h-8 w-[110px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="asc">Asc</SelectItem>
              <SelectItem value="desc">Desc</SelectItem>
            </SelectContent>
          </Select>
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


      {/* New Key Display */}
      {newKey && (
        <Card className="border-green-500">
          <CardHeader>
            <CardTitle className="">New API Key Created</CardTitle>
            <CardDescription>Copy this key now - it will not be shown again</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Input value={newKey} readOnly type={showNewKey ? "text" : "password"} className="font-mono" />
              <Button variant="outline" size="icon" onClick={() => setShowNewKey(!showNewKey)}>
                {showNewKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
              <Button variant="outline" size="icon" onClick={() => copyToClipboard(newKey)}>
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>All API Keys</CardTitle>
          <CardDescription>
            {keys.length} API key{keys.length !== 1 ? "s" : ""} in the system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>User ID</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Quotas</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {keys.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                      {loading ? "Loading API keys..." : "No API keys found"}
                    </TableCell>
                  </TableRow>
                ) : (
                  keys.map((key) => (
                    <TableRow key={key.id}>
                      <TableCell className="font-medium">{key.name}</TableCell>
                      <TableCell className="font-mono text-sm">{key.user_id}</TableCell>
                      <TableCell>
                        <Badge variant={key.role === "admin" ? "default" : "secondary"}>{key.role}</Badge>
                      </TableCell>
                      <TableCell className="text-sm">
                        <div>Monthly: {key.monthly_quota_tokens || "∞"}</div>
                        <div>Daily: {key.daily_request_quota || "∞"}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={key.status === "active" ? "default" : "destructive"}>
                          {key.status === "active" ? "Active" : "Revoked"}
                        </Badge>
                      </TableCell>

                      <TableCell className="text-sm text-muted-foreground">
                      {key.created_at
                      ? new Date(key.created_at).toLocaleDateString("en-GB") // gives DD/MM/YYYY
                      : "—"}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button variant="outline" size="sm">
                                <RotateCcw className="h-3 w-3" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Rotate API Key</DialogTitle>
                                <DialogDescription>
                                  This will generate a new key and invalidate the old one. Are you sure?
                                </DialogDescription>
                              </DialogHeader>
                              <div className="flex gap-2 justify-end">
                                <Button variant="outline" onClick={() => rotateKey(key.id)}>
                                  Rotate Key
                                </Button>
                              </div>
                            </DialogContent>
                          </Dialog>

                          <Dialog>
                            <DialogTrigger asChild>
                              <Button variant="outline" size="sm">
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Revoke API Key</DialogTitle>
                                <DialogDescription>
                                  This will permanently disable this API key. Are you sure?
                                </DialogDescription>
                              </DialogHeader>
                              <div className="flex gap-2 justify-end">
                                <Button variant="destructive" onClick={() => revokeKey(key.id)}>
                                  Revoke Key
                                </Button>
                              </div>
                            </DialogContent>
                          </Dialog>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-muted-foreground">
              Page {page} of {Math.max(1, Math.ceil(total / pageSize))} · {total} total
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 text-sm">
                <span>Rows per page</span>
                <Select
                  value={String(pageSize)}
                  onValueChange={(v) => {
                    setPageSize(Number(v))
                    setPage(1)
                  }}
                >
                  <SelectTrigger className="h-8 w-[80px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="25">25</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const totalPages = Math.max(1, Math.ceil(total / pageSize))
                    setPage((p) => Math.min(totalPages, p + 1))
                  }}
                  disabled={page >= Math.max(1, Math.ceil(total / pageSize))}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <CreateKeyModal
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onSuccess={handleCreateSuccess}
      />


    </div>
  )
}
