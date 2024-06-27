from httpx import AsyncClient
import re
from html import unescape as unescape_html

class Wiki:

    SEARCH_REGEX = re.compile('<div class="mw-search-result-heading"><a href="(.*?)" title="(.*?)".*?<\/div>')
    CONTENT_REGEX = re.compile("<textarea.*?>(.*?)<\/textarea>", re.S)

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

    async def get_page_content(self, path: str) -> str:
        content = await self.client.get(
            self.base_url + path,
            params = {
                "action": "edit"
            }
        )
        return unescape_html(self.CONTENT_REGEX.search(content.text).group(1))
