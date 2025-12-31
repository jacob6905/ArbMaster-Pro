/**
 * React Query hooks for ArbMaster Pro API
 *
 * Provides type-safe hooks for fetching data from the backend.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient, queryKeys } from "@/lib/api-client"

// ============================================================================
// Performance Metrics
// ============================================================================

export function useMetrics() {
  return useQuery({
    queryKey: queryKeys.metrics,
    queryFn: () => apiClient.getMetrics(),
    refetchInterval: 5000, // Refetch every 5 seconds
  })
}

// ============================================================================
// Opportunities
// ============================================================================

export function useOpportunities(limit?: number) {
  return useQuery({
    queryKey: [...queryKeys.opportunities, limit],
    queryFn: () => apiClient.getOpportunities(limit),
    refetchInterval: 2000, // Refetch every 2 seconds for real-time feel
  })
}

// ============================================================================
// Trades
// ============================================================================

export function useTrades(limit?: number) {
  return useQuery({
    queryKey: [...queryKeys.trades, limit],
    queryFn: () => apiClient.getTrades(limit),
    refetchInterval: 5000,
  })
}

// ============================================================================
// Positions
// ============================================================================

export function usePositions() {
  return useQuery({
    queryKey: queryKeys.positions,
    queryFn: () => apiClient.getPositions(),
    refetchInterval: 10000,
  })
}

// ============================================================================
// Strategies
// ============================================================================

export function useStrategies() {
  return useQuery({
    queryKey: queryKeys.strategies,
    queryFn: () => apiClient.getStrategies(),
  })
}

export function useToggleStrategy() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (strategyId: string) => apiClient.toggleStrategy(strategyId),
    onSuccess: () => {
      // Invalidate strategies query to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.strategies })
    },
  })
}

// ============================================================================
// Platform Status
// ============================================================================

export function usePlatformStatus() {
  return useQuery({
    queryKey: queryKeys.platforms,
    queryFn: () => apiClient.getPlatformStatus(),
    refetchInterval: 10000,
  })
}

// ============================================================================
// Circuit Breaker
// ============================================================================

export function useCircuitBreaker() {
  return useQuery({
    queryKey: queryKeys.circuitBreaker,
    queryFn: () => apiClient.getCircuitBreaker(),
    refetchInterval: 5000,
  })
}

// ============================================================================
// Config
// ============================================================================

export function useConfig() {
  return useQuery({
    queryKey: queryKeys.config,
    queryFn: () => apiClient.getConfig(),
    staleTime: Infinity, // Config rarely changes
  })
}

// ============================================================================
// Health Check
// ============================================================================

export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiClient.healthCheck(),
    refetchInterval: 30000, // Every 30 seconds
  })
}
