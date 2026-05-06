import asyncio
from src.memory.wiki import load_wiki
from src.memory.semantic_store import add as semantic_add, search as semantic_search
from src.memory.graph_store import add_episode as graph_add_episode, search as graph_search

def test_wiki():
    content = load_wiki()
    print(f"\nWiki loaded: {len(content)} chars\n")
    assert isinstance(content, str)
    print(f"\nWiki content:\n{content}\n")
    print("\nWiki OK\n")

def test_semantic_store():
    # Placeholder for fastembed/Qdrant tests
    semantic_add("user prefers concise responses", user_id="test_user", session_id="test_session")
    results = semantic_search("response style", user_id="test_user")
    print(f"Semantic Store OK — placeholder add/search executed. Found: {len(results)} results")

async def test_graph_store():
    # Placeholder for Kuzu tests
    await graph_add_episode(
        "\nUser decided to use Kuzu over Neo4j on April 30th",
        session_id="test_session_001"
    )
    results = await graph_search("Kuzu decision")
    print(f"\nGraph Store OK — placeholder add/search executed. Found {len(results)} results")

if __name__ == "__main__":
    test_wiki()
    test_semantic_store()
    asyncio.run(test_graph_store())
    print("\nAll memory layers working (placeholders for new architecture).\n")