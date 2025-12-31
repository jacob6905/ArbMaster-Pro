"use client"

import {
  Home,
  Search,
  Target,
  BarChart3,
  Settings as SettingsIcon
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { Page } from "."

interface SidebarProps {
  currentPage: Page
  onPageChange: (page: Page) => void
}

const navItems = [
  { id: "dashboard" as Page, icon: Home, label: "Dashboard" },
  { id: "scanner" as Page, icon: Search, label: "Scanner" },
  { id: "strategies" as Page, icon: Target, label: "Strategies" },
  { id: "analytics" as Page, icon: BarChart3, label: "Analytics" },
  { id: "settings" as Page, icon: SettingsIcon, label: "Settings" },
]

export function Sidebar({ currentPage, onPageChange }: SidebarProps) {
  return (
    <div className="w-20 bg-bg-secondary border-r border-border flex flex-col items-center py-6 gap-4">
      {/* Logo */}
      <div className="mb-6">
        <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-accent-green to-emerald-400 flex items-center justify-center text-2xl font-bold">
          A
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex flex-col gap-2 flex-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = currentPage === item.id

          return (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id)}
              className={cn(
                "w-14 h-14 rounded-xl flex items-center justify-center transition-all group relative",
                isActive
                  ? "bg-accent-green/10 text-accent-green"
                  : "text-muted-foreground hover:bg-bg-tertiary hover:text-foreground"
              )}
              title={item.label}
            >
              <Icon className="w-6 h-6" />

              {/* Tooltip */}
              <div className="absolute left-full ml-2 px-2 py-1 bg-bg-tertiary rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                {item.label}
              </div>
            </button>
          )
        })}
      </nav>

      {/* Status Indicator */}
      <div className="mt-auto flex flex-col items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-accent-green animate-pulse-green"
             title="System Online" />
      </div>
    </div>
  )
}
