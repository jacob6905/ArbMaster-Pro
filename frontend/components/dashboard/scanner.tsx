"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Search, Filter, Play, Pause } from "lucide-react"

export function Scanner() {
  return (
    <div className="space-y-6">
      {/* Scanner Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5" />
              Opportunity Scanner
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="success" className="animate-pulse-green">
                Active
              </Badge>
              <Button size="sm" variant="outline">
                <Pause className="w-4 h-4 mr-2" />
                Pause
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="text-sm text-muted-foreground mb-1 block">Platform</label>
              <select className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm">
                <option>All Platforms</option>
                <option>Polymarket</option>
                <option>Kalshi</option>
                <option>CEX</option>
                <option>DEX</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="text-sm text-muted-foreground mb-1 block">Strategy Type</label>
              <select className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm">
                <option>All Types</option>
                <option>Binary Complement</option>
                <option>Cross-Platform</option>
                <option>Multi-Outcome</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="text-sm text-muted-foreground mb-1 block">Min Profit %</label>
              <input
                type="number"
                step="0.1"
                defaultValue="1.0"
                className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div className="flex-1">
              <label className="text-sm text-muted-foreground mb-1 block">Min Liquidity</label>
              <input
                type="number"
                step="1000"
                defaultValue="10000"
                className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Opportunities List */}
      <Card>
        <CardHeader>
          <CardTitle>Live Opportunities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-muted-foreground">
            <Search className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p className="text-lg">Scanning for opportunities...</p>
            <p className="text-sm mt-2">No arbitrage opportunities detected at the moment</p>
            <p className="text-xs mt-1">Last scan: 0.3s ago • Latency: 127ms</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
