"use client"
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { apiClient } from '@/lib/api'

export default function OrganizationsPage() {
  const [items, setItems] = useState<Array<{id:string;name:string;status?:string;monthly_token_quota?:number|null}>>([])
  const [loading, setLoading] = useState(false)
  const [name, setName] = useState("")
  const [quota, setQuota] = useState("")
  const [error, setError] = useState("")

  const load = async () => {
    setLoading(true)
    setError("")
    try {
      const res = await apiClient.getOrganizations()
      setItems(res.items || [])
    } catch (e:any) {
      setError(e?.message || 'Failed to load organizations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const create = async () => {
    if (!name.trim()) return
    try {
      await apiClient.createOrganization({ name: name.trim(), monthly_token_quota: quota ? Number(quota) : undefined })
      setName(''); setQuota(''); load()
    } catch (e:any) {
      setError(e?.message || 'Failed to create organization')
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Organizations</CardTitle>
          <CardDescription>Manage organizations and quotas</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 items-center mb-4">
            <Input placeholder="Organization name" value={name} onChange={(e)=>setName(e.target.value)} className="w-[260px]" />
            <Input placeholder="Monthly token quota (optional)" type="number" value={quota} onChange={(e)=>setQuota(e.target.value)} className="w-[260px]" />
            <Button onClick={create} disabled={loading || !name.trim()}>Create</Button>
          </div>
          {error && <div className="text-red-600 text-sm mb-2">{error}</div>}
          <ul className="space-y-2">
            {loading ? <li>Loading...</li> : items.map((o)=> (
              <li key={o.id} className="flex items-center justify-between border rounded px-3 py-2">
                <div>
                  <div className="font-medium">{o.name}</div>
                  <div className="text-sm text-muted-foreground">Quota: {o.monthly_token_quota ?? '—'}</div>
                </div>
                <div className="text-xs uppercase tracking-wide text-muted-foreground">{o.status}</div>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

