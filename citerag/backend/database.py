from shared.database import get_connection, release_connection

# Re-export for citerag usage
__all__ = ["get_connection", "release_connection"]