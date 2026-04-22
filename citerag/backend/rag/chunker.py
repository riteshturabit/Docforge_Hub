import logging
from notion_client import Client
from shared.notion_client import notion
from citerag.backend.utils.text_utils import (
    clean_notion_text,
    truncate_text
)
from citerag.backend.constants import CHUNK_SIZE

logger = logging.getLogger("citerag.chunker")


def get_notion_pages(database_id: str) -> list:
    """
    Fetch all pages from Notion database
    Compatible with notion-client 3.0.0
    """
    try:
        pages     = []
        cursor    = None
        clean_db  = database_id.replace("-", "")

        while True:
            kwargs = {
                "filter":    {"value": "page", "property": "object"},
                "page_size": 100
            }
            if cursor:
                kwargs["start_cursor"] = cursor

            response = notion.search(**kwargs)
            results  = response.get("results", [])

            for page in results:
                parent   = page.get("parent", {})
                # Check database_id directly in parent
                # regardless of parent type
                page_db  = parent.get(
                    "database_id", ""
                ).replace("-", "")

                if page_db == clean_db:
                    pages.append(page)

            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")

        logger.info(
            f"Fetched {len(pages)} pages | "
            f"db={database_id}"
        )
        return pages

    except Exception as e:
        logger.error(f"Notion fetch failed | {e}")
        raise


def extract_page_metadata(page: dict) -> dict:
    """
    Extract metadata from Notion page properties
    Returns industry, doc_type, version
    """
    props    = page.get("properties", {})
    metadata = {}

    # Extract industry
    ind_prop = props.get("Industry", {})
    if ind_prop.get("select"):
        metadata["industry"] = ind_prop["select"].get("name", "")

    # Extract document type
    type_prop = props.get("Type", {})
    if type_prop.get("select"):
        metadata["doc_type"] = type_prop["select"].get("name", "")

    # Extract version
    ver_prop = props.get("Version", {})
    if ver_prop.get("rich_text"):
        metadata["version"] = (
            ver_prop["rich_text"][0]["plain_text"]
            if ver_prop["rich_text"] else "v1.0"
        )

    # Extract title
    name_prop = props.get("Name", {})
    if name_prop.get("title"):
        metadata["doc_title"] = (
            name_prop["title"][0]["plain_text"]
            if name_prop["title"] else "Untitled"
        )

    return metadata


def extract_page_content(page_id: str) -> list:
    """
    Extract all blocks from a Notion page
    Handles pagination for long pages
    """
    try:
        blocks = []
        cursor = None

        while True:
            kwargs = {"block_id": page_id}
            if cursor:
                kwargs["start_cursor"] = cursor

            response = notion.blocks.children.list(**kwargs)
            blocks.extend(response["results"])

            if not response["has_more"]:
                break
            cursor = response["next_cursor"]

        logger.debug(f"Extracted {len(blocks)} blocks | page={page_id}")
        return blocks

    except Exception as e:
        logger.error(f"Block extraction failed | page={page_id} | {e}")
        return []


def extract_text_from_block(block: dict) -> str:
    """
    Extract plain text from any Notion block type
    Handles paragraph, heading, bullet, table etc
    """
    block_type = block.get("type", "")
    text       = ""

    if block_type in ["paragraph",
                      "heading_1",
                      "heading_2",
                      "heading_3"]:
        rich_text = block.get(block_type, {}).get("rich_text", [])
        text = "".join([t.get("plain_text", "") for t in rich_text])

    elif block_type == "bulleted_list_item":
        rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
        text = "• " + "".join([t.get("plain_text", "") for t in rich_text])

    elif block_type == "numbered_list_item":
        rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
        text = "".join([t.get("plain_text", "") for t in rich_text])

    elif block_type == "table_row":
        cells = block.get("table_row", {}).get("cells", [])
        cell_texts = []
        for cell in cells:
            cell_text = "".join([t.get("plain_text", "") for t in cell])
            cell_texts.append(cell_text)
        text = " | ".join(cell_texts)

    elif block_type == "quote":
        rich_text = block.get("quote", {}).get("rich_text", [])
        text = "".join([t.get("plain_text", "") for t in rich_text])

    return clean_notion_text(text)


def blocks_to_chunks(
    blocks:    list,
    page_id:   str,
    metadata:  dict,
    chunk_size: int = CHUNK_SIZE
) -> list:
    """
    Convert Notion page blocks into text chunks
    Each chunk preserves stable citation info:
    → notion_page_id + section_title

    Chunking strategy:
    → New section heading → save current chunk → start new
    → Text exceeds chunk_size → save → start new
    → End of blocks → save remaining text
    """
    chunks          = []
    current_section = "Introduction"
    current_text    = ""
    chunk_index     = 0
    doc_title       = metadata.get("doc_title", "Untitled")

    def save_chunk():
        nonlocal chunk_index, current_text
        text = current_text.strip()
        if text:
            chunks.append({
                "notion_page_id": page_id,
                "doc_title":      doc_title,
                "section_title":  current_section,
                "chunk_text":     text,
                "chunk_index":    chunk_index,
                "industry":       metadata.get("industry", ""),
                "doc_type":       metadata.get("doc_type", ""),
                "version":        metadata.get("version", "v1.0"),
            })
            chunk_index  += 1
            current_text  = ""

    for block in blocks:
        block_type = block.get("type", "")

        # New section → save current chunk
        if block_type in ["heading_1", "heading_2", "heading_3"]:
            save_chunk()
            rich_text       = block.get(block_type, {}).get("rich_text", [])
            current_section = "".join(
                [t.get("plain_text", "") for t in rich_text]
            )
            continue

        text = extract_text_from_block(block)
        if not text:
            continue

        current_text += text + "\n"

        # Chunk too big so save and start new
        if len(current_text) >= chunk_size:
            save_chunk()

    # Save last remaining chunk
    save_chunk()

    logger.info(
        f"Chunked | doc={doc_title} | "
        f"chunks={len(chunks)} | page={page_id}"
    )
    return chunks