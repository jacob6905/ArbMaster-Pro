"use client"

import { useState } from "react"
import { Sidebar } from "./sidebar"
import { Header } from "./header"
import { DashboardOverview } from "./dashboard-overview"
import { Scanner } from "./scanner"
import { Strategies } from "./strategies"
import { Analytics } from "./analytics"
import { Settings } from "./settings"

export type Page = "dashboard" | "scanner" | "strategies" | "analytics" | "settings"

export function Dashboard() {
  const [currentPage, setCurrentPage] = useState<Page>("dashboard")

  return (
    <div className="flex h-screen bg-bg-primary">
      {/* Sidebar */}
      <Sidebar currentPage={currentPage} onPageChange={setCurrentPage} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          {currentPage === "dashboard" && <DashboardOverview />}
          {currentPage === "scanner" && <Scanner />}
          {currentPage === "strategies" && <Strategies />}
          {currentPage === "analytics" && <Analytics />}
          {currentPage === "settings" && <Settings />}
        </main>
      </div>
    </div>
  )
}
