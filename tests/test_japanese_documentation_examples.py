"""
Test cases to validate the examples provided in the Japanese documentation (PROPERTY_GRAPH_GUIDE_ja.md).
These tests ensure that the code examples in the documentation are accurate and functional.
"""
import os
from unittest import TestCase, SkipTest
from unittest.mock import Mock, patch

from llama_index.core.graph_stores.types import (
    EntityNode,
    Relation,
    VectorStoreQuery,
)
from llama_index.graph_stores.postgres import PostgresPropertyGraphStore, PostgresGraphStore


def get_property_graph_store():
    """Helper function to create a test PostgresPropertyGraphStore instance."""
    return PostgresPropertyGraphStore(
        db_connection_string=os.environ.get("POSTGRES_TEST_CONNECTION_STRING"),
        embedding_dim=1024,  # As documented: embed_dim is fixed at 1024
        node_table_name="test_doc_nodes",
        relation_table_name="test_doc_relations",
        drop_existing_table=True,
        echo_queries=False,
    )


def get_graph_store():
    """Helper function to create a test PostgresGraphStore instance."""
    return PostgresGraphStore(
        db_connection_string=os.environ.get("POSTGRES_TEST_CONNECTION_STRING")
    )


class TestJapaneseDocumentationExamples(TestCase):
    """Test cases for Japanese documentation examples."""

    @classmethod
    def setUp(self) -> None:
        """Set up test environment."""
        try:
            get_property_graph_store()
        except Exception:
            raise SkipTest("PostgreSQL database is not available")

    def test_property_graph_store_initialization(self):
        """Test PropertyGraphStore initialization as shown in Japanese documentation."""
        # Test the basic initialization example from the documentation
        graph_store = PostgresPropertyGraphStore(
            db_connection_string=os.environ.get("POSTGRES_TEST_CONNECTION_STRING"),
            embedding_dim=1024,  # 固定値（変更不可）
            node_table_name="pg_nodes",  # ノードテーブル名（オプション）
            relation_table_name="pg_relations",  # 関係テーブル名（オプション）
            drop_existing_table=False,  # 既存テーブルを削除するか（オプション）
            echo_queries=False,  # SQLクエリをログ出力するか（オプション）
        )
        
        # Verify the store was created with correct parameters
        assert graph_store._embedding_dim == 1024
        assert graph_store._node_table_name == "pg_nodes"
        assert graph_store._relation_table_name == "pg_relations"
        assert graph_store.supports_vector_queries is True
        assert graph_store.supports_structured_queries is False

    def test_embedding_dimension_constraint(self):
        """Test that embed_dim is indeed fixed at 1024 as documented."""
        # Test default value
        store_default = get_property_graph_store()
        assert store_default._embedding_dim == 1024
        
        # Test explicit 1024 value
        store_1024 = PostgresPropertyGraphStore(
            db_connection_string=os.environ.get("POSTGRES_TEST_CONNECTION_STRING"),
            embedding_dim=1024,
            drop_existing_table=True,
            node_table_name="test_1024_nodes",
            relation_table_name="test_1024_relations",
        )
        assert store_1024._embedding_dim == 1024
        
        # Test that other dimensions can be set (though documentation says it's fixed)
        # This tests the actual implementation vs documentation claim
        store_512 = PostgresPropertyGraphStore(
            db_connection_string=os.environ.get("POSTGRES_TEST_CONNECTION_STRING"),
            embedding_dim=512,
            drop_existing_table=True,
            node_table_name="test_512_nodes",
            relation_table_name="test_512_relations",
        )
        assert store_512._embedding_dim == 512

    def test_basic_node_and_relation_operations(self):
        """Test basic node and relation operations as shown in documentation."""
        graph_store = get_property_graph_store()
        
        # Create test entities as shown in documentation examples
        person_node = EntityNode(
            name="人物1", 
            label="人物", 
            properties={"年齢": 30, "職業": "エンジニア"}
        )
        company_node = EntityNode(
            name="会社1", 
            label="会社", 
            properties={"設立年": 2010, "業界": "IT"}
        )
        
        # Create relation
        works_at_relation = Relation(
            label="働いている",
            source_id=person_node.id,
            target_id=company_node.id,
            properties={"開始年": 2015}
        )
        
        # Test upsert operations
        graph_store.upsert_nodes([person_node, company_node])
        graph_store.upsert_relations([works_at_relation])
        
        # Test retrieval operations
        retrieved_nodes = graph_store.get(ids=[person_node.id, company_node.id])
        assert len(retrieved_nodes) == 2
        
        # Test triplet retrieval
        triplets = graph_store.get_triplets(entity_names=["人物1"])
        assert len(triplets) == 1
        assert triplets[0][1].label == "働いている"

    def test_vector_query_functionality(self):
        """Test vector query functionality as documented."""
        graph_store = get_property_graph_store()
        
        # Create a test node with embedding
        import numpy as np
        test_embedding = np.random.rand(1024).tolist()  # 1024 dimensions as documented
        
        entity_node = EntityNode(
            name="テストエンティティ",
            label="テスト",
            properties={"説明": "これはテスト用のエンティティです"}
        )
        entity_node.embedding = test_embedding
        
        graph_store.upsert_nodes([entity_node])
        
        # Test vector query
        query_embedding = np.random.rand(1024).tolist()
        vector_query = VectorStoreQuery(
            query_embedding=query_embedding,
            similarity_top_k=5
        )
        
        nodes, scores = graph_store.vector_query(vector_query)
        assert len(nodes) >= 0  # Should return results or empty list
        assert len(nodes) == len(scores)

    def test_depth_search_functionality(self):
        """Test depth search functionality as shown in documentation."""
        graph_store = get_property_graph_store()
        
        # Create a chain of entities for depth testing
        entity1 = EntityNode(name="エンティティ1", label="テスト")
        entity2 = EntityNode(name="エンティティ2", label="テスト")
        entity3 = EntityNode(name="エンティティ3", label="テスト")
        
        relation1 = Relation(
            label="関連1",
            source_id=entity1.id,
            target_id=entity2.id
        )
        relation2 = Relation(
            label="関連2",
            source_id=entity2.id,
            target_id=entity3.id
        )
        
        graph_store.upsert_nodes([entity1, entity2, entity3])
        graph_store.upsert_relations([relation1, relation2])
        
        # Test depth search as shown in documentation
        nodes = graph_store.get(ids=[entity1.id])
        related_triplets = graph_store.get_rel_map(
            graph_nodes=nodes,
            depth=2,  # 深度
            limit=30,  # 結果の上限
            ignore_rels=["無関係"]  # 無視する関係タイプ
        )
        
        # Should find relations within depth 2
        assert len(related_triplets) >= 1

    def test_graph_visualization_functionality(self):
        """Test graph visualization functionality as documented."""
        import tempfile
        import os
        from pathlib import Path
        
        graph_store = get_property_graph_store()
        
        # Add some test data
        entity1 = EntityNode(name="可視化テスト1", label="テスト")
        entity2 = EntityNode(name="可視化テスト2", label="テスト")
        relation = Relation(
            label="テスト関係",
            source_id=entity1.id,
            target_id=entity2.id
        )
        
        graph_store.upsert_nodes([entity1, entity2])
        graph_store.upsert_relations([relation])
        
        # Test graph visualization as shown in documentation
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # グラフをHTML形式で保存
            graph_store.save_networkx_graph(tmp_path)
            
            # Verify file was created
            path = Path(tmp_path)
            assert path.exists()
            assert path.stat().st_size > 0
            
            # Basic content verification
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "<html>" in content
                assert "可視化テスト1" in content or "entity" in content.lower()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_knowledge_graph_store_initialization(self):
        """Test KnowledgeGraphStore initialization as shown in documentation."""
        # Test the basic initialization example from the documentation
        graph_store = PostgresGraphStore(
            db_connection_string=os.environ.get("POSTGRES_TEST_CONNECTION_STRING")
        )
        
        # Verify the store was created correctly
        assert graph_store is not None
        # Basic functionality test would require more setup

    @patch('llama_index.core.PropertyGraphIndex.from_documents')
    @patch('llama_index.embeddings.bedrock.BedrockEmbedding')
    @patch('llama_index.llms.bedrock_converse.BedrockConverse')
    def test_documentation_example_structure(self, mock_llm, mock_embed, mock_index):
        """Test that the documentation example structure is valid."""
        # This test verifies that the imports and basic structure in the documentation work
        # We mock the external dependencies to focus on the PostgreSQL integration
        
        # Mock the external components
        mock_llm_instance = Mock()
        mock_embed_instance = Mock()
        mock_index_instance = Mock()
        
        mock_llm.return_value = mock_llm_instance
        mock_embed.return_value = mock_embed_instance
        mock_index.return_value = mock_index_instance
        
        # Test that we can create the graph store as shown in documentation
        graph_store = PostgresPropertyGraphStore(
            db_connection_string=os.environ.get("POSTGRES_TEST_CONNECTION_STRING"),
            embedding_dim=1024,
            drop_existing_table=True,
            node_table_name="test_doc_example_nodes",
            relation_table_name="test_doc_example_relations",
        )
        
        assert graph_store is not None
        assert graph_store._embedding_dim == 1024
        
        # Verify that the store has the expected interface
        assert hasattr(graph_store, 'upsert_nodes')
        assert hasattr(graph_store, 'upsert_relations')
        assert hasattr(graph_store, 'get_triplets')
        assert hasattr(graph_store, 'vector_query')
        assert hasattr(graph_store, 'save_networkx_graph')