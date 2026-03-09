from utils.db import fetchall, execute_returning


def get_comments(ticket_id: int) -> list:
    """Get all comments for a ticket ordered by time."""
    return fetchall("""
        SELECT * FROM ticket_comments
        WHERE ticket_id = %s
        ORDER BY created_at ASC
    """, (ticket_id,))


def add_comment(ticket_id: int, author_name: str, author_role: str, message: str):
    """Add a comment to a ticket."""
    return execute_returning("""
        INSERT INTO ticket_comments (ticket_id, author_name, author_role, message)
        VALUES (%s, %s, %s, %s)
        RETURNING id, created_at
    """, (ticket_id, author_name, author_role, message))
