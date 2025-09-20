"use client"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { RefreshCw, Plus, Users, AlertCircleIcon, CheckCircle2Icon } from "lucide-react"
import { apiClient } from "@/lib/api"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CreateUserModal } from "./modals/create-user-modal"

interface User {
  id: string
  name: string
  email?: string
  created_at?: string
}

export function UsersManagement() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [total, setTotal] = useState(0)

  const fetchUsers = async () => {
    setLoading(true)
    setError("")
    try {
      const data = await apiClient.getUsers({ page, page_size: pageSize })
      const items = Array.isArray((data as any)?.items) ? (data as any).items : Array.isArray(data) ? data : []
      const totalCount = typeof (data as any)?.total === "number" ? (data as any).total : items.length
      setUsers(items)
      setTotal(totalCount)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch users")
    } finally {
      setLoading(false)
    }
  }

  const handleCreateSuccess = () => {
    setSuccess("User created successfully")
    fetchUsers()
    setTimeout(() => setSuccess(""), 3000)
  }

  useEffect(() => {
    fetchUsers()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const canPrev = page > 1
  const canNext = page < totalPages

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Users className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Users Management</h2>
            <p className="text-muted-foreground">Manage system users and their accounts</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={fetchUsers} disabled={loading} variant="outline" size="sm">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button onClick={() => setCreateModalOpen(true)} size="sm">
            <Plus className="h-4 w-4" />
            Add User
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

      <Card>
        <CardHeader>
          <CardTitle>All Users</CardTitle>
          <CardDescription>
            {users.length} user{users.length !== 1 ? "s" : ""} registered in the system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>User ID</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                      {loading ? "Loading users..." : "No users found"}
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.name}</TableCell>
                      <TableCell>{user.email || "—"}</TableCell>
                      <TableCell className="font-mono text-sm">{user.id}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                      {user.created_at
                      ? new Date(user.created_at).toLocaleDateString("en-GB") // gives DD/MM/YYYY
                      : "—"}                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-muted-foreground">
              Page {page} of {totalPages} · {total} total
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
                <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={!canPrev}>
                  Previous
                </Button>
                <Button variant="outline" size="sm" onClick={() => setPage((p) => p + 1)} disabled={!canNext}>
                  Next
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <CreateUserModal open={createModalOpen} onOpenChange={setCreateModalOpen} onSuccess={handleCreateSuccess} />
    </div>
  )
}
