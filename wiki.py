from collections import defaultdict
from httpx import AsyncClient
import re
from bs4 import BeautifulSoup
import textwrap

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

        return "\n".join(
            self._parse_section(section['heading'], section['data']) for section in content if section["data"] != ""
        )
    
    def _parse_section(self, heading: str, data: str) -> str:
        def href_fix(m: re.Match[str]):
            url = m.group(1)
            if url.startswith("/"):
                url = self.url + url
            return f'<a href="{url}">'
        
        data = re.sub(r"<img.*?\/>", "", data)
        data = re.sub(r"<\/?(span|br).*?>", "", data)
        heading = re.sub(r"<\/?span.*?>", "", heading)
        data = re.sub(r"<a .*?href=\"(.*?)\".*?>", href_fix, data)
        data = re.sub(r"<audio.*?>.*?<\/audio>", "", data)
        data = re.sub(r"<sup.*?>.*?<\/sup>", "", data)
        data = data.replace("\xa0", "")
        return f"<b>{heading}</b>\n{data}"
    
    @staticmethod
    def fix_tags_single(text: str) -> tuple[str, str]:
        tags: list[str] = re.findall(r"<(.*?)>", text)
        tags_count = defaultdict(int)
        last_tags = defaultdict(list)
        for tag in tags:
            effective_tag = tag.replace("/", "").split(" ")[0]
            if tag[0] != "/":
                last_tags[effective_tag].append(tag)
                tags_count[effective_tag] += 1
            else:
                tags_count[effective_tag] -= 1

        next_text_prefix = ""
        for tag, count in tags_count.items():
            if count > 0:
                text += "</"+tag*count+">"
                next_text_prefix += "<"+last_tags[tag].pop()+">"
        
        return text, next_text_prefix
    
    @staticmethod
    def fix_tags_multiple(texts: list[str]) -> list[str]:
        new_texts = list(texts)
        text_prefix = ""
        for i in range(len(new_texts)):
            new_texts[i], text_prefix = Wiki.fix_tags_single(text_prefix+new_texts[i])
        return new_texts
    
    @staticmethod
    def textwrap(text: str, limit: int):
        text = text.replace("a href", "a-href")
        texts = textwrap.wrap(text, limit, fix_sentence_endings = False, replace_whitespace = False)
        texts = [text.replace("a-href", "a href") for text in texts]
        return Wiki.fix_tags_multiple(texts)


