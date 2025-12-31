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
  userId: string
  marketId: string
  outcomeId: string
  strategyId: string
  type: 'buy' | 'sell'
  side: 'YES' | 'NO'
  size: number
  price: number
  fees: number
  txHash?: string
  status: 'pending' | 'filled' | 'cancelled' | 'failed'
  executedAt: Date
  profitUsd?: number
}

export interface ArbitrageOpportunity {
  id: string
  type: StrategyType
  markets: MarketReference[]
  profitPct: number
  netProfitPct: number
  requiredCapital: number
  liquidity: number
  expiresAt: Date
  detectedAt: Date
  confidence: number
  aiAssessment?: AIAssessment
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
  userId: string
  type: StrategyType
  enabled: boolean
  allocation: number
  parameters: Record<string, any>
  createdAt: Date
  updatedAt: Date
}

export interface PerformanceMetrics {
  totalPnL: number
  dailyPnL: number
  weeklyPnL: number
  monthlyPnL: number
  winRate: number
  totalTrades: number
  activePositions: number
  activeCapital: number
  dailyROI: number
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
