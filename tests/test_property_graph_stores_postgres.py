import os
import tempfile
from unittest import TestCase, SkipTest, mock

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
        
    @mock.patch("llama_index.graph_stores.postgres.property_graph.NETWORKX_AVAILABLE", True)
    @mock.patch("llama_index.graph_stores.postgres.property_graph.nx")
    @mock.patch("llama_index.graph_stores.postgres.property_graph.plt")
    def test_save_networkx_graph(self, mock_plt, mock_nx):
        # Setup mock for NetworkX
        mock_graph = mock.MagicMock()
        mock_nx.DiGraph.return_value = mock_graph
        mock_nx.spring_layout.return_value = {}
        
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.png') as temp_file:
            output_name = temp_file.name[:-4]  # Remove .png extension
            
            # Create graph store and add test data
            g = get_store()
            g.upsert_nodes([self.e1, self.e2])
            g.upsert_relations([self.r])
            
            # Call the method
            g.save_networkx_graph(output_name)
            
            # Verify the graph was created with the correct nodes and edges
            mock_nx.DiGraph.assert_called_once()
            
            # Verify that nodes were added to the graph
            self.assertEqual(mock_graph.add_node.call_count, 2)
            
            # Verify that edges were added to the graph
            mock_graph.add_edge.assert_called_once()
            
            # Verify that the plot was saved
            mock_plt.savefig.assert_called_once()
            
    def test_save_networkx_graph_import_error(self):
        # Test the case where NetworkX is not available
        with mock.patch("llama_index.graph_stores.postgres.property_graph.NETWORKX_AVAILABLE", False):
            g = get_store()
            with self.assertRaises(ImportError):
                g.save_networkx_graph("test_graph")
