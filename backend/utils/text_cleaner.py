import re
import logging

logger = logging.getLogger("docforge.utils.text_cleaner")


def clean_content(text: str) -> str:
    """
    Cleans raw LLM output into professional document content.
    Removes markdown symbols, normalizes bullets,
    collapses blank lines and formats pipe tables.
    """
    # Remove markdown headers like ## or ###
    text = re.sub(r'#{1,6}\s*', '', text)

    # Convert lone * bullet to • symbol
    text = re.sub(
        r'(?<!\*)\*(?!\*)(?!\*)\s+', '• ',
        text,
        flags=re.MULTILINE
    )

    # Remove **bold** and *italic* markers but keep text
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)

    # Remove __underline__ markers but keep text
    text = re.sub(r'_{1,3}(.*?)_{1,3}', r'\1', text)

    # Remove markdown table separator rows like |---|---|
    text = re.sub(r'\|[-:\s|]+\|', '', text)

    # Format pipe table rows into readable format
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        if line.strip().startswith('|') and line.strip().endswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            cells = [c for c in cells if c]
            cleaned.append('  |  '.join(cells))
        else:
            cleaned.append(line)
    text = '\n'.join(cleaned)

    # Convert remaining * bullets to • symbol
    text = re.sub(r'^\s*[*]\s+', '• ', text, flags=re.MULTILINE)

    # Collapse 3+ blank lines to double blank line
    text = re.sub(r'\n{3,}', '\n\n', text)

    logger.debug("Content cleaned successfully")
    return text.strip()