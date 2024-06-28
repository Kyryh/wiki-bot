from httpx import AsyncClient
import re

class Wiki:

    SEARCH_REGEX = re.compile('(<div class="mw-search-result-heading">|<h3 class="unified-search__result__header">)\s*<a href="(.*?)".*?title="(.*?)"', re.S)
    CONTENT_REGEX = re.compile("<textarea.*?>(.*?)<\/textarea>", re.S)
    URL_PATH_REGEX = re.compile('(.*\..*?)?(\/.*)')

    def __init__(self, url: str):
        self.url = re.split("(?<!\W)/(?!\W)", url)[0] + "/api.php"
        self.client = AsyncClient()
    
    async def search(self, query: str) -> dict[str, str]:
        search_response = await self.client.get(
            self.url,
            params = {
                "action": "query",
                "list": "search",
                "format": "json",
                "srsearch": query
            }
        )
        return {result["title"]: result["pageid"] for result in search_response.json()["query"]["search"]}

    async def get_page_content(self, page: str | int) -> str:
        if isinstance(page, str):
            params = {
                "page": page
            }
        elif isinstance(page, int):
            params = {
                "pageid": page
            }
        else:
            raise ValueError("Invalid argument type for 'page'")
            
        content = await self.client.get(
            self.url,
            params = params | {
                "action": "parse",
                "redirects": True,
                "format": "json",
                "prop": "text"
                #"prop": "text|wikitext"
            }
        )

        return content.json()["parse"]["text"]["*"]

    def parse_content(self, content: str) -> str:
        
        


        return content
