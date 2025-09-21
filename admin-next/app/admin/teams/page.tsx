"use client"
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { apiClient } from '@/lib/api'

export default function TeamsPage() {
  const [orgs, setOrgs] = useState<Array<{id:string;name:string}>>([])
  const [teams, setTeams] = useState<Array<{id:string;organization_id:string;name:string}>>([])
  const [orgId, setOrgId] = useState<string>("")
  const [name, setName] = useState<string>("")
  const [error, setError] = useState<string>("")

  const load = async () => {
    try {
      const o = await apiClient.getOrganizations()
      setOrgs(o.items || [])
      const oid = orgId || (o.items?.[0]?.id || '')
      if (oid) {
        const t = await apiClient.getTeams({ organization_id: oid })
        setTeams(t.items || [])
        setOrgId(oid)
      }
    } catch (e:any) {
      setError(e?.message || 'Failed to load')
    }
  }

  useEffect(() => { load() }, [])

  const create = async () => {
    if (!orgId || !name.trim()) return
    try {
      await apiClient.createTeam({ organization_id: orgId, name: name.trim() })
      setName('')
      const t = await apiClient.getTeams({ organization_id: orgId })
      setTeams(t.items || [])
    } catch (e:any) {
      setError(e?.message || 'Failed to create team')
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Teams</CardTitle>
          <CardDescription>Manage organization teams</CardDescription>
        </CardHeader>
        <CardContent>
          {error && <div className="text-red-600 text-sm mb-2">{error}</div>}
          <div className="flex gap-2 items-center mb-4">
            <select className="border rounded px-2 py-1" value={orgId} onChange={async (e)=>{setOrgId(e.target.value); const t = await apiClient.getTeams({ organization_id: e.target.value }); setTeams(t.items || [])}}>
              {orgs.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
            </select>
            <Input placeholder="Team name" value={name} onChange={(e)=>setName(e.target.value)} className="w-[260px]" />
            <Button onClick={create} disabled={!orgId || !name.trim()}>Create</Button>
          </div>
          <ul className="space-y-2">
            {teams.map(t => (
              <li key={t.id} className="flex items-center justify-between border rounded px-3 py-2">
                <div className="font-medium">{t.name}</div>
                <div className="text-xs text-muted-foreground">Org: {t.organization_id}</div>
              </li>
            ))}
            {teams.length === 0 && <li className="text-sm text-muted-foreground">No teams</li>}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

