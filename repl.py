# FIXME
import airag.core as rag
import airag.scrap.http as scrap

print("""
* Start with command:

rag.setup()


* And try:

doc = scrap.browse('http://example.com/')
print(doc)
rag.insert(**doc)
rag.show()

""")