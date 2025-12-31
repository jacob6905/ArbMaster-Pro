import { getDefaultConfig } from "@rainbow-me/rainbowkit"
import { polygon, polygonAmoy } from "wagmi/chains"

export const config = getDefaultConfig({
  appName: "ArbMaster Pro",
  projectId: process.env.NEXT_PUBLIC_WALLET_CONNECT_PROJECT_ID || "YOUR_PROJECT_ID",
  chains: [polygon, polygonAmoy],
  ssr: true,
})
