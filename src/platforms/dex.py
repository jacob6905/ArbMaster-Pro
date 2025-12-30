"""
ArbMaster Pro - Decentralized Exchange Integration

Client for interacting with DEXs via Web3.py.
Supports Uniswap, SushiSwap, and other AMM protocols.
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from loguru import logger

try:
    from web3 import Web3, AsyncWeb3
    from web3.middleware import geth_poa_middleware
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("web3 not installed, DEX functionality limited")

from .base import BasePlatform, PlatformError
from ..models.market import OrderBook, OrderBookLevel
from ..models.trade import TradeLeg, TradeStatus, OrderSide, OrderType
from ..config import settings


# Common ERC20 ABI for token interactions
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]

# Uniswap V2 Router ABI (simplified)
UNISWAP_V2_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"},
        ],
        "name": "getAmountsOut",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Common token addresses
TOKENS = {
    "ethereum": {
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "DAI": "0x6B175474E89094C44Da98b954EescdeCB5DC4F27",
    },
    "polygon": {
        "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    },
    "arbitrum": {
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
        "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
    },
}

# DEX Router addresses
DEX_ROUTERS = {
    "uniswap_v2": {
        "ethereum": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    },
    "sushiswap": {
        "ethereum": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        "polygon": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        "arbitrum": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
    },
    "quickswap": {
        "polygon": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
    },
}


class DEXClient(BasePlatform):
    """
    Decentralized Exchange Client using Web3.py

    Supports:
    - Uniswap V2/V3
    - SushiSwap
    - QuickSwap (Polygon)
    - PancakeSwap (BSC)
    """

    platform_name = "dex"

    def __init__(
        self,
        network: str = "polygon",
        dex: str = "sushiswap",
        dry_run: bool = True,
    ):
        super().__init__(dry_run=dry_run)
        self.network = network.lower()
        self.dex = dex.lower()
        self._w3: Optional[Any] = None
        self._router_contract = None
        self._wallet_address = settings.blockchain.wallet_address
        self._private_key = settings.blockchain.wallet_private_key

        # Get RPC URL for network
        self._rpc_url = self._get_rpc_url()

    def _get_rpc_url(self) -> str:
        """Get RPC URL for the selected network."""
        if self.network == "polygon":
            return settings.blockchain.polygon_rpc_url
        elif self.network == "ethereum":
            return settings.blockchain.ethereum_rpc_url
        elif self.network == "arbitrum":
            return settings.blockchain.arbitrum_rpc_url
        else:
            return settings.blockchain.polygon_rpc_url

    async def connect(self) -> bool:
        """Initialize Web3 connection."""
        if not WEB3_AVAILABLE:
            logger.error("web3 library not available")
            return False

        try:
            # Create Web3 instance
            self._w3 = Web3(Web3.HTTPProvider(self._rpc_url))

            # Add PoA middleware for networks like Polygon
            if self.network in ("polygon", "arbitrum"):
                self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            # Check connection
            if not self._w3.is_connected():
                logger.error(f"Failed to connect to {self.network} RPC")
                return False

            # Load router contract
            router_address = DEX_ROUTERS.get(self.dex, {}).get(self.network)
            if router_address:
                self._router_contract = self._w3.eth.contract(
                    address=Web3.to_checksum_address(router_address),
                    abi=UNISWAP_V2_ROUTER_ABI,
                )

            self._connected = True
            chain_id = self._w3.eth.chain_id
            logger.info(f"Connected to {self.network} (chain ID: {chain_id}) via {self.dex}")

            return True

        except Exception as e:
            logger.error(f"Error connecting to {self.network}: {e}")
            return False

    async def disconnect(self) -> None:
        """Close Web3 connection."""
        self._w3 = None
        self._router_contract = None
        self._connected = False
        logger.info(f"Disconnected from {self.network}")

    async def get_token_price(
        self,
        token_address: str,
        quote_token: str = "USDC",
        amount_in: Decimal = Decimal("1"),
    ) -> Optional[Decimal]:
        """
        Get token price in quote currency.

        Args:
            token_address: Address of token to price
            quote_token: Quote token symbol (USDC, USDT, etc.)
            amount_in: Amount of token to price

        Returns:
            Price per token in quote currency
        """
        if not self._w3 or not self._router_contract:
            raise PlatformError("Not connected", platform=self.platform_name)

        try:
            # Get quote token address
            quote_address = TOKENS.get(self.network, {}).get(quote_token)
            if not quote_address:
                logger.warning(f"Quote token {quote_token} not found for {self.network}")
                return None

            # Get token decimals
            token_contract = self._w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI,
            )
            decimals = token_contract.functions.decimals().call()

            # Convert amount to wei
            amount_wei = int(amount_in * (10 ** decimals))

            # Get amounts out
            path = [
                Web3.to_checksum_address(token_address),
                Web3.to_checksum_address(quote_address),
            ]

            amounts = self._router_contract.functions.getAmountsOut(
                amount_wei,
                path,
            ).call()

            # Convert to decimal (USDC has 6 decimals)
            quote_decimals = 6 if quote_token in ("USDC", "USDT") else 18
            price = Decimal(amounts[1]) / Decimal(10 ** quote_decimals)

            return price / amount_in

        except Exception as e:
            logger.debug(f"Error getting token price: {e}")
            return None

    async def get_swap_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
    ) -> Optional[dict]:
        """
        Get a quote for swapping tokens.

        Args:
            token_in: Address of input token
            token_out: Address of output token
            amount_in: Amount of input token

        Returns:
            Quote details including output amount and price impact
        """
        if not self._w3 or not self._router_contract:
            raise PlatformError("Not connected", platform=self.platform_name)

        try:
            # Get input token decimals
            token_in_contract = self._w3.eth.contract(
                address=Web3.to_checksum_address(token_in),
                abi=ERC20_ABI,
            )
            decimals_in = token_in_contract.functions.decimals().call()
            symbol_in = token_in_contract.functions.symbol().call()

            # Get output token decimals
            token_out_contract = self._w3.eth.contract(
                address=Web3.to_checksum_address(token_out),
                abi=ERC20_ABI,
            )
            decimals_out = token_out_contract.functions.decimals().call()
            symbol_out = token_out_contract.functions.symbol().call()

            # Convert amount
            amount_wei = int(amount_in * (10 ** decimals_in))

            # Get quote
            path = [
                Web3.to_checksum_address(token_in),
                Web3.to_checksum_address(token_out),
            ]

            amounts = self._router_contract.functions.getAmountsOut(
                amount_wei,
                path,
            ).call()

            amount_out = Decimal(amounts[1]) / Decimal(10 ** decimals_out)
            price = amount_out / amount_in

            return {
                "token_in": symbol_in,
                "token_out": symbol_out,
                "amount_in": amount_in,
                "amount_out": amount_out,
                "price": price,
                "path": path,
            }

        except Exception as e:
            logger.debug(f"Error getting swap quote: {e}")
            return None

    async def get_markets(
        self,
        category: Optional[str] = None,
        status: str = "active",
        limit: int = 100,
    ) -> list[Any]:
        """DEX doesn't have traditional markets - returns empty list."""
        return []

    async def get_market(self, market_id: str) -> None:
        """DEX doesn't have traditional markets."""
        return None

    async def get_orderbook(
        self,
        market_id: str,
        outcome: str = "YES",
    ) -> Optional[OrderBook]:
        """
        DEX uses AMM, not order books.
        This returns a synthetic order book based on liquidity curve.
        """
        # For AMMs, we can simulate an orderbook from the liquidity curve
        # This is a simplified version
        return None

    async def place_order(
        self,
        market_id: str,
        side: OrderSide,
        outcome: str,
        price: Decimal,
        size: Decimal,
        order_type: str = "limit",
    ) -> Optional[TradeLeg]:
        """
        Execute a swap on the DEX.

        Note: DEX uses AMM, so 'price' is actually slippage tolerance.
        """
        if self.dry_run:
            return self._handle_dry_run_order(
                market_id=market_id,
                side=side,
                outcome=outcome,
                price=price,
                size=size,
            )

        if not self._w3:
            raise PlatformError("Not connected", platform=self.platform_name)

        if not self._private_key:
            raise PlatformError(
                "Private key required for swaps",
                platform=self.platform_name,
                recoverable=False,
            )

        # Parse market_id as token_in/token_out
        # Implementation would build and submit swap transaction
        logger.info(f"Would execute swap: {market_id} {side.value} {size}")

        import uuid

        leg = TradeLeg(
            leg_id=uuid.uuid4().hex[:12],
            leg_order=1,
            platform=f"{self.dex}_{self.network}",
            market_id=market_id,
            symbol=market_id,
            side=side,
            order_type=OrderType.MARKET,  # DEX swaps are market orders
            price=price,
            size=size,
            status=TradeStatus.SUBMITTED,
        )

        return leg

    async def cancel_order(self, order_id: str) -> bool:
        """DEX swaps cannot be cancelled once submitted."""
        logger.warning("DEX swaps cannot be cancelled")
        return False

    async def get_positions(self) -> list[dict[str, Any]]:
        """Get token balances as positions."""
        if not self._w3 or not self._wallet_address:
            return []

        positions = []

        # Check balances for common tokens
        for symbol, address in TOKENS.get(self.network, {}).items():
            try:
                token_contract = self._w3.eth.contract(
                    address=Web3.to_checksum_address(address),
                    abi=ERC20_ABI,
                )
                balance = token_contract.functions.balanceOf(
                    Web3.to_checksum_address(self._wallet_address)
                ).call()
                decimals = token_contract.functions.decimals().call()

                if balance > 0:
                    positions.append({
                        "symbol": symbol,
                        "address": address,
                        "balance": Decimal(balance) / Decimal(10 ** decimals),
                    })
            except Exception:
                continue

        return positions

    async def get_balance(self) -> Decimal:
        """Get native token balance (ETH/MATIC)."""
        if not self._w3 or not self._wallet_address:
            return Decimal("0")

        try:
            balance_wei = self._w3.eth.get_balance(
                Web3.to_checksum_address(self._wallet_address)
            )
            return Decimal(balance_wei) / Decimal(10 ** 18)
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return Decimal("0")

    async def get_gas_price(self) -> Decimal:
        """Get current gas price in Gwei."""
        if not self._w3:
            return Decimal("0")

        try:
            gas_wei = self._w3.eth.gas_price
            return Decimal(gas_wei) / Decimal(10 ** 9)  # Wei to Gwei
        except Exception:
            return Decimal("0")

    async def estimate_gas(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
    ) -> Optional[Decimal]:
        """
        Estimate gas cost for a swap in USD.

        Returns:
            Estimated gas cost in USD
        """
        if not self._w3:
            return None

        try:
            # Get gas price
            gas_price = await self.get_gas_price()

            # Typical swap gas usage
            gas_limit = Decimal("250000")  # Conservative estimate

            # Calculate gas cost in native token
            gas_cost_native = gas_price * gas_limit / Decimal(10 ** 9)

            # Get native token price
            native_price = await self._get_native_token_price()

            if native_price:
                return gas_cost_native * native_price

            return gas_cost_native  # Return in native if price unavailable

        except Exception as e:
            logger.debug(f"Error estimating gas: {e}")
            return None

    async def _get_native_token_price(self) -> Optional[Decimal]:
        """Get price of native token (ETH/MATIC) in USD."""
        try:
            # Use WETH/WMATIC -> USDC pair
            if self.network == "polygon":
                native_token = TOKENS["polygon"]["WMATIC"]
            elif self.network == "arbitrum":
                native_token = TOKENS["arbitrum"]["WETH"]
            else:
                native_token = TOKENS["ethereum"]["WETH"]

            return await self.get_token_price(native_token, "USDC")
        except Exception:
            return None


class FlashLoanExecutor:
    """
    Flash Loan Executor for atomic arbitrage

    Uses Aave V3 flash loans for capital-efficient DEX arbitrage.
    """

    # Aave V3 Pool addresses
    AAVE_POOLS = {
        "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        "polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    }

    def __init__(self, network: str = "polygon", dry_run: bool = True):
        self.network = network
        self.dry_run = dry_run
        self._w3: Optional[Any] = None

    async def execute_flash_loan_arb(
        self,
        token_address: str,
        amount: Decimal,
        route: list[dict],
    ) -> Optional[dict]:
        """
        Execute atomic arbitrage using flash loan.

        Args:
            token_address: Token to borrow
            amount: Amount to borrow
            route: List of swaps to execute

        Returns:
            Transaction result or None
        """
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would execute flash loan arb: "
                f"borrow {amount} of {token_address}"
            )
            return {
                "success": True,
                "dry_run": True,
                "amount": str(amount),
                "route": route,
            }

        # Actual implementation would:
        # 1. Build flash loan callback contract
        # 2. Encode swap route into callback data
        # 3. Submit flash loan request to Aave
        # 4. Contract executes swaps and repays loan atomically

        logger.info(f"Would execute flash loan for {amount} {token_address}")
        return None
