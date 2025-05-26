import os
import tempfile
from unittest import TestCase, SkipTest
from pathlib import Path

from llama_index.core.graph_stores.types import (
    EntityNode,
    Relation,
)

from llama_index.graph_stores.postgres import PostgresPropertyGraphStore


def get_store():
    return PostgresPropertyGraphStore(
        db_connection_string=os.environ.get("POSTGRES_TEST_CONNECTION_STRING"),
        drop_existing_table=True,
        relation_table_name="test_relations",
        node_table_name="test_nodes",
    )


class TestPostgresPropertyGraphStore(TestCase):
    @classmethod
    def setUp(self) -> None:
        try:
            get_store()
        except Exception:
            raise SkipTest("PostgreSQL database is not available")

        self.e1 = EntityNode(name="e1", properties={"p1": "v1"})
        self.e2 = EntityNode(name="e2")
        self.r = Relation(label="r", source_id=self.e1.id, target_id=self.e2.id)

    def test_add(self):
        g = get_store()

        g.upsert_nodes([self.e1, self.e2])
        g.upsert_relations([self.r])
        assert len(g.get_triplets(entity_names=["e1"])) == 1
        assert len(g.get_triplets(entity_names=["e3"])) == 0
        assert len(g.get_triplets(properties={"p1": "v1"})) == 1
        assert len(g.get_triplets(properties={"p1": "v2"})) == 0

    def test_delete_by_entity_names(self):
        g = get_store()

        g.upsert_nodes([self.e1, self.e2])
        g.upsert_relations([self.r])
        assert len(g.get_triplets(entity_names=["e1"])) == 1
        g.delete(entity_names=["e1"])
        assert len(g.get_triplets(entity_names=["e1"])) == 0

    def test_delete_by_entity_properties(self):
        g = get_store()

        g.upsert_nodes([self.e1, self.e2])
        g.upsert_relations([self.r])
        assert len(g.get_triplets(entity_names=["e1"])) == 1
        g.delete(properties={"p1": "not exist"})
        assert len(g.get_triplets(entity_names=["e1"])) == 1
        g.delete(properties={"p1": "v1"})
        assert len(g.get_triplets(entity_names=["e1"])) == 0

    def test_get(self):
        g = get_store()

        g.upsert_nodes([self.e1, self.e2])
        assert len(g.get(ids=[self.e1.id])) == 1
        assert len(g.get(ids=[self.e1.id, self.e2.id])) == 2
        assert len(g.get(properties={"p1": "v1"})) == 1
        
    def test_save_networkx_graph(self):
        g = get_store()
        
        # Add some test nodes and relations
        e1 = EntityNode(name="entity1", label="person", properties={"age": 30})
        e2 = EntityNode(name="entity2", label="company", properties={"founded": 2010})
        e3 = EntityNode(name="entity3", label="person", properties={"age": 25})
        
        r1 = Relation(label="works_at", source_id=e1.id, target_id=e2.id, properties={"since": 2015})
        r2 = Relation(label="knows", source_id=e1.id, target_id=e3.id, properties={"since": 2018})
        
        g.upsert_nodes([e1, e2, e3])
        g.upsert_relations([r1, r2])
        
        # Create a temporary file for the graph visualization
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Save the graph visualization
            g.save_networkx_graph(tmp_path)
            
            # Check if the file was created and has content
            path = Path(tmp_path)
            assert path.exists()
            assert path.stat().st_size > 0
            
            # Basic check for HTML content
            with open(tmp_path, "r") as f:
                content = f.read()
                assert "<html>" in content
                assert "vis-network" in content
                
                # Check for node and edge data
                assert "entity1" in content
                assert "entity2" in content
                assert "entity3" in content
                assert "works_at" in content
                assert "knows" in content
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
