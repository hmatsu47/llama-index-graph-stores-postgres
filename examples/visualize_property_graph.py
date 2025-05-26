"""
Example script demonstrating how to visualize a PostgreSQL property graph.

This script:
1. Creates a PostgreSQL property graph store
2. Adds some sample nodes and relations
3. Visualizes the graph and saves it as an image

Requirements:
- PostgreSQL with pgvector extension
- NetworkX and Matplotlib libraries

Usage:
- Set the POSTGRES_CONNECTION_STRING environment variable to your PostgreSQL connection string
- Run the script: python visualize_property_graph.py
"""

import os
from llama_index.core.graph_stores.types import EntityNode, Relation
from llama_index.graph_stores.postgres import PostgresPropertyGraphStore

# Get PostgreSQL connection string from environment variable
db_connection_string = os.environ.get(
    "POSTGRES_CONNECTION_STRING", 
    "postgresql://postgres:postgres@localhost:5432/postgres"
)

# Create a PostgreSQL property graph store
graph_store = PostgresPropertyGraphStore(
    db_connection_string=db_connection_string,
    drop_existing_table=True,  # Warning: This will drop existing tables
    node_table_name="example_nodes",
    relation_table_name="example_relations",
)

# Create some sample nodes
nodes = [
    EntityNode(name="Alice", label="Person", properties={"age": "30", "occupation": "Engineer"}),
    EntityNode(name="Bob", label="Person", properties={"age": "28", "occupation": "Designer"}),
    EntityNode(name="Charlie", label="Person", properties={"age": "35", "occupation": "Manager"}),
    EntityNode(name="Project X", label="Project", properties={"status": "Active", "priority": "High"}),
    EntityNode(name="Project Y", label="Project", properties={"status": "Planning", "priority": "Medium"}),
]

# Create some sample relations
relations = [
    Relation(label="WORKS_ON", source_id=nodes[0].id, target_id=nodes[3].id, properties={"role": "Lead"}),
    Relation(label="WORKS_ON", source_id=nodes[1].id, target_id=nodes[3].id, properties={"role": "Member"}),
    Relation(label="WORKS_ON", source_id=nodes[1].id, target_id=nodes[4].id, properties={"role": "Lead"}),
    Relation(label="WORKS_ON", source_id=nodes[2].id, target_id=nodes[4].id, properties={"role": "Supervisor"}),
    Relation(label="MANAGES", source_id=nodes[2].id, target_id=nodes[0].id),
    Relation(label="MANAGES", source_id=nodes[2].id, target_id=nodes[1].id),
    Relation(label="FRIENDS_WITH", source_id=nodes[0].id, target_id=nodes[1].id),
]

# Add nodes and relations to the graph store
print("Adding nodes and relations to the graph store...")
graph_store.upsert_nodes(nodes)
graph_store.upsert_relations(relations)

# Visualize the graph and save it as an image
print("Generating graph visualization...")
try:
    graph_store.save_networkx_graph("property_graph_visualization")
    print("Graph visualization saved successfully!")
except ImportError as e:
    print(f"Error: {e}")
    print("Please install the required libraries with: pip install networkx matplotlib")