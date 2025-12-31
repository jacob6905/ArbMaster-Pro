import type { Metadata } from "next"
import "./globals.css"
import { Providers } from "@/components/providers"

export const metadata: Metadata = {
  title: "ArbMaster Pro | Universal Arbitrage Trading Platform",
  description: "Automated arbitrage trading across prediction markets, CEX, DEX, and DeFi protocols. Target: $500+ daily profit through risk-neutral strategies.",
  keywords: ["arbitrage", "prediction markets", "polymarket", "kalshi", "crypto trading", "defi"],
  authors: [{ name: "ArbMaster Pro" }],
  viewport: "width=device-width, initial-scale=1",
  themeColor: "#00ff88",
  icons: {
    icon: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
