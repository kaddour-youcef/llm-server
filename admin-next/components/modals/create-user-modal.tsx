"use client"

import type React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { apiClient } from "@/lib/api"

interface CreateUserModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

export function CreateUserModal({ open, onOpenChange, onSuccess }: CreateUserModalProps) {
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState("")
  const [formData, setFormData] = useState({ name: "", email: "" })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim()) {
      setError("Name is required")
      return
    }

    setCreating(true)
    setError("")
    try {
      await apiClient.createUser({
        name: formData.name,
        email: formData.email || undefined,
      })
      setFormData({ name: "", email: "" })
      onSuccess()
      onOpenChange(false)
    } catch (err) {
      let message = "Failed to create user"
    
      // If your apiClient throws { response: { data } } like Axios
      if (err?.response?.data) {
        const data = err.response.data
        if (typeof data === "object") {
          message = data.detail || data.error || data.message || message
        }
      }
      // If your apiClient just throws an Error with JSON inside message
      else if (err instanceof Error) {
        try {
          const parsed = JSON.parse(err.message)
          message = parsed.detail || parsed.error || parsed.message || err.message
        } catch {
          message = err.message
        }
      }
    
      setError(message)
    }
     finally {
      setCreating(false)
    }
  }

  const handleClose = () => {
    setFormData({ name: "", email: "" })
    setError("")
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New User</DialogTitle>
          <DialogDescription>Add a new user to the system. Name is required.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Enter user name"
                disabled={creating}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="Enter email (optional)"
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
              {creating ? "Creating..." : "Create User"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
