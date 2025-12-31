"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart3 } from "lucide-react"

export function Analytics() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Analytics</h2>
        <p className="text-muted-foreground">Performance analytics and insights</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profit History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-24 text-muted-foreground">
            <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p>Analytics charts will be displayed here</p>
            <p className="text-sm mt-2">Connect to backend to view real-time data</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
