/**
 * ArbMaster Pro - Frontend API Client
 *
 * Handles all communication with the FastAPI backend.
 * Includes REST API calls and WebSocket connection.
 */

import type {
  PerformanceMetrics,
  ArbitrageOpportunity,
  Trade,
  Position,
  StrategyConfig,
} from "@/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"

// ============================================================================
// REST API Client
// ============================================================================

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`)
    }

    return response.json()
  }

  // Health & Status
  async healthCheck() {
    return this.fetch<{
      status: string
      timestamp: string
      uptime_seconds: number
      mode: string
      version: string
    }>("/health")
  }

  // Performance Metrics
  async getMetrics(): Promise<PerformanceMetrics> {
    return this.fetch<PerformanceMetrics>("/api/metrics")
  }

  // Opportunities
  async getOpportunities(limit: number = 20): Promise<ArbitrageOpportunity[]> {
    return this.fetch<ArbitrageOpportunity[]>(`/api/opportunities?limit=${limit}`)
  }

  // Trades
  async getTrades(limit: number = 50): Promise<Trade[]> {
    return this.fetch<Trade[]>(`/api/trades?limit=${limit}`)
  }

  // Positions
  async getPositions(): Promise<Position[]> {
    return this.fetch<Position[]>("/api/positions")
  }

  // Strategies
  async getStrategies(): Promise<StrategyConfig[]> {
    return this.fetch<StrategyConfig[]>("/api/strategies")
  }

  async toggleStrategy(strategyId: string): Promise<{
    success: boolean
    strategy_id: string
    enabled: boolean
  }> {
    return this.fetch(`/api/strategies/${strategyId}/toggle`, {
      method: "POST",
    })
  }

  // Platform Status
  async getPlatformStatus(): Promise<Array<{
    name: string
    platform: string
    status: string
    last_update: string
    latency_ms: number | null
  }>> {
    return this.fetch("/api/platforms")
  }

  // Circuit Breaker
  async getCircuitBreaker(): Promise<{
    is_triggered: boolean
    daily_loss: number
    max_daily_loss: number
    consecutive_errors: number
    max_consecutive_errors: number
    trades_today: number
    max_trades_per_day: number
    reason: string | null
  }> {
    return this.fetch("/api/circuit-breaker")
  }

  // Config
  async getConfig(): Promise<{
    execution: { dry_run: boolean; debug: boolean }
    risk: Record<string, number>
    performance: Record<string, number>
  }> {
    return this.fetch("/api/config")
  }
}

export const apiClient = new ApiClient()

// ============================================================================
// WebSocket Client
// ============================================================================

type WebSocketMessage =
  | { type: "connected"; data: { timestamp: string; message: string } }
  | { type: "new_opportunity"; data: ArbitrageOpportunity }
  | { type: "metrics_update"; data: PerformanceMetrics }
  | { type: "trade_executed"; data: Trade }
  | { type: "echo"; data: string }

type WebSocketCallback = (message: WebSocketMessage) => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private callbacks: Set<WebSocketCallback> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(url: string = `${WS_URL}/ws`) {
    this.url = url
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log("WebSocket already connected")
      return
    }

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log("WebSocket connected")
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.callbacks.forEach((callback) => callback(message))
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error)
        }
      }

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error)
      }

      this.ws.onclose = () => {
        console.log("WebSocket disconnected")
        this.reconnect()
      }
    } catch (error) {
      console.error("Failed to create WebSocket:", error)
      this.reconnect()
    }
  }

  private reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnect attempts reached")
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    console.log(`Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts})`)

    setTimeout(() => {
      this.connect()
    }, delay)
  }

  subscribe(callback: WebSocketCallback): () => void {
    this.callbacks.add(callback)

    // Return unsubscribe function
    return () => {
      this.callbacks.delete(callback)
    }
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(typeof data === "string" ? data : JSON.stringify(data))
    } else {
      console.warn("WebSocket not connected, cannot send message")
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.callbacks.clear()
  }

  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }
}

export const wsClient = new WebSocketClient()

// ============================================================================
// React Query Hooks (for use with TanStack Query)
// ============================================================================

export const queryKeys = {
  metrics: ["metrics"] as const,
  opportunities: ["opportunities"] as const,
  trades: ["trades"] as const,
  positions: ["positions"] as const,
  strategies: ["strategies"] as const,
  platforms: ["platforms"] as const,
  circuitBreaker: ["circuit-breaker"] as const,
  config: ["config"] as const,
}

// ============================================================================
// Exports
// ============================================================================

export { ApiClient, WebSocketClient }
export type { WebSocketMessage, WebSocketCallback }
