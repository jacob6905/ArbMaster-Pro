"use client"

import { useState } from "react"
import {
  Home,
  Search,
  Target,
  BarChart3,
  Settings as SettingsIcon,
  ChevronLeft,
  ChevronRight
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
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div
      className={cn(
        "bg-bg-secondary border-r border-border flex flex-col transition-all duration-300 ease-in-out relative",
        isExpanded ? "w-64" : "w-20"
      )}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-center border-b border-border">
        <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-accent-green to-emerald-400 flex items-center justify-center text-2xl font-bold transition-transform hover:scale-105">
          A
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 py-6 px-3 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = currentPage === item.id

          return (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id)}
              className={cn(
                "w-full rounded-xl flex items-center transition-all group relative overflow-hidden",
                isExpanded ? "px-4 py-3 justify-start" : "px-0 py-3 justify-center",
                isActive
                  ? "bg-accent-green/10 text-accent-green"
                  : "text-muted-foreground hover:bg-bg-tertiary hover:text-foreground"
              )}
              title={!isExpanded ? item.label : undefined}
            >
              {/* Active indicator */}
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-accent-green rounded-r" />
              )}

              <Icon className={cn("w-5 h-5 flex-shrink-0", isExpanded && "mr-3")} />

              {/* Label - only show when expanded */}
              <span className={cn(
                "whitespace-nowrap font-medium transition-all duration-300",
                isExpanded ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-4 absolute"
              )}>
                {item.label}
              </span>

              {/* Tooltip - only show when collapsed */}
              {!isExpanded && (
                <div className="absolute left-full ml-2 px-3 py-2 bg-bg-tertiary rounded-lg text-sm whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 border border-border">
                  {item.label}
                </div>
              )}
            </button>
          )
        })}
      </nav>

      {/* Status Indicator */}
      <div className="p-4 border-t border-border">
        <div className={cn(
          "flex items-center transition-all",
          isExpanded ? "justify-start gap-3" : "justify-center"
        )}>
          <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse-green" />
          {isExpanded && (
            <span className="text-xs text-accent-green font-medium">System Online</span>
          )}
        </div>
      </div>

      {/* Expand/Collapse Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-bg-secondary border border-border flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-bg-tertiary transition-colors z-50"
        aria-label={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
      >
        {isExpanded ? (
          <ChevronLeft className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
      </button>
    </div>
  )
}
