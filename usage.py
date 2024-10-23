# First, do `docker compose up`

import airag.core as rag
import airag.scrap.http as scrap 

rag.setup()
rag.clear()
rag.import_dummy_data()
rag.show()

doc = scrap.browse('http://example.com/')
print(doc)
rag.insert(**doc)
rag.show()

query = 'Tell me about gates in South Korea.'
response = rag.query(query, context_limit=3)
print('\n---\n')
print(response)