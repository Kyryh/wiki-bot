from httpx import AsyncClient
import re
from html import unescape as unescape_html

class Wiki:

    SEARCH_REGEX = re.compile('(<div class="mw-search-result-heading">|<h3 class="unified-search__result__header">)\s*<a href="(.*?)".*?title="(.*?)"', re.S)
    CONTENT_REGEX = re.compile("<textarea.*?>(.*?)<\/textarea>", re.S)
    URL_PATH_REGEX = re.compile('(.*\..*?)?(\/.*)')

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
        return {result[2]: self.URL_PATH_REGEX.search(result[1]).group(2) for result in search_results}

    async def get_page_content(self, path: str) -> str:
        content = await self.client.get(
            self.base_url + path,
            params = {
                "action": "edit"
            }
        )
        return unescape_html(self.CONTENT_REGEX.search(content.text).group(1))

    def parse_content(self, content: str) -> str:
        
        def template(match: re.Match[str]):
            params = match.group(1).split("|")
            print(params)
            if len(params) > 2:
                return ""
            return params[-1]

        content = re.sub(r"{{(.*?)}}\s", template, content, flags=re.S)


        return content
