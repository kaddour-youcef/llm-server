"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { CalendarIcon, BarChart3, Activity, Zap } from "lucide-react"
import { format, subDays } from "date-fns"
import { apiClient } from "@/lib/api"
import type { UsageData } from "@/lib/types"

export function UsageAnalytics() {
  const [usageData, setUsageData] = useState<UsageData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [filters, setFilters] = useState({
    from: format(subDays(new Date(), 30), "yyyy-MM-dd"),
    to: format(new Date(), "yyyy-MM-dd"),
    key_id: "",
  })

  const fetchUsage = async () => {
    setLoading(true)
    setError("")
    try {
      const params: { from: string; to: string; key_id?: string } = {
        from: filters.from,
        to: filters.to,
      }
      if (filters.key_id.trim()) {
        params.key_id = filters.key_id.trim()
      }

      const data = await apiClient.getUsage(params)
      setUsageData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch usage data")
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    fetchUsage()
  }

  useEffect(() => {
    fetchUsage()
  }, [])

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <BarChart3 className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Usage Analytics</h2>
          <p className="text-muted-foreground">Monitor token usage and request patterns</p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarIcon className="h-5 w-5" />
            Date Range & Filters
          </CardTitle>
          <CardDescription>Filter usage data by date range and API key</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-wrap gap-4 items-end">
            <div className="space-y-2">
              <Label htmlFor="from">From Date</Label>
              <Input
                id="from"
                type="date"
                value={filters.from}
                onChange={(e) => setFilters({ ...filters, from: e.target.value })}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="to">To Date</Label>
              <Input
                id="to"
                type="date"
                value={filters.to}
                onChange={(e) => setFilters({ ...filters, to: e.target.value })}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="key_id">Key ID (Optional)</Label>
              <Input
                id="key_id"
                value={filters.key_id}
                onChange={(e) => setFilters({ ...filters, key_id: e.target.value })}
                placeholder="Filter by specific key"
                disabled={loading}
              />
            </div>

            <Button type="submit" disabled={loading}>
              {loading ? "Loading..." : "Apply Filters"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {usageData && (
        <>
          {/* Metrics Cards */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatNumber(usageData.totals.total_tokens)}</div>
                <p className="text-xs text-muted-foreground">Tokens consumed in selected period</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatNumber(usageData.totals.request_count)}</div>
                <p className="text-xs text-muted-foreground">API requests made in selected period</p>
              </CardContent>
            </Card>
          </div>

          {/* Usage Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Token Usage Over Time
              </CardTitle>
              <CardDescription>Daily token consumption trends</CardDescription>
            </CardHeader>
            <CardContent>
              {usageData.timeseries && usageData.timeseries.length > 0 ? (
                <div className="h-[400px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={usageData.timeseries}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" tickFormatter={(value) => format(new Date(value), "MMM dd")} />
                      <YAxis tickFormatter={formatNumber} />
                      <Tooltip
                        labelFormatter={(value) => format(new Date(value as string), "MMM dd, yyyy")}
                        formatter={(value: number, name: string) => [
                          formatNumber(value),
                          name === "total_tokens" ? "Tokens" : "Requests",
                        ]}
                      />
                      <Line
                        type="monotone"
                        dataKey="total_tokens"
                        stroke="hsl(var(--primary))"
                        strokeWidth={2}
                        dot={{ fill: "hsl(var(--primary))" }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                  No usage data available for the selected period
                </div>
              )}
            </CardContent>
          </Card>

          {/* Request Count Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Request Count Over Time
              </CardTitle>
              <CardDescription>Daily API request volume</CardDescription>
            </CardHeader>
            <CardContent>
              {usageData.timeseries && usageData.timeseries.length > 0 ? (
                <div className="h-[300px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={usageData.timeseries}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" tickFormatter={(value) => format(new Date(value), "MMM dd")} />
                      <YAxis tickFormatter={formatNumber} />
                      <Tooltip
                        labelFormatter={(value) => format(new Date(value as string), "MMM dd, yyyy")}
                        formatter={(value: number) => [formatNumber(value), "Requests"]}
                      />
                      <Line
                        type="monotone"
                        dataKey="request_count"
                        stroke="hsl(var(--chart-2))"
                        strokeWidth={2}
                        dot={{ fill: "hsl(var(--chart-2))" }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                  No request data available for the selected period
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
