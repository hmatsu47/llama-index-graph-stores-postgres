# PostgreSQL Property Graph Index 詳細ガイド

このドキュメントは、LlamaIndexのProperty Graph Index機能をPostgreSQLと組み合わせて使用する方法について詳しく説明します。

## Property Graph Index とは

Property Graph Index（プロパティグラフインデックス）は、LlamaIndexの最新のグラフインデックス機能で、従来のKnowledge Graph Indexよりも表現力豊かで柔軟なグラフ構造を提供します。

### 従来のKnowledge Graph Indexとの違い

| 特徴 | Knowledge Graph Index | Property Graph Index |
|------|----------------------|---------------------|
| データ構造 | トリプレット（主語-述語-目的語） | ノードとエッジにプロパティを持つグラフ |
| 表現力 | 基本的なリレーションシップ | 複雑な属性とメタデータ |
| ベクトル検索 | 限定的 | 完全サポート |
| クエリの柔軟性 | 基本的 | 高度 |

参考: [LlamaIndex Property Graph Index Guide](https://docs.llamaindex.ai/en/stable/module_guides/indexing/lpg_index_guide/)

## PostgreSQL Property Graph Store の特徴

### 1. ベクトル埋め込みサポート

pgvector拡張機能を活用して、ノードとエッジの両方にベクトル埋め込みを保存できます。

```python
from llama_index.graph_stores.postgres import PostgresPropertyGraphStore

# ベクトル次元を指定してストアを初期化
graph_store = PostgresPropertyGraphStore(
    db_connection_string="postgresql://user:password@host:5432/dbname",
    embed_dim=1536,  # 埋め込みベクトルの次元数
)
```

### 2. 柔軟なスキーマ設計

ノードとエッジに任意のプロパティを追加できます。

```python
# カスタムプロパティを持つノードの例
node_properties = {
    "name": "Apple Inc.",
    "type": "Company",
    "founded": "1976",
    "industry": "Technology",
    "market_cap": "3000000000000"  # 3兆ドル
}
```

## 実装の詳細

### データベーススキーマ

PostgreSQL Property Graph Storeは以下のテーブル構造を使用します：

```sql
-- ノードテーブル
CREATE TABLE property_graph_nodes (
    id VARCHAR PRIMARY KEY,
    name VARCHAR,
    type VARCHAR,
    properties JSONB,
    embedding VECTOR(1536)  -- pgvector型
);

-- エッジテーブル  
CREATE TABLE property_graph_edges (
    id VARCHAR PRIMARY KEY,
    source_id VARCHAR REFERENCES property_graph_nodes(id),
    target_id VARCHAR REFERENCES property_graph_nodes(id),
    type VARCHAR,
    properties JSONB,
    embedding VECTOR(1536)
);

-- インデックス
CREATE INDEX ON property_graph_nodes USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON property_graph_edges USING ivfflat (embedding vector_cosine_ops);
```

### 抽出器（Extractors）の種類

#### 1. SimpleLLMPathExtractor

基本的なLLMベースの抽出器です。

```python
from llama_index.core.indices.property_graph import SimpleLLMPathExtractor

extractor = SimpleLLMPathExtractor(
    llm=llm,
    max_paths_per_chunk=10,  # チャンクあたりの最大パス数
    num_workers=4,           # 並列処理のワーカー数
)
```

#### 2. SchemaLLMPathExtractor

事前定義されたスキーマに基づいて抽出を行います。

```python
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor

schema_extractor = SchemaLLMPathExtractor(
    llm=llm,
    possible_entities=[
        "Person", "Company", "Product", "Technology", 
        "Location", "Event", "Concept"
    ],
    possible_relations=[
        "WORKS_AT", "FOUNDED", "DEVELOPED", "LOCATED_IN",
        "PARTICIPATED_IN", "USES", "COMPETES_WITH"
    ],
    strict=True,  # スキーマを厳密に適用
)
```

#### 3. ImplicitPathExtractor

テキストの構造から暗黙的なパスを抽出します。

```python
from llama_index.core.indices.property_graph import ImplicitPathExtractor

implicit_extractor = ImplicitPathExtractor()
```

## 高度な使用例

### 1. 複数の抽出器を組み合わせた使用

```python
from llama_index.core import PropertyGraphIndex, Settings
from llama_index.core.indices.property_graph import (
    SimpleLLMPathExtractor,
    SchemaLLMPathExtractor,
    ImplicitPathExtractor,
)

# 複数の抽出器を組み合わせ
extractors = [
    SchemaLLMPathExtractor(
        llm=llm,
        possible_entities=["Person", "Company", "Product"],
        possible_relations=["WORKS_AT", "FOUNDED", "CREATED"],
    ),
    SimpleLLMPathExtractor(llm=llm),
    ImplicitPathExtractor(),
]

index = PropertyGraphIndex.from_documents(
    documents,
    embed_model=embed_model,
    kg_extractors=extractors,
    property_graph_store=graph_store,
    show_progress=True,
)
```

### 2. カスタムクエリエンジンの設定

```python
# 詳細なクエリエンジン設定
query_engine = index.as_query_engine(
    include_text=True,                    # 元のテキストを含める
    response_mode="tree_summarize",       # 応答モード
    similarity_top_k=10,                  # 類似度検索の上位K件
    explore_global_knowledge=True,        # グローバル知識の探索
    max_knowledge_sequence=30,            # 最大知識シーケンス長
)
```

### 3. グラフの可視化

```python
import networkx as nx
from pyvis.network import Network

# グラフデータの取得
graph_data = graph_store.get_graph_data()

# NetworkXグラフの作成
G = nx.Graph()
for node in graph_data.nodes:
    G.add_node(node.id, **node.properties)
for edge in graph_data.edges:
    G.add_edge(edge.source_id, edge.target_id, **edge.properties)

# Pyvisを使用した可視化
net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
net.from_nx(G)
net.show("property_graph.html")
```

## パフォーマンス最適化

### 1. バッチ処理の最適化

```python
# 大量のドキュメントを効率的に処理
index = PropertyGraphIndex.from_documents(
    documents,
    embed_model=embed_model,
    kg_extractors=extractors,
    property_graph_store=graph_store,
    insert_batch_size=50,     # 挿入バッチサイズ
    num_workers=8,            # 並列処理数
    show_progress=True,
)
```

### 2. インデックスの最適化

```sql
-- ベクトル検索の最適化
CREATE INDEX CONCURRENTLY ON property_graph_nodes 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- プロパティ検索の最適化
CREATE INDEX CONCURRENTLY ON property_graph_nodes 
USING gin (properties);

-- 複合インデックス
CREATE INDEX CONCURRENTLY ON property_graph_nodes (type, name);
```

### 3. メモリ使用量の最適化

```python
# メモリ効率的な設定
Settings.chunk_size = 512        # チャンクサイズを小さく
Settings.chunk_overlap = 50      # オーバーラップを最小限に

# ストリーミング処理
for doc_batch in batch_documents(documents, batch_size=10):
    index.insert_documents(doc_batch)
```

## 実用的なユースケース

### 1. 企業知識ベースの構築

```python
# 企業文書からの知識抽出
company_extractor = SchemaLLMPathExtractor(
    llm=llm,
    possible_entities=[
        "Employee", "Department", "Project", "Client", 
        "Product", "Technology", "Process"
    ],
    possible_relations=[
        "WORKS_IN", "MANAGES", "PARTICIPATES_IN", "USES",
        "DEVELOPS", "SERVES", "DEPENDS_ON"
    ],
)

# 企業固有のクエリ
query_engine = index.as_query_engine(include_text=True)
response = query_engine.query(
    "プロジェクトXに関わった従業員と使用された技術について教えてください"
)
```

### 2. 研究論文の分析

```python
# 学術論文からの知識抽出
academic_extractor = SchemaLLMPathExtractor(
    llm=llm,
    possible_entities=[
        "Author", "Institution", "Paper", "Concept", 
        "Method", "Dataset", "Metric"
    ],
    possible_relations=[
        "AUTHORED", "AFFILIATED_WITH", "CITES", "PROPOSES",
        "USES", "EVALUATES_ON", "IMPROVES"
    ],
)
```

### 3. 顧客サポートシステム

```python
# サポート文書からの知識抽出
support_extractor = SchemaLLMPathExtractor(
    llm=llm,
    possible_entities=[
        "Product", "Feature", "Issue", "Solution", 
        "User", "Version", "Platform"
    ],
    possible_relations=[
        "HAS_FEATURE", "CAUSES", "SOLVES", "AFFECTS",
        "COMPATIBLE_WITH", "REQUIRES", "REPLACES"
    ],
)
```

## まとめ

PostgreSQL Property Graph Storeは、LlamaIndexの強力なグラフインデックス機能とPostgreSQLの堅牢性を組み合わせた、スケーラブルで高性能なソリューションです。複雑な知識グラフの構築と検索が可能で、様々な実用的なアプリケーションに適用できます。

詳細な技術仕様については、[LlamaIndex公式ドキュメント](https://docs.llamaindex.ai/en/stable/module_guides/indexing/lpg_index_guide/)を参照してください。