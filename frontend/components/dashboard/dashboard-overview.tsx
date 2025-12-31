"use client"

import { useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { formatCurrency, formatPercent } from "@/lib/utils"
import { TrendingUp, TrendingDown, Activity, DollarSign, Target, Zap, Loader2 } from "lucide-react"
import type { ArbitrageOpportunity, Trade } from "@/types"
import { useMetrics, useOpportunities, useTrades, usePlatformStatus } from "@/hooks/use-api"
import { wsClient } from "@/lib/api-client"

export function DashboardOverview() {
  // Fetch data using React Query hooks
  const { data: metrics, isLoading: metricsLoading } = useMetrics()
  const { data: opportunities = [], isLoading: oppsLoading } = useOpportunities(10)
  const { data: recentTrades = [], isLoading: tradesLoading } = useTrades(10)
  const { data: platforms = [] } = usePlatformStatus()

  // Connect to WebSocket for real-time updates
  useEffect(() => {
    wsClient.connect()

    const unsubscribe = wsClient.subscribe((message) => {
      console.log("WebSocket message:", message)
      // Messages are handled by React Query's automatic refetching
    })

    return () => {
      unsubscribe()
    }
  }, [])

  // Show loading state
  if (metricsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-accent-green" />
        <span className="ml-3 text-muted-foreground">Loading dashboard...</span>
      </div>
    )
  }

  if (!metrics) return null

  // Check if Polymarket is connected
  const polymarketConnected = platforms.some(
    (p) => p.platform === "polymarket" && p.status === "online"
  )

  return (
    <div className="space-y-6">
      {/* Connection Status Banner */}
      <div className="flex items-center justify-between px-4 py-3 rounded-lg border border-border bg-bg-secondary">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${polymarketConnected ? "bg-accent-green animate-pulse" : "bg-yellow-500"}`} />
          <span className="text-sm font-medium">
            {polymarketConnected ? "Connected to Polymarket" : "Using Demo Data"}
          </span>
          {polymarketConnected && (
            <Badge variant="success" className="text-xs">
              Live Data
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Activity className="w-3 h-3" />
          <span>Last scan: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Performance Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Daily P&L */}
        <MetricCard
          title="Daily P&L"
          value={formatCurrency(metrics.daily_pnl)}
          change={formatPercent(12.3)}
          positive={metrics.daily_pnl > 0}
          icon={DollarSign}
        />

        {/* Win Rate */}
        <MetricCard
          title="Win Rate"
          value={`${metrics.win_rate.toFixed(1)}%`}
          change={`${metrics.total_trades} trades`}
          positive={metrics.win_rate > 85}
          icon={Target}
        />

        {/* Active Positions */}
        <MetricCard
          title="Active Positions"
          value={metrics.active_positions.toString()}
          change={formatCurrency(metrics.active_capital)}
          positive={true}
          icon={Activity}
        />

        {/* Daily ROI */}
        <MetricCard
          title="Daily ROI"
          value={`${metrics.daily_roi.toFixed(1)}%`}
          change={formatPercent(0.4)}
          positive={metrics.daily_roi > 0}
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
            {platforms.map((platform) => (
              <PlatformStatus
                key={platform.platform}
                name={platform.name}
                status={platform.status as 'online' | 'offline' | 'error'}
              />
            ))}
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
          {formatPercent(opportunity.net_profit_pct)}
        </p>
        <p className="text-xs text-muted-foreground">
          ~{formatCurrency(opportunity.required_capital * (opportunity.net_profit_pct / 100))}
        </p>
      </div>
    </div>
  )
}

function TradeCard({ trade }: { trade: Trade }) {
  const isProfit = (trade.profit_usd || 0) > 0

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
        <p className="text-xs text-muted-foreground">{trade.strategy_id}</p>
      </div>
      <div className="text-right">
        <p className={`text-sm font-mono ${isProfit ? 'text-accent-green' : 'text-accent-red'}`}>
          {isProfit ? '+' : ''}{formatCurrency(trade.profit_usd || 0)}
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
