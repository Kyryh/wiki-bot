from httpx import AsyncClient
import re
from bs4 import BeautifulSoup

class Wiki:

    URL_PATH_REGEX = re.compile('(.*\..*?)?(\/.*)')

    def __init__(self, url: str):
        self.url = re.split("(?<!\W)/(?!\W)", url)[0]
        self.client = AsyncClient()
    
    async def search(self, query: str) -> dict[str, str]:
        search_response = await self.client.get(
            self.url + "/api.php",
            params = {
                "action": "query",
                "list": "search",
                "format": "json",
                "srsearch": query
            }
        )
        return {result["title"]: result["pageid"] for result in search_response.json()["query"]["search"]}

    async def get_page_content(self, page: str | int) -> dict[str, str]:
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
            self.url + "/api.php",
            params = params | {
                "action": "parse",
                "redirects": True,
                "format": "json",
                "prop": "text|langlinks|categories|links|templates|images|externallinks|sections|revid|displaytitle|iwlinks|properties|parsewarnings"
                #"prop": "text|wikitext"
            }
        )

        json = content.json()

        title = json["parse"]["title"]

        raw_content = json["parse"]["text"]["*"]

        parsed_content = self._parse_content(title, raw_content)


        return {
            "title": title,
            "raw_content": raw_content,
            "parsed_content": parsed_content
        }

    def _parse_content(self, title: str, raw_content: str) -> str:
        
        soup = BeautifulSoup(raw_content, "html.parser")
        
        soup.decode_contents

        content = [{"heading": title, "data": ""}]

        for element in soup.div.find_all(re.compile("^(p|h\d?)$"), recursive=False):
            if element.name.startswith("h"):
                if element.text:
                    content.append({"heading": element.span.decode_contents(), "data": ""})
            else:
                if element.text and not element.text.isspace():
                    content[-1]["data"] += element.decode_contents()

        return "\n\n".join(
            self._parse_section(section['heading'], section['data']) for section in content if section["data"] != ""
        )
    
    def _parse_section(self, heading: str, data: str) -> str:
        data = re.sub(r"<img\s.*?\/>", "", data)
        data = re.sub(r"<\/?(span|br).*?>", "", data)
        data = data.replace("href=\"", "href=\"" + self.url)
        data = data.replace("\xa0", "")
        return f"<b>{heading}</b>\n{data}"




