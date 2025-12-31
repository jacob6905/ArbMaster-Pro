import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatPercent(value: number, decimals: number = 2): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`
}

export function formatNumber(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function truncateAddress(address: string, chars: number = 4): string {
  return `${address.slice(0, chars + 2)}...${address.slice(-chars)}`
}

export function calculateProfitColor(profit: number): string {
  if (profit > 0) return 'text-accent-green'
  if (profit < 0) return 'text-accent-red'
  return 'text-muted-foreground'
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'online':
    case 'active':
    case 'running':
    case 'success':
      return 'text-accent-green'
    case 'offline':
    case 'paused':
    case 'inactive':
      return 'text-muted-foreground'
    case 'error':
    case 'failed':
      return 'text-accent-red'
    case 'warning':
      return 'text-yellow-500'
    default:
      return 'text-muted-foreground'
  }
}
