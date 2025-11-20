"""Check what's in the ChromaDB"""
import sys
sys.path.insert(0, '/var/www/hcsbot/backend')

from vector_db import VectorDatabase

db = VectorDatabase()
total = db.collection.count()

print(f"\nTotal documents in ChromaDB: {total}")

# Check if there are any web articles
results = db.collection.get(limit=10)

web_count = 0
pdf_count = 0

# Sample first 100 to check
sample = db.collection.get(limit=100)
for metadata in sample['metadatas']:
    if 'source_type' in metadata and metadata['source_type'] == 'web':
        web_count += 1
    else:
        pdf_count += 1

print(f"In sample of 100:")
print(f"  - Web articles: {web_count}")
print(f"  - PDF documents: {pdf_count}")

# Show a web article if found
if web_count > 0:
    print("\nSample web article metadata:")
    for i, metadata in enumerate(sample['metadatas']):
        if 'source_type' in metadata and metadata['source_type'] == 'web':
            print(f"  {metadata}")
            break
