// Core Types for ArbMaster Pro

export interface User {
  id: string
  walletAddress: string
  createdAt: Date
  settings: UserSettings
}

export interface UserSettings {
  enabledPlatforms: Platform[]
  enabledStrategies: StrategyType[]
  riskSettings: RiskSettings
  notificationSettings: NotificationSettings
}

export interface RiskSettings {
  maxDailyLoss: number
  maxDrawdown: number
  maxPositionSize: number
  maxTotalExposure: number
  slippageTolerance: number
}

export interface NotificationSettings {
  telegram: boolean
  discord: boolean
  email: boolean
  webhookUrl?: string
}

export type Platform = 'polymarket' | 'kalshi' | 'binance' | 'uniswap' | 'aave'

export type StrategyType =
  | 'binary_complement'
  | 'cross_platform'
  | 'multi_outcome'
  | 'dex_cex'
  | 'funding_rate'
  | 'yield_farming'

export interface Market {
  id: string
  platform: Platform
  title: string
  description: string
  category: string
  outcomes: Outcome[]
  resolutionDate: Date
  totalVolume: number
  totalLiquidity: number
  status: 'active' | 'resolved' | 'cancelled'
}

export interface Outcome {
  id: string
  marketId: string
  name: string
  currentPrice: number
  bestBid: number
  bestAsk: number
  volume24h: number
}

export interface Position {
  id: string
  userId: string
  marketId: string
  outcomeId: string
  side: 'YES' | 'NO'
  size: number
  avgEntryPrice: number
  currentValue: number
  unrealizedPnL: number
  createdAt: Date
}

export interface Trade {
  id: string
  market_id: string
  strategy_id: string
  type: string
  side: string
  size: number
  price: number
  fees: number
  status: string
  executed_at: string
  profit_usd?: number
}

export interface ArbitrageOpportunity {
  id: string
  type: StrategyType
  markets: any[]
  profit_pct: number
  net_profit_pct: number
  required_capital: number
  liquidity: number
  expires_at: string | null
  detected_at: string
  confidence: number
  title: string
  platforms: string[]
}

export interface MarketReference {
  platform: Platform
  marketId: string
  outcomeId: string
  price: number
  action: 'buy' | 'sell'
}

export interface AIAssessment {
  riskScore: number
  recommendation: string
  reasoning: string
  concerns: string[]
}

export interface StrategyConfig {
  id: string
  type: StrategyType
  name: string
  description: string
  enabled: boolean
  allocation: number
  roi: number
  trades: number
  win_rate: number
  parameters: Record<string, any>
}

export interface PerformanceMetrics {
  total_pnl: number
  daily_pnl: number
  weekly_pnl: number
  monthly_pnl: number
  win_rate: number
  total_trades: number
  active_positions: number
  active_capital: number
  daily_roi: number
}

export interface CircuitBreakerStatus {
  isTriggered: boolean
  dailyLoss: number
  maxDailyLoss: number
  consecutiveErrors: number
  maxConsecutiveErrors: number
  tradesToday: number
  maxTradesPerDay: number
  reason?: string
}

export interface WhaleTradeAlert {
  walletAddress: string
  market: string
  side: 'YES' | 'NO'
  amount: number
  price: number
  timestamp: Date
  insiderScore: number
  walletAge: number
  totalTransactions: number
  tradeImpact: number
}

export interface TraderProfile {
  address: string
  nickname?: string
  totalPnL: number
  winRate: number
  totalTrades: number
  avgTradeSize: number
  topCategories: CategoryPerformance[]
  preferredMarketTypes: string[]
  avgHoldTime: number
  overallRank: number
}

export interface CategoryPerformance {
  category: string
  pnl: number
  winRate: number
  tradeCount: number
}
