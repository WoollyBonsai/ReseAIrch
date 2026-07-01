import os
import uuid
import chromadb
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server for Memory
mcp = FastMCP("ReseAIrch-Memory")

# Initialize ChromaDB client (persistent storage in workspace/chroma)
db_path = os.path.join(os.getcwd(), "workspace", "chroma")
os.makedirs(db_path, exist_ok=True)
client = chromadb.PersistentClient(path=db_path)

@mcp.tool()
def store_document(collection_name: str, content: str, source_url: str = "") -> str:
    """
    Stores a scraped document (raw text or markdown) into the vector database.
    
    Args:
        collection_name: Name of the project or specific research topic.
        content: The text content to store.
        source_url: The URL where the content was scraped from.
    """
    try:
        collection = client.get_or_create_collection(name=collection_name)
        doc_id = str(uuid.uuid4())
        
        # In a production long-run, we chunk this text. 
        # For this tool, we assume the agent or another skill handles chunking,
        # or we store it directly if it's within embedding limits.
        
        # Simple chunking to prevent embedding crash on massive texts
        max_length = 5000 
        chunks = [content[i:i+max_length] for i in range(0, len(content), max_length)]
        
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": source_url, "chunk": i} for i in range(len(chunks))]
        
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        return f"Successfully stored document in {collection_name} across {len(chunks)} chunks."
    except Exception as e:
        return f"Error storing document: {str(e)}"

@mcp.tool()
def query_memory(collection_name: str, query: str, n_results: int = 5) -> str:
    """
    Queries the vector database for relevant information based on the query.
    
    Args:
        collection_name: Name of the project or specific research topic.
        query: The question or context to search for.
        n_results: Number of relevant chunks to return.
    """
    try:
        collection = client.get_collection(name=collection_name)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results['documents'] or not results['documents'][0]:
            return "No relevant information found in memory."
            
        formatted_results = []
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            source = meta.get("source", "Unknown")
            formatted_results.append(f"Source: {source}\nExcerpt:\n{doc}\n---")
            
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Error querying memory: {str(e)}"

if __name__ == "__main__":
    print("Starting ReseAIrch-Memory MCP Server...", flush=True)
    mcp.run()
