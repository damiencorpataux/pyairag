from . import database
import ollama

# Core config

model_for_query = 'llama3.2'
model_for_embedding = 'nomic-embed-text'
ollama_service = 'http://ollama:11434'  # NOTE: URL to be called from inside container 'timescaledb' !


# FIXME: Changing config for dev environment purpose
database.config = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres',
    'port': '5433'  # Non-standard port !
}

def setup():
    # FIXME: To be implemented correctly: Automatically execute this on docker image build
    database.execute('CREATE EXTENSION IF NOT EXISTS ai CASCADE;')
    database.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            title TEXT,
            content TEXT,
            embedding VECTOR(768)
        );
    """)

    # FIXME: To be implemented correctly: First, models MUST be pulled using `ollama pull <model>`
    print(f'Pulling models for ollama (takes a while): {model_for_query}, {model_for_embedding}...')
    ollama_client = ollama.Client(host='http://localhost:11435')  # FIXME: Dev purpose
    print(ollama_client.pull(model_for_query))
    print(ollama_client.pull(model_for_embedding))


# Core component

def insert(title, content):
    """Insert new RAG contents.
    """
    # For now, a RAG data is simply a title and content
    embed_text = f'{title} - {content}'
    rows = database.execute("""
        INSERT INTO documents (title, content, embedding)
        VALUES (
            %(title)s,
            %(content)s,
            ollama_embed(%(model_for_embedding)s, %(embed_text)s, _host=>%(ollama_service)s)
        )
    """, {
        'title': title,
        'content': content,
        'model_for_embedding': model_for_embedding,
        'embed_text': embed_text,
        'ollama_service': ollama_service
    })

def query(query = 'Tell me about gates in South Korea.', context_limit = 3):
    """Return a response generated using RAG contents for the given query.
    """
    query_contextualized = contextualize_query(query, limit=context_limit)
    print(f'Querying model "{model_for_query}" with context:\n{'\n'.join(f'> {line}' for line in query_contextualized.splitlines())}')
    # Generate the answer using ollama
    answer = ollama.chat(
        # model="mistral",
        model=model_for_query,
        messages = [{
            "role": "user",
            'content': query_contextualized
        }]
    )
    return answer['message']['content']
    # FIXME: The following raises an error in PL/Python function ollama_generate()
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
    """Return the given query contextualized with RAG contents.
    """
    context = retrieve_context(query, limit=limit)
    query_contextualized = f"Query: {query}\n\nContext:\n\n{context}"
    return query_contextualized

def retrieve_context(query, limit = 3):
    """Return a string containing a context from RAG contents.
    """
    print('Retrieving context data...')
    # FIXME: Limit could be relative to overall "score" of retrieved rows
    #   - Implement auto-limit based on similarity score ?
    #     Maybe simply take results with similarity >= 7.0 ?
    rows = database.execute("""
        SELECT ollama_embed(%(model_for_embedding)s, %(query)s, _host=>%(ollama_service)s);
    """, {
        'query': query,
        'model_for_embedding': model_for_embedding,
        'ollama_service': ollama_service,
    })
    query_embedding = rows[0]

    # Retrieve relevant documents based on cosine distance
    limit = limit if limit>0 else 'NULL'
    rows = database.execute(f"""
        SELECT title, content, 1 - (embedding <=> %s) AS similarity
        FROM documents
        ORDER BY similarity DESC
        LIMIT {limit};
    """, (query_embedding,))

    for row in rows:
        print(f'{row[2]}: {row[0]}')
        
    # Prepare the context for generating the response
    context = "\n\n".join([f"Title: {row[0]}\nContent: {row[1]}" for row in rows])
    return context

def show():
    """Print RAG contents.
    """
    for row in list():
        print(f"Title: {row[0]}, Content: {row[1]}, Embedding Dimensions: {row[2]}")

def list():
    """Return a list of RAG contents.
    """
    rows = database.execute("""
        SELECT title, content, vector_dims(embedding) 
        FROM documents;
    """)
    return rows

def clear():
    """Clear stored RAG contents.
    """
    rows = database.execute("""
        DELETE FROM documents;
    """)
    return rows

# FIXME: For sandbox
def import_dummy_data():
    data = [
        {"title": "Seoul Tower", "content": "Seoul Tower is a communication and observation tower located on Namsan Mountain in central Seoul, South Korea."},
        {"title": "Gwanghwamun Gate", "content": "Gwanghwamun is the main and largest gate of Gyeongbokgung Palace, in Jongno-gu, Seoul, South Korea."},
        {"title": "Bukchon Hanok Village", "content": "Bukchon Hanok Village is a Korean traditional village in Seoul with a long history."},
        {"title": "Myeong-dong Shopping Street", "content": "Myeong-dong is one of the primary shopping districts in Seoul, South Korea."},
        {"title": "Dongdaemun Design Plaza", "content": "The Dongdaemun Design Plaza is a major urban development landmark in Seoul, South Korea."}
    ]
    if len(list()):
        raise AssertionError('Database is not empty')
    for item in data:
        print(f'Importing dummy data: {item}')
        insert(item['title'], item['content'])
