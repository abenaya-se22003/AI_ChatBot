from services.embedding_service import create_embedding
from services.db_service import get_connection


# =====================================
# Split text into chunks
# =====================================

def chunk_text(text, chunk_size=500):

    chunks = []

    for i in range(0, len(text), chunk_size):

        chunk = text[i:i + chunk_size]

        chunks.append(chunk)

    return chunks


# =====================================
# Save chunks into PostgreSQL
# =====================================

def save_document_to_db(text):

    chunks = chunk_text(text)

    conn = get_connection()

    cur = conn.cursor()

    for chunk in chunks:

        embedding = create_embedding(chunk)

        cur.execute(
            """
            INSERT INTO documents
            (content, embedding)
            VALUES (%s, %s)
            """,
            (chunk, embedding)
        )

    conn.commit()

    cur.close()
    conn.close()


# =====================================
# Search similar chunks (with scores)
# =====================================

def search_documents_with_scores(query):
    """Search documents and return list of (content, distance) tuples.
    Lower distance = more similar. Cosine distance range: 0 (identical) to 2 (opposite).
    """
    embedding = create_embedding(query)

    conn = get_connection()

    cur = conn.cursor()

    cur.execute(
        """
        SELECT content, embedding <-> %s::vector AS distance
        FROM documents
        ORDER BY distance
        LIMIT 3
        """,
        (embedding,)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [(r[0], r[1]) for r in rows]


def search_documents(query):
    """Backward-compatible: returns only content strings."""
    return [content for content, _ in search_documents_with_scores(query)]