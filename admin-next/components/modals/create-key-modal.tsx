"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Check, ChevronsUpDown } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { apiClient } from "@/lib/api"
import type { User } from "@/lib/types"
import { CreateKeyFormSchema, formatZodError } from "@/lib/validation"

interface CreateKeyModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: (res?: { plaintext_key?: string }) => void
}


export function CreateKeyModal({ open, onOpenChange, onSuccess }: CreateKeyModalProps) {
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState("")
  const [users, setUsers] = useState<User[]>([])
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [userSelectorOpen, setUserSelectorOpen] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    user_id: "",
    role: "user" as "user" | "admin",
    monthlyQuota: "",
    dailyQuota: "",
  })

  useEffect(() => {
    if (open) {
      fetchUsers()
    }
  }, [open])

  const fetchUsers = async () => {
    setLoadingUsers(true)
    try {
      const data = await apiClient.getUsers({ page: 1, page_size: 100 })
      setUsers(data.items)
    } catch (err) {
      console.error("Failed to fetch users:", err)
    } finally {
      setLoadingUsers(false)
    }
  }

  const getSelectedUserText = () => {
    const selectedUser = users.find((user) => user.id === formData.user_id)
    return selectedUser ? `${selectedUser.name} (${selectedUser.email})` : "Select user..."
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // Zod validation
    const parsed = CreateKeyFormSchema.safeParse(formData)
    if (!parsed.success) {
      setError(formatZodError(parsed.error))
      return
    }

    setCreating(true)
    setError("")
    try {
      const res = await apiClient.createKey({
        name: parsed.data.name,
        user_id: parsed.data.user_id,
        role: parsed.data.role,
        monthly_quota_tokens: parsed.data.monthlyQuota,
        daily_request_quota: parsed.data.dailyQuota,
      })
  
      setFormData({
        name: "",
        user_id: "",
        role: "user",
        monthlyQuota: "",
        dailyQuota: "",
      })
  
      onSuccess(res)            // ✅ send the new plaintext_key up
      onOpenChange(false)       // ✅ close the modal right after success
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create API key")
    } finally {
      setCreating(false)
    }
  }
  

  const handleClose = () => {
    setFormData({
      name: "",
      user_id: "",
      role: "user",
      monthlyQuota: "",
      dailyQuota: "",
    })
    setError("")
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New API Key</DialogTitle>
          <DialogDescription>Generate a new API key for a user. Select a user from the list below.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            {/* User selector */}
            <div className="grid gap-2">
              <Label htmlFor="user_id">User *</Label>
              <Popover open={userSelectorOpen} onOpenChange={setUserSelectorOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={userSelectorOpen}
                    className="justify-between bg-transparent"
                    disabled={creating || loadingUsers}
                  >
                    {loadingUsers ? "Loading users..." : getSelectedUserText()}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[400px] p-0">
                  <Command>
                    <CommandInput placeholder="Search users by name or email..." />
                    <CommandList>
                      <CommandEmpty>No users found.</CommandEmpty>
                      <CommandGroup>
                        {users.map((user) => (
                          <CommandItem
                            key={user.id}
                            value={`${user.name} ${user.email}`}
                            onSelect={() => {
                              setFormData({ ...formData, user_id: user.id })
                              setUserSelectorOpen(false)
                            }}
                          >
                            <Check
                              className={cn("mr-2 h-4 w-4", formData.user_id === user.id ? "opacity-100" : "opacity-0")}
                            />
                            <div className="flex flex-col">
                              <span className="font-medium">{user.name}</span>
                              <span className="text-sm text-muted-foreground">{user.email}</span>
                            </div>
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>

            {/* Key name */}
            <div className="grid gap-2">
              <Label htmlFor="name">Key Name *</Label>
              <Input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Enter a descriptive name for this API key"
                disabled={creating}
                required
              />
            </div>

            {/* Role selector */}
            <div className="grid gap-2">
              <Label htmlFor="role">Role</Label>
              <Select
                value={formData.role}
                onValueChange={(value: "user" | "admin") => setFormData({ ...formData, role: value })}
                disabled={creating}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Monthly quota */}
            <div className="grid gap-2">
              <Label htmlFor="monthlyQuota">Monthly Quota (tokens, optional)</Label>
              <Input
                id="monthlyQuota"
                type="number"
                value={formData.monthlyQuota}
                onChange={(e) => setFormData({ ...formData, monthlyQuota: e.target.value })}
                placeholder="Enter monthly token quota"
                disabled={creating}
              />
            </div>

            {/* Daily quota */}
            <div className="grid gap-2">
              <Label htmlFor="dailyQuota">Daily Quota (requests, optional)</Label>
              <Input
                id="dailyQuota"
                type="number"
                value={formData.dailyQuota}
                onChange={(e) => setFormData({ ...formData, dailyQuota: e.target.value })}
                placeholder="Enter daily request quota"
                disabled={creating}
              />
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} disabled={creating}>
              Cancel
            </Button>
            <Button type="submit" disabled={creating}>
              {creating ? "Creating..." : "Create API Key"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
