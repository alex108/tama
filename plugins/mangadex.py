from typing import Match
from tama import api
from tama.util import http

__all__ = ["mangadex"]


@api.regex(r"^https://mangadex.org/title/([0-9]+)/")
async def mangadex(match: Match) -> str:
    url = 'https://mangadex.org/api/manga/' + match.group(1)
    hdr = {'User-Agent': 'Mozilla/5.0'}
    data = await http.get_json(url, headers=hdr)
    return data["manga"]["title"]
