"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Target, Play, Pause, Settings as SettingsIcon } from "lucide-react"

const strategies = [
  {
    id: "binary_complement",
    name: "Binary Complement Arbitrage",
    description: "YES + NO < $1.00 risk-free opportunities",
    enabled: true,
    allocation: 40,
    roi: 12.4,
    trades: 47,
    winRate: 96.1,
  },
  {
    id: "cross_platform",
    name: "Cross-Platform Arbitrage",
    description: "Polymarket vs Kalshi price gaps",
    enabled: true,
    allocation: 30,
    roi: 8.2,
    trades: 23,
    winRate: 91.3,
  },
  {
    id: "multi_outcome",
    name: "Multi-Outcome Bundle",
    description: "All outcomes < $1.00 in multi-choice markets",
    enabled: false,
    allocation: 0,
    roi: 0,
    trades: 0,
    winRate: 0,
  },
]

export function Strategies() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Trading Strategies</h2>
          <p className="text-muted-foreground">Configure and manage your automated trading strategies</p>
        </div>
        <Button>
          <Target className="w-4 h-4 mr-2" />
          Add Strategy
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {strategies.map((strategy) => (
          <Card key={strategy.id}>
            <CardHeader>
              <div className="flex items-start justify-between mb-2">
                <Badge variant={strategy.enabled ? "success" : "outline"}>
                  {strategy.enabled ? "Active" : "Paused"}
                </Badge>
                <Button size="icon" variant="ghost">
                  <SettingsIcon className="w-4 h-4" />
                </Button>
              </div>
              <CardTitle className="text-lg">{strategy.name}</CardTitle>
              <p className="text-sm text-muted-foreground">{strategy.description}</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Allocation</span>
                    <span className="font-medium">{strategy.allocation}%</span>
                  </div>
                  <div className="h-2 bg-bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-accent-green"
                      style={{ width: `${strategy.allocation}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-sm text-muted-foreground">ROI</p>
                    <p className="text-lg font-mono font-bold text-accent-green">
                      {strategy.roi.toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Trades</p>
                    <p className="text-lg font-mono font-bold">{strategy.trades}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Win Rate</p>
                    <p className="text-lg font-mono font-bold">{strategy.winRate.toFixed(1)}%</p>
                  </div>
                </div>

                <Button
                  className="w-full"
                  variant={strategy.enabled ? "outline" : "default"}
                >
                  {strategy.enabled ? (
                    <>
                      <Pause className="w-4 h-4 mr-2" />
                      Pause Strategy
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Activate Strategy
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
