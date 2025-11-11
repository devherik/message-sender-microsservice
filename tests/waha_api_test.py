import httpx

from core.settings import settings


async def test_waha_api_integration() -> bool:
    try:
        api_url = f"{settings.waha_api_url}/ping"
        if not api_url.startswith("http"):
            raise ValueError("Invalid Waha API URL")
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0)
        ) as client:
            response = await client.get(
                api_url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"X-Api-Key {settings.waha_api_key}",
                },
            )
        response.raise_for_status()
        return True
    except httpx.HTTPError as e:
        print(f"Error occurred while testing Waha API: {e}")
        return False
