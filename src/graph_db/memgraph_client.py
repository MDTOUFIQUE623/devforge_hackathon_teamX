"""
Memgraph Graph DB client using gqlalchemy (works on Windows + Python 3.13)
Supports:
- Creating nodes for entities
- Creating relationships between nodes
- Storing metadata as node/edge properties
"""

from typing import Dict, List, Optional, Any
from gqlalchemy import Memgraph
from gqlalchemy.exceptions import GQLAlchemyWaitForConnectionError
import json


class MemgraphClient:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7687,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize connection to Memgraph using gqlalchemy.
        """
        try:
            self.memgraph = Memgraph(
                host=host,
                port=port,
                username=username or "",
                password=password or ""
            )
        except (GQLAlchemyWaitForConnectionError, Exception) as e:
            raise ConnectionError(
                f"Failed to connect to Memgraph at {host}:{port}. "
                f"Make sure Memgraph is running. Error: {e}"
            )

    # -------------------- NODE OPERATIONS --------------------
    def create_entity_node(self, entity_id: str, label: str, metadata: Dict[str, Any]):
        """
        Create a node representing an entity.

        Args:
            entity_id: Unique ID of entity
            label: Label/type of entity (e.g., Person, Company)
            metadata: Dictionary of additional properties
        """
        try:
            # Build properties string with proper escaping
            props_list = [f"id: '{entity_id}'"]
            for k, v in metadata.items():
                # Escape single quotes in string values
                if isinstance(v, str):
                    escaped_value = v.replace("'", "\\'")
                    props_list.append(f"{k}: '{escaped_value}'")
                else:
                    # For non-string values, use JSON representation
                    props_list.append(f"{k}: {json.dumps(v)}")
            
            props_str = ", ".join(props_list)
            query = f"""
            MERGE (n:{label} {{{props_str}}})
            """
            self.memgraph.execute(query)
        except (GQLAlchemyWaitForConnectionError, Exception) as e:
            raise ConnectionError(
                f"Failed to execute query. Make sure Memgraph is running. Error: {e}"
            )

    # -------------------- RELATIONSHIP OPERATIONS --------------------
    def create_relationship(
        self,
        start_entity_id: str,
        end_entity_id: str,
        rel_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create a relationship between two nodes.

        Args:
            start_entity_id: ID of the start node
            end_entity_id: ID of the end node
            rel_type: Relationship type (string)
            metadata: Optional dict for relationship properties
        """
        try:
            props_str = ""
            if metadata:
                props_list = []
                for k, v in metadata.items():
                    # Escape single quotes in string values
                    if isinstance(v, str):
                        escaped_value = v.replace("'", "\\'")
                        props_list.append(f"{k}: '{escaped_value}'")
                    else:
                        # For non-string values, use JSON representation
                        props_list.append(f"{k}: {json.dumps(v)}")
                props_str = "{" + ", ".join(props_list) + "}"

            query = f"""
            MATCH (a {{id: '{start_entity_id}'}}), (b {{id: '{end_entity_id}'}})
            MERGE (a)-[r:{rel_type} {props_str}]->(b)
            """
            self.memgraph.execute(query)
        except (GQLAlchemyWaitForConnectionError, Exception) as e:
            raise ConnectionError(
                f"Failed to execute query. Make sure Memgraph is running. Error: {e}"
            )

    # -------------------- QUERY --------------------
    def run_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute arbitrary Cypher query and return results as list of dicts.
        """
        try:
            result = self.memgraph.execute_and_fetch(query)
            # Convert results to list of dicts
            # gqlalchemy returns Record objects that can be converted to dicts
            results = []
            for record in result:
                if hasattr(record, 'items'):
                    results.append(dict(record.items()))
                else:
                    # Fallback: try to convert to dict
                    results.append(dict(record))
            return results
        except (GQLAlchemyWaitForConnectionError, Exception) as e:
            raise ConnectionError(
                f"Failed to execute query. Make sure Memgraph is running. Error: {e}"
            )

    def close(self):
        """
        Close connection. gqlalchemy uses HTTP under the hood, so explicit close not required.
        """
        pass
