"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { RefreshCw, FileText, Eye, Clock, User, Key } from "lucide-react"
import { format } from "date-fns"
import { apiClient } from "@/lib/api"

interface RequestLog {
  id?: string
  timestamp?: string
  method?: string
  endpoint?: string
  status_code?: number
  response_time_ms?: number
  user_id?: string
  key_id?: string
  tokens_used?: number
  error_message?: string
  request_body?: string
  response_body?: string
}

export function RequestLogs() {
  const [requests, setRequests] = useState<RequestLog[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [selectedRequest, setSelectedRequest] = useState<RequestLog | null>(null)

  const fetchRequests = async () => {
    setLoading(true)
    setError("")
    try {
      const data = await apiClient.getRequests()
      setRequests(Array.isArray(data) ? data : [data].filter(Boolean))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch request logs")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRequests()
  }, [])

  const getStatusBadgeVariant = (statusCode?: number) => {
    if (!statusCode) return "secondary"
    if (statusCode >= 200 && statusCode < 300) return "default"
    if (statusCode >= 400 && statusCode < 500) return "destructive"
    if (statusCode >= 500) return "destructive"
    return "secondary"
  }

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return "—"
    try {
      return format(new Date(timestamp), "MMM dd, HH:mm:ss")
    } catch {
      return timestamp
    }
  }

  const formatResponseTime = (ms?: number) => {
    if (!ms) return "—"
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <FileText className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Request Logs</h2>
            <p className="text-muted-foreground">View recent API requests and responses</p>
          </div>
        </div>
        <Button onClick={fetchRequests} disabled={loading} variant="outline" size="sm">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Recent API Requests</CardTitle>
          <CardDescription>
            {requests.length} request{requests.length !== 1 ? "s" : ""} logged
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>Endpoint</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Response Time</TableHead>
                  <TableHead>User/Key</TableHead>
                  <TableHead>Tokens</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                      {loading ? "Loading request logs..." : "No request logs found"}
                    </TableCell>
                  </TableRow>
                ) : (
                  requests.map((request, index) => (
                    <TableRow key={request.id || index}>
                      <TableCell className="font-mono text-sm">
                        <div className="flex items-center gap-2">
                          <Clock className="h-3 w-3 text-muted-foreground" />
                          {formatTimestamp(request.timestamp)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono">
                          {request.method || "GET"}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm max-w-[200px] truncate">
                        {request.endpoint || "/"}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(request.status_code)}>{request.status_code || 200}</Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {formatResponseTime(request.response_time_ms)}
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          {request.user_id && (
                            <div className="flex items-center gap-1 text-xs">
                              <User className="h-3 w-3" />
                              <span className="font-mono">{request.user_id}</span>
                            </div>
                          )}
                          {request.key_id && (
                            <div className="flex items-center gap-1 text-xs">
                              <Key className="h-3 w-3" />
                              <span className="font-mono">{request.key_id}</span>
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {request.tokens_used ? request.tokens_used.toLocaleString() : "—"}
                      </TableCell>
                      <TableCell>
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="outline" size="sm" onClick={() => setSelectedRequest(request)}>
                              <Eye className="h-3 w-3" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl max-h-[80vh]">
                            <DialogHeader>
                              <DialogTitle>Request Details</DialogTitle>
                              <DialogDescription>Full request and response information</DialogDescription>
                            </DialogHeader>
                            {selectedRequest && (
                              <ScrollArea className="max-h-[60vh]">
                                <div className="space-y-4">
                                  {/* Request Info */}
                                  <div className="grid grid-cols-2 gap-4">
                                    <div>
                                      <h4 className="font-semibold mb-2">Request Info</h4>
                                      <div className="space-y-2 text-sm">
                                        <div>
                                          <span className="font-medium">Method:</span>{" "}
                                          <Badge variant="outline">{selectedRequest.method || "GET"}</Badge>
                                        </div>
                                        <div>
                                          <span className="font-medium">Endpoint:</span>{" "}
                                          <code className="bg-muted px-1 rounded">
                                            {selectedRequest.endpoint || "/"}
                                          </code>
                                        </div>
                                        <div>
                                          <span className="font-medium">Timestamp:</span>{" "}
                                          {formatTimestamp(selectedRequest.timestamp)}
                                        </div>
                                      </div>
                                    </div>
                                    <div>
                                      <h4 className="font-semibold mb-2">Response Info</h4>
                                      <div className="space-y-2 text-sm">
                                        <div>
                                          <span className="font-medium">Status:</span>{" "}
                                          <Badge variant={getStatusBadgeVariant(selectedRequest.status_code)}>
                                            {selectedRequest.status_code || 200}
                                          </Badge>
                                        </div>
                                        <div>
                                          <span className="font-medium">Response Time:</span>{" "}
                                          {formatResponseTime(selectedRequest.response_time_ms)}
                                        </div>
                                        <div>
                                          <span className="font-medium">Tokens Used:</span>{" "}
                                          {selectedRequest.tokens_used?.toLocaleString() || "—"}
                                        </div>
                                      </div>
                                    </div>
                                  </div>

                                  {/* User/Key Info */}
                                  {(selectedRequest.user_id || selectedRequest.key_id) && (
                                    <div>
                                      <h4 className="font-semibold mb-2">Authentication</h4>
                                      <div className="space-y-2 text-sm">
                                        {selectedRequest.user_id && (
                                          <div>
                                            <span className="font-medium">User ID:</span>{" "}
                                            <code className="bg-muted px-1 rounded">{selectedRequest.user_id}</code>
                                          </div>
                                        )}
                                        {selectedRequest.key_id && (
                                          <div>
                                            <span className="font-medium">Key ID:</span>{" "}
                                            <code className="bg-muted px-1 rounded">{selectedRequest.key_id}</code>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  )}

                                  {/* Error Message */}
                                  {selectedRequest.error_message && (
                                    <div>
                                      <h4 className="font-semibold mb-2 text-destructive">Error</h4>
                                      <div className="bg-destructive/10 border border-destructive/20 rounded p-3">
                                        <code className="text-sm">{selectedRequest.error_message}</code>
                                      </div>
                                    </div>
                                  )}

                                  {/* Request Body */}
                                  {selectedRequest.request_body && (
                                    <div>
                                      <h4 className="font-semibold mb-2">Request Body</h4>
                                      <div className="bg-muted rounded p-3">
                                        <pre className="text-sm overflow-x-auto">
                                          {JSON.stringify(JSON.parse(selectedRequest.request_body), null, 2)}
                                        </pre>
                                      </div>
                                    </div>
                                  )}

                                  {/* Response Body */}
                                  {selectedRequest.response_body && (
                                    <div>
                                      <h4 className="font-semibold mb-2">Response Body</h4>
                                      <div className="bg-muted rounded p-3">
                                        <pre className="text-sm overflow-x-auto">
                                          {JSON.stringify(JSON.parse(selectedRequest.response_body), null, 2)}
                                        </pre>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </ScrollArea>
                            )}
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
