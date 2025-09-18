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
import { RefreshCw, Plus, Copy, RotateCcw, Trash2, Eye, EyeOff, Key } from "lucide-react"
import { apiClient } from "@/lib/api"
import { CreateKeyModal } from "./modals/create-key-modal"

interface ApiKey {
  id: string
  name: string
  user_id: string
  role: string
  monthly_quota_tokens?: number | null
  daily_request_quota?: number | null
  created_at?: string
  is_active?: boolean
}

interface User {
  id: string
  name: string
  email?: string
}

export function KeysManagement() {
  const [keys, setKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [newKey, setNewKey] = useState("")
  const [showNewKey, setShowNewKey] = useState(false)
  const [createModalOpen, setCreateModalOpen] = useState(false)

  const fetchKeys = async () => {
    setLoading(true)
    setError("")
    try {
      const data = await apiClient.getKeys()
      setKeys(Array.isArray(data) ? data : [data].filter(Boolean))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch keys")
    } finally {
      setLoading(false)
    }
  }

  const handleCreateSuccess = () => {
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
  }, [])

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

      {(error || success) && (
        <Alert variant={error ? "destructive" : "default"}>
          <AlertDescription>{error || success}</AlertDescription>
        </Alert>
      )}

      {/* New Key Display */}
      {newKey && (
        <Card className="border-accent/20 bg-accent/5">
          <CardHeader>
            <CardTitle className="text-accent">New API Key Created</CardTitle>
            <CardDescription>Copy this key now - it won't be shown again</CardDescription>
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
                        <Badge variant={key.is_active !== false ? "default" : "destructive"}>
                          {key.is_active !== false ? "Active" : "Revoked"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {key.created_at ? new Date(key.created_at).toLocaleDateString() : "—"}
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
        </CardContent>
      </Card>

      <CreateKeyModal open={createModalOpen} onOpenChange={setCreateModalOpen} onSuccess={handleCreateSuccess} />
    </div>
  )
}
