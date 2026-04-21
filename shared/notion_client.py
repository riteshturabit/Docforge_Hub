import os
import logging
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("shared.notion")

# Single shared Notion client for all projects
notion = Client(auth=os.getenv("NOTION_TOKEN"))

# Notion database IDs
DOCS_DB_ID    = os.getenv("NOTION_DB_ID")
TICKETS_DB_ID = os.getenv("NOTION_TICKETS_DB_ID")

logger.info("Shared Notion client initialized")