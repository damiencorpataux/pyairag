Python wrapper for RAG on Ollama using Postgres.

```sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

docker compose up -d
python test.py
```

From: https://github.com/timescale/private-rag-example