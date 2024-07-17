import logging
import textwrap

from telegram import (
    Update,
)
from telegram.constants import (
    MessageLimit
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PicklePersistence,
    Defaults,
)

from wiki import Wiki
from os import getenv

__import__("dotenv").load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs.log")
    ]
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

TOKEN = getenv("TOKEN")

wiki = Wiki("https://deeprockgalactic.wiki.gg")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Start"
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            "Syntax: /search <something>"
        )
        return
    results = await wiki.search(" ".join(context.args))
    if not results:
        await update.effective_message.reply_text(
            "No results found :/"
        )
        return
    
    content = await wiki.get_page_content(list(results.values())[0])

    texts = textwrap.wrap(content["parsed_content"], MessageLimit.MAX_TEXT_LENGTH, fix_sentence_endings = False, replace_whitespace = False)

    if len(texts) > 1:
        texts = Wiki.fix_tags_multiple(texts)

    for text in texts:
        await update.effective_message.reply_text(
            text
        )
    

def main():
    application = (
        Application
        .builder()
        .token(TOKEN)
        .persistence(PicklePersistence("persistence.pickle"))
        .defaults(
            Defaults(
                parse_mode="HTML"
            )
        ).concurrent_updates(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))


    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
