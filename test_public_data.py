
import asyncio
from src.utils.public_data import PublicDataProvider
import json

async def test_public_data():
    print("Testing PublicDataProvider...")
    
    print("\nFetching Polymarket Data...")
    poly_data = await PublicDataProvider.fetch_polymarket_data()
    print(f"Polymarket Results: {len(poly_data)}")
    if poly_data:
        print(json.dumps(poly_data[0], indent=2, default=str))
        
    print("\nFetching Kalshi Data...")
    kalshi_data = await PublicDataProvider.fetch_kalshi_data()
    print(f"Kalshi Results: {len(kalshi_data)}")
    if kalshi_data:
        print(json.dumps(kalshi_data[0], indent=2, default=str))

    print("\nFetching Binance Prices...")
    binance_data = await PublicDataProvider.fetch_binance_prices()
    print(f"Binance Results: {binance_data}")

if __name__ == "__main__":
    asyncio.run(test_public_data())
