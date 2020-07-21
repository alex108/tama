import aiohttp

__all__ = ["get_json"]


async def get_json(url: str, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, **kwargs) as response:
            data = await response.json()

    return data
