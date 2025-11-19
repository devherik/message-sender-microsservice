import asyncio

from tests.waha_api_test import test_waha_api_integration


async def main():
    result = await test_waha_api_integration()
    if result:
        print("Waha API integration test passed.")
    else:
        print("Waha API integration test failed.")


if __name__ == "__main__":
    asyncio.run(main())
