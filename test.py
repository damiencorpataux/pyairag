# First, do `docker compose up`

import airag.core as rag

rag.setup()
rag.import_dummy_data()

response = rag.query('Tell me about gates in South Korea.')
print(response)