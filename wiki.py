from httpx import AsyncClient
import re

class Wiki:

    SEARCH_REGEX = re.compile('<div class="mw-search-result-heading"><a href="(.*?)" title="(.*?)".*?<\/div>')

    def __init__(self, base_url: str):
        self.base_url = re.split("(?<!\W)/(?!\W)", base_url)[0]
        self.client = AsyncClient()
    
    async def search(self, query: str) -> dict[str, str]:
        search_response = await self.client.get(
            self.base_url + "/wiki/Special:Search",
            params = {
                "search": query,
                "ns0": 1,
                "fulltext": 1
            }
        )
        search_results = self.SEARCH_REGEX.findall(search_response.text)
        return {result[1]: result[0] for result in search_results}
