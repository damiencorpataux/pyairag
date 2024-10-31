from . import database
from ollama import Client as ollama_Client

# Core config

model_for_query = 'mistral'  # FIXME: 'llama3.2' raises error: ollama._types.ResponseError: error loading model /root/.ollama/models/blobs/...
model_for_embedding = 'nomic-embed-text'
ollama_service = 'http://ollama:11434'  # NOTE: URL to be called from inside container 'timescaledb' !

print('Creating ollama client...')
ollama = ollama_Client(host=ollama_service)  # FIXME: Dev purpose

def setup():
    # FIXME: To be implemented correctly: Automatically execute this on docker image build
    database.execute('CREATE EXTENSION IF NOT EXISTS ai CASCADE;')
    database.execute("""
        DROP TABLE IF EXISTS documents;
    """)
    database.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            title TEXT,
            content TEXT,
            embedding VECTOR(768),
            mimetype TEXT,
            source TEXT,
            created TIMESTAMP DEFAULT now()
        );
    """)

    # FIXME: To be implemented correctly: First, models MUST be pulled using `ollama pull <model>`
    print(f'Pulling models for ollama (takes a while): {model_for_query}, {model_for_embedding}...')
    for partial in ollama.pull(model_for_query, stream=True):
        print(partial)
    for partial in ollama.pull(model_for_embedding, stream=True):
        print(partial)


# Core component

def insert(title, content, mimetype=None, source=None):
    """Insert new RAG content.
    """
    # For now, a RAG data is simply a title and content
    embed_text = f'{title} - {content}'
    rows = database.execute("""
        INSERT INTO documents (title, content, embedding, mimetype, source)
        VALUES (
            %(title)s,
            %(content)s,
            ollama_embed(%(model_for_embedding)s, %(embed_text)s, _host=>%(ollama_service)s),
            %(mimetype)s,
            %(source)s
        )
    """, {
        'title': title,
        'content': content,
        'mimetype': mimetype,
        'source': source,
        'model_for_embedding': model_for_embedding,
        'embed_text': embed_text,
        'ollama_service': ollama_service
    })

def query(query = 'Tell me about gates in South Korea.', context_limit = 3):
    """Return a response generated using RAG content for the given query.
    """
    query_contextualized = contextualize_query(query, limit=context_limit)
    print(f'Querying model "{model_for_query}" with context:\n{'\n'.join(f'> {line}' for line in query_contextualized.splitlines())}')
    # Generate the answer using ollama.chat
    answer = ollama.chat(
        model=model_for_query,
        messages = [{
            "role": "user",
            'content': query_contextualized
        }]
    )
    return answer['message']['content']
    # # FIXME: The following raises an error in PL/Python function ollama_generate()
    # # Generate the response using the ollama_generate function
    # rows = database.execute("""
    #     SELECT ollama_generate(%(model_for_query)s, %(query_contextualized)s, _host=>%(ollama_service)s);
    # """, {
    #     'query_contextualized': query_contextualized,
    #     'model_for_query': model_for_query,
    #     'ollama_service': ollama_service,
    # })
    # model_response = rows[0]
    # return model_response['response']

def contextualize_query(query, limit = 0):
    """Return the given query contextualized with RAG content.
    """
    context = retrieve_context(query, limit=limit)
    query_contextualized = f"Query: {query}\n\nContext:\n\n{context}"
    return query_contextualized

def retrieve_context(query, limit = 3):
    """Return a string containing a context from RAG content.
    """
    print('Retrieving context data...')
    # FIXME: Limit could be relative to overall "score" of retrieved rows
    #   - Implement auto-limit based on similarity score ?
    #     Maybe simply take results with similarity >= 7.0 ?
    rows = database.execute("""
        SELECT
            ollama_embed(
                %(model_for_embedding)s, %(query)s,
                _host=>%(ollama_service)s);
    """, {
        'query': query,
        'model_for_embedding': model_for_embedding,
        'ollama_service': ollama_service,
    })
    query_embedding = rows[0]

    # Retrieve relevant documents based on cosine distance
    limit = limit if limit>0 else 'NULL'
    rows = database.execute(f"""
        SELECT * FROM (
            SELECT
                title,
                content,
                1 - (embedding <=> %(query_embedding)s) AS similarity
            FROM documents
            LIMIT {limit}
        )
        WHERE similarity > %(similarity_min)s
        ORDER BY similarity DESC;
    """, {
        'query_embedding': query_embedding,
        'similarity_min': 0.58  # FIXME: Hardcoded
    })

    for row in rows:
        print(f'{row[2]}: {row[0]}')
        
    # Prepare the context for generating the response
    context = "\n\n".join([f"Title: {row[0]}\nContent: {row[1]}" for row in rows])
    return context

def show():
    """Print RAG content.
    """
    for row in list():
        print(f"Title: {row[0]}, "
              f"Content: {row[1][:30].replace('\n', ' ')}{f'(...{len(row[1])} chars)' if len(row[1])>30 else ''}, "
              f"Embedding Dimensions: {row[2]}")

def list():
    """Return a list of RAG content.
    """
    rows = database.execute("""
        SELECT title, content, vector_dims(embedding) 
        FROM documents;
    """)
    return rows

def clear():
    """Clear stored RAG content.
    """
    rows = database.execute("""
        DELETE FROM documents;
    """)
    return rows

# FIXME: For sandbox
def import_dummy_data():
    data = [
        {"source": "dummy", "title": "Seoul Tower", "content": "Seoul Tower is a communication and observation tower located on Namsan Mountain in central Seoul, South Korea."},
        {"source": "dummy", "title": "Gwanghwamun Gate", "content": "Gwanghwamun is the main and largest gate of Gyeongbokgung Palace, in Jongno-gu, Seoul, South Korea."},
        {"source": "dummy", "title": "Bukchon Hanok Village", "content": "Bukchon Hanok Village is a Korean traditional village in Seoul with a long history."},
        {"source": "dummy", "title": "Myeong-dong Shopping Street", "content": "Myeong-dong is one of the primary shopping districts in Seoul, South Korea."},
        {"source": "dummy", "title": "Dongdaemun Design Plaza", "content": "The Dongdaemun Design Plaza is a major urban development landmark in Seoul, South Korea."}
    ]
    if len(list()):
        raise AssertionError('Database is not empty')
    for item in data:
        print(f'Importing dummy data: {item}')
        insert(item['title'], item['content'])
