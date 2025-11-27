"""
Test file for MemgraphClient.
Run this script to verify that nodes and relationships are correctly created.
"""
import sys
from pathlib import Path

# Add project root to Python path so we can import from src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.graph_db.memgraph_client import MemgraphClient

def main():
    try:
        # Initialize Memgraph client
        client = MemgraphClient(host="127.0.0.1", port=7687)
    except Exception as e:
        print(f"[ERROR] {e}")
        print("\nTo run this test, you need to have Memgraph running.")
        print("You can start Memgraph using Docker:")
        print("  docker run -it -p 7687:7687 -p 7444:7444 memgraph/memgraph")
        return

    # --- Test Node Creation ---
    entities = [
        {"id": "e1", "label": "Person", "metadata": {"name": "Alice", "role": "Engineer"}},
        {"id": "e2", "label": "Person", "metadata": {"name": "Bob", "role": "CTO"}},
        {"id": "e3", "label": "Company", "metadata": {"name": "DevForge", "location": "Bangalore"}}
    ]

    try:
        for e in entities:
            client.create_entity_node(entity_id=e["id"], label=e["label"], metadata=e["metadata"])
            print(f"Created node: {e['id']} ({e['label']})")
    except ConnectionError as e:
        print(f"[ERROR] {e}")
        print("\nTo run this test, you need to have Memgraph running.")
        print("You can start Memgraph using Docker:")
        print("  docker run -it -p 7687:7687 -p 7444:7444 memgraph/memgraph")
        return

    # --- Test Relationship Creation ---
    relationships = [
        {"start": "e1", "end": "e3", "type": "WORKS_AT", "metadata": {"since": "2022"}},
        {"start": "e2", "end": "e3", "type": "WORKS_AT", "metadata": {"since": "2020"}}
    ]

    try:
        for r in relationships:
            client.create_relationship(
                start_entity_id=r["start"],
                end_entity_id=r["end"],
                rel_type=r["type"],
                metadata=r["metadata"]
            )
            print(f"Created relationship: {r['start']} -[{r['type']}]-> {r['end']}")

        # --- Test Query ---
        query = "MATCH (p:Person)-[r:WORKS_AT]->(c:Company) RETURN p.name, r.since, c.name"
        results = client.run_query(query)
        print("\nQuery Results:")
        for row in results:
            print(row)
    except ConnectionError as e:
        print(f"[ERROR] {e}")
        print("\nTo run this test, you need to have Memgraph running.")
        print("You can start Memgraph using Docker:")
        print("  docker run -it -p 7687:7687 -p 7444:7444 memgraph/memgraph")
        return

    # Close connection
    client.close()


if __name__ == "__main__":
    main()
