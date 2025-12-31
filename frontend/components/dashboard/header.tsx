"use client"

import { Bell, Search } from "lucide-react"
import { ConnectButton } from "@rainbow-me/rainbowkit"

export function Header() {
  return (
    <header className="h-16 border-b border-border bg-bg-secondary px-6 flex items-center justify-between">
      {/* Search */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search markets..."
            className="w-full bg-bg-primary border border-border rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-green/50"
          />
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-4">
        {/* System Status */}
        <div className="flex items-center gap-2 px-3 py-1 bg-bg-primary rounded-lg">
          <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse-green" />
          <span className="text-xs text-accent-green font-medium">ONLINE</span>
        </div>

        {/* ETH Price */}
        <div className="px-3 py-1 bg-bg-primary rounded-lg">
          <span className="text-xs text-muted-foreground">ETH</span>
          <span className="text-xs font-mono ml-1">$3,420</span>
        </div>

        {/* Notifications */}
        <button className="w-10 h-10 rounded-lg bg-bg-primary hover:bg-bg-tertiary flex items-center justify-center transition-colors relative">
          <Bell className="w-5 h-5" />
          <div className="absolute top-2 right-2 w-2 h-2 bg-accent-red rounded-full" />
        </button>

        {/* Wallet Connect */}
        <ConnectButton
          chainStatus="icon"
          showBalance={false}
        />
      </div>
    </header>
  )
}
