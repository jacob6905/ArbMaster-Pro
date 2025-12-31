"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Settings as SettingsIcon, Shield, Bell, Key } from "lucide-react"

export function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Settings</h2>
        <p className="text-muted-foreground">Configure your trading bot and platform integrations</p>
      </div>

      {/* Trading Mode */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SettingsIcon className="w-5 h-5" />
            Trading Mode
          </CardTitle>
          <CardDescription>Control how the bot executes trades</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Paper Trading Mode</p>
              <p className="text-sm text-muted-foreground">
                Simulate trades without risking real capital
              </p>
            </div>
            <Badge variant="success">Enabled</Badge>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Live Trading</p>
              <p className="text-sm text-muted-foreground">
                Execute real trades with actual capital
              </p>
            </div>
            <Badge variant="outline">Disabled</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Risk Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Risk Management
          </CardTitle>
          <CardDescription>Configure circuit breakers and risk limits</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Max Daily Loss</label>
              <input
                type="number"
                defaultValue="500"
                className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Max Position Size</label>
              <input
                type="number"
                defaultValue="10000"
                className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Slippage Tolerance %</label>
              <input
                type="number"
                step="0.1"
                defaultValue="0.5"
                className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">Min Profit Threshold %</label>
              <input
                type="number"
                step="0.1"
                defaultValue="1.0"
                className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="w-5 h-5" />
            API Keys
          </CardTitle>
          <CardDescription>Configure platform API credentials</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm text-muted-foreground mb-1 block">Polymarket API Key</label>
            <input
              type="password"
              placeholder="Enter your Polymarket API key"
              className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="text-sm text-muted-foreground mb-1 block">Kalshi Email</label>
            <input
              type="email"
              placeholder="Enter your Kalshi email"
              className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="text-sm text-muted-foreground mb-1 block">Kalshi Password</label>
            <input
              type="password"
              placeholder="Enter your Kalshi password"
              className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Notifications
          </CardTitle>
          <CardDescription>Configure alerts and notifications</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm text-muted-foreground mb-1 block">Telegram Bot Token</label>
            <input
              type="password"
              placeholder="Enter your Telegram bot token"
              className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="text-sm text-muted-foreground mb-1 block">Discord Webhook URL</label>
            <input
              type="url"
              placeholder="Enter your Discord webhook URL"
              className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button size="lg">
          Save Changes
        </Button>
      </div>
    </div>
  )
}
