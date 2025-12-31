"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { formatCurrency, formatPercent } from "@/lib/utils"
import { TrendingUp, TrendingDown, Activity, DollarSign, Target, Zap } from "lucide-react"
import type { PerformanceMetrics, ArbitrageOpportunity, Trade } from "@/types"

export function DashboardOverview() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    totalPnL: 2847.32,
    dailyPnL: 127.50,
    weeklyPnL: 634.80,
    monthlyPnL: 2847.32,
    winRate: 87.3,
    totalTrades: 147,
    activePositions: 12,
    activeCapital: 15000,
    dailyROI: 3.2,
  })

  const [opportunities, setOpportunities] = useState<ArbitrageOpportunity[]>([])
  const [recentTrades, setRecentTrades] = useState<Trade[]>([])

  // TODO: Connect to WebSocket for real-time updates
  useEffect(() => {
    // Fetch initial data
    // WebSocket connection will be implemented when backend is ready
  }, [])

  return (
    <div className="space-y-6">
      {/* Performance Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Daily P&L */}
        <MetricCard
          title="Daily P&L"
          value={formatCurrency(metrics.dailyPnL)}
          change={formatPercent(12.3)}
          positive={metrics.dailyPnL > 0}
          icon={DollarSign}
        />

        {/* Win Rate */}
        <MetricCard
          title="Win Rate"
          value={`${metrics.winRate.toFixed(1)}%`}
          change={`${metrics.totalTrades} trades`}
          positive={metrics.winRate > 85}
          icon={Target}
        />

        {/* Active Positions */}
        <MetricCard
          title="Active Positions"
          value={metrics.activePositions.toString()}
          change={formatCurrency(metrics.activeCapital)}
          positive={true}
          icon={Activity}
        />

        {/* Daily ROI */}
        <MetricCard
          title="Daily ROI"
          value={`${metrics.dailyROI.toFixed(1)}%`}
          change={formatPercent(0.4)}
          positive={metrics.dailyROI > 0}
          icon={TrendingUp}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Opportunities - 2/3 width */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-accent-green" />
                Live Opportunities
              </CardTitle>
              <Badge variant="success" className="animate-pulse-green">
                Scanning
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {opportunities.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Zap className="w-12 h-12 mx-auto mb-3 opacity-20" />
                  <p>Scanning for arbitrage opportunities...</p>
                  <p className="text-sm mt-1">No opportunities detected at the moment</p>
                </div>
              ) : (
                opportunities.map((opp) => (
                  <OpportunityCard key={opp.id} opportunity={opp} />
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Live Activity - 1/3 width */}
        <Card>
          <CardHeader>
            <CardTitle>Live Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentTrades.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Activity className="w-12 h-12 mx-auto mb-3 opacity-20" />
                  <p className="text-sm">No recent trades</p>
                </div>
              ) : (
                recentTrades.map((trade) => (
                  <TradeCard key={trade.id} trade={trade} />
                ))
              )}

              {/* Sample placeholder trades */}
              <div className="flex items-center gap-3 p-3 bg-bg-secondary rounded-lg">
                <div className="px-2 py-1 bg-accent-green/10 text-accent-green rounded text-xs font-medium">
                  BUY
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Bitcoin &gt; $100k</p>
                  <p className="text-xs text-muted-foreground">Binary Complement</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-mono text-accent-green">+$12.50</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-bg-secondary rounded-lg">
                <div className="px-2 py-1 bg-accent-green/10 text-accent-green rounded text-xs font-medium">
                  ARB
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Poly/Kalshi Spread</p>
                  <p className="text-xs text-muted-foreground">Cross-Platform</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-mono text-accent-green">+$42.00</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Platform Status */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <PlatformStatus name="Polymarket" status="online" />
            <PlatformStatus name="Kalshi" status="online" />
            <PlatformStatus name="Binance" status="offline" />
            <PlatformStatus name="Uniswap" status="online" />
            <PlatformStatus name="Aave" status="online" />
            <PlatformStatus name="SushiSwap" status="offline" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

interface MetricCardProps {
  title: string
  value: string
  change: string
  positive: boolean
  icon: React.ElementType
}

function MetricCard({ title, value, change, positive, icon: Icon }: MetricCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-muted-foreground mb-1">{title}</p>
            <p className="text-2xl font-bold font-mono">{value}</p>
            <div className="flex items-center gap-1 mt-2">
              {positive ? (
                <TrendingUp className="w-3 h-3 text-accent-green" />
              ) : (
                <TrendingDown className="w-3 h-3 text-accent-red" />
              )}
              <span className={`text-xs ${positive ? 'text-accent-green' : 'text-accent-red'}`}>
                {change}
              </span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-accent-green/10 flex items-center justify-center">
            <Icon className="w-5 h-5 text-accent-green" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function OpportunityCard({ opportunity }: { opportunity: ArbitrageOpportunity }) {
  return (
    <div className="flex items-center justify-between p-4 bg-bg-secondary rounded-lg border border-border hover:border-accent-green/50 transition-colors">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <Badge variant="outline" className="text-xs">
            {opportunity.type.replace('_', ' ').toUpperCase()}
          </Badge>
          <span className="text-sm font-medium">Market Name Here</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Liquidity: {formatCurrency(opportunity.liquidity)}
        </p>
      </div>
      <div className="text-right">
        <p className="text-lg font-mono font-bold text-accent-green">
          {formatPercent(opportunity.netProfitPct)}
        </p>
        <p className="text-xs text-muted-foreground">
          ~{formatCurrency(opportunity.requiredCapital * (opportunity.netProfitPct / 100))}
        </p>
      </div>
    </div>
  )
}

function TradeCard({ trade }: { trade: Trade }) {
  const isProfit = (trade.profitUsd || 0) > 0

  return (
    <div className="flex items-center gap-3 p-3 bg-bg-secondary rounded-lg">
      <div className={`px-2 py-1 rounded text-xs font-medium ${
        trade.type === 'buy'
          ? 'bg-accent-green/10 text-accent-green'
          : 'bg-accent-red/10 text-accent-red'
      }`}>
        {trade.type.toUpperCase()}
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium">Market</p>
        <p className="text-xs text-muted-foreground">{trade.strategyId}</p>
      </div>
      <div className="text-right">
        <p className={`text-sm font-mono ${isProfit ? 'text-accent-green' : 'text-accent-red'}`}>
          {isProfit ? '+' : ''}{formatCurrency(trade.profitUsd || 0)}
        </p>
      </div>
    </div>
  )
}

function PlatformStatus({ name, status }: { name: string; status: 'online' | 'offline' | 'error' }) {
  const statusConfig = {
    online: { color: 'bg-accent-green', text: 'text-accent-green', label: 'Online' },
    offline: { color: 'bg-muted-foreground', text: 'text-muted-foreground', label: 'Offline' },
    error: { color: 'bg-accent-red', text: 'text-accent-red', label: 'Error' },
  }

  const config = statusConfig[status]

  return (
    <div className="flex items-center gap-2 p-3 bg-bg-secondary rounded-lg">
      <div className={`w-2 h-2 rounded-full ${config.color} ${status === 'online' ? 'animate-pulse-green' : ''}`} />
      <div>
        <p className="text-sm font-medium">{name}</p>
        <p className={`text-xs ${config.text}`}>{config.label}</p>
      </div>
    </div>
  )
}
