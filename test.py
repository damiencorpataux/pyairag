# First, do `docker compose up`

import airag.core as rag

rag.setup()
rag.clear()
rag.import_dummy_data()

query = 'Tell me about gates in South Korea.'
response = rag.query(query, context_limit=3)
print('\n---\n')
print(response)