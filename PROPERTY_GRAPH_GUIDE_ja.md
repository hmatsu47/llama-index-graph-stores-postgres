# LlamaIndex Graph Stores Integration: PostgreSQL - プロパティグラフガイド

## 概要

このドキュメントでは、LlamaIndexのプロパティグラフインデックスをPostgreSQLと統合して使用する方法について説明します。PostgreSQLは35年以上の開発実績を持つ強力なオープンソースのオブジェクトリレーショナルデータベースシステムです。pgvector拡張機能により、PostgreSQLはベクトル操作をサポートし、AIアプリケーションやベクトル類似性検索に適しています。

このプロジェクトでは、PostgreSQLをグラフストアとして統合し、LlamaIndexのグラフデータを保存し、PostgreSQLのSQLインターフェースを使用してグラフデータをクエリできるようにしています。

## 主な機能

- **プロパティグラフストア**: `PostgresPropertyGraphStore`
- **ナレッジグラフストア**: `PostgresGraphStore`

## インストール

```shell
pip install llama-index
pip install git+https://github.com/hmatsu47/llama-index-graph-stores-postgres.git
```

## 前提条件

### PostgreSQL設定

プロパティグラフストアを使用するには、PostgreSQLデータベースにpgvector拡張機能がインストールされている必要があります。

```sql
-- pgvector拡張機能を有効化
CREATE EXTENSION IF NOT EXISTS vector;
```

## プロパティグラフストア（PostgresPropertyGraphStore）

**重要**: このリポジトリのコードでは embed_dim は 1024 固定です。

### 基本概念

プロパティグラフは、ノードとエッジ（関係）の両方にプロパティ（属性）を持つことができるグラフデータ構造です。LlamaIndexのプロパティグラフインデックスは、以下の特徴を持ちます：

- **エンティティノード**: 抽出されたエンティティを表現
- **チャンクノード**: 元のテキストチャンクを表現
- **関係**: エンティティ間の関係を表現
- **ベクトル検索**: エンベディングを使用した類似性検索

### 重要な制限事項

**注意**: このリポジトリのコードでは embed_dim は 1024 固定です。

### 基本的な使用例

```python
from llama_index.core import PropertyGraphIndex, Settings, SimpleDirectoryReader
from llama_index.embeddings.bedrock import BedrockEmbedding, Models
from llama_index.llms.bedrock_converse import BedrockConverse
from llama_index.core.indices.property_graph import (
    ImplicitPathExtractor,
    SimpleLLMPathExtractor,
)
from llama_index.graph_stores.postgres import PostgresPropertyGraphStore

# ドキュメントの読み込み
documents = SimpleDirectoryReader("./data/").load_data()

# PostgreSQLプロパティグラフストアの初期化
graph_store = PostgresPropertyGraphStore(
    db_connection_string="postgresql://user:password@host:5432/dbname",
    embedding_dim=1024,  # 固定値（変更不可）
    node_table_name="pg_nodes",  # ノードテーブル名（オプション）
    relation_table_name="pg_relations",  # 関係テーブル名（オプション）
    drop_existing_table=False,  # 既存テーブルを削除するか（オプション）
    echo_queries=False,  # SQLクエリをログ出力するか（オプション）
)

# LLMとエンベディングモデルの設定
llm = BedrockConverse(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name="us-west-2",
    temperature=0.0,
)
embed_model = BedrockEmbedding(
    model_name=Models.TITAN_EMBEDDING_V2_0, 
    region_name="us-west-2"
)

Settings.llm = llm
Settings.embed_model = embed_model

# プロパティグラフインデックスの作成
index = PropertyGraphIndex.from_documents(
    documents,
    embed_model=embed_model,
    kg_extractors=[
        SimpleLLMPathExtractor(llm=llm),  # LLMベースの関係抽出
        ImplicitPathExtractor(),  # 暗黙的な関係抽出
    ],
    property_graph_store=graph_store,
    show_progress=True,
)

# クエリエンジンの作成と使用
query_engine = index.as_query_engine(include_text=True)
response = query_engine.query("InterleafとViawebで何が起こったのですか？")
print(response)
```

### データベーススキーマ

PostgresPropertyGraphStoreは以下のテーブル構造を使用します：

#### ノードテーブル（pg_nodes）

```sql
CREATE TABLE pg_nodes (
    id VARCHAR(512) PRIMARY KEY,
    text TEXT,
    name VARCHAR(512),
    label VARCHAR(512) NOT NULL DEFAULT 'node',
    properties JSONB DEFAULT '{}',
    embedding VECTOR(1024),  -- 固定次元
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### 関係テーブル（pg_relations）

```sql
CREATE TABLE pg_relations (
    id SERIAL PRIMARY KEY,
    label VARCHAR(512) NOT NULL,
    source_id VARCHAR(512) REFERENCES pg_nodes(id),
    target_id VARCHAR(512) REFERENCES pg_nodes(id),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 高度な使用例

#### カスタムエクストラクターの使用

```python
from llama_index.core.indices.property_graph import (
    SchemaLLMPathExtractor,
    DynamicLLMPathExtractor,
)

# スキーマベースの抽出器
schema_extractor = SchemaLLMPathExtractor(
    llm=llm,
    possible_entities=["人物", "会社", "製品", "場所"],
    possible_relations=["働いている", "設立した", "開発した", "位置している"],
)

# 動的抽出器
dynamic_extractor = DynamicLLMPathExtractor(
    llm=llm,
    max_triplets_per_chunk=10,
)

# インデックス作成時に使用
index = PropertyGraphIndex.from_documents(
    documents,
    embed_model=embed_model,
    kg_extractors=[
        schema_extractor,
        dynamic_extractor,
        ImplicitPathExtractor(),
    ],
    property_graph_store=graph_store,
    show_progress=True,
)
```

#### グラフの可視化

```python
# グラフをHTML形式で保存
graph_store.save_networkx_graph("knowledge_graph.html")
```

### クエリ機能

#### ベクトル検索

```python
from llama_index.core.graph_stores.types import VectorStoreQuery

# ベクトルクエリの実行
query_embedding = embed_model.get_text_embedding("技術革新について")
vector_query = VectorStoreQuery(
    query_embedding=query_embedding,
    similarity_top_k=5
)

nodes, scores = graph_store.vector_query(vector_query)
for node, score in zip(nodes, scores):
    print(f"ノード: {node.name}, スコア: {score}")
```

#### 関係の深度検索

```python
# 特定のノードから指定した深度までの関係を取得
nodes = graph_store.get(ids=["entity_1"])
related_triplets = graph_store.get_rel_map(
    graph_nodes=nodes,
    depth=2,  # 深度
    limit=30,  # 結果の上限
    ignore_rels=["無関係"]  # 無視する関係タイプ
)
```

## ナレッジグラフストア（PostgresGraphStore）

従来のナレッジグラフ（トリプレット形式）を使用する場合は、`PostgresGraphStore`を使用できます。

```python
from llama_index.graph_stores.postgres import PostgresGraphStore
from llama_index.core import (
    KnowledgeGraphIndex,
    SimpleDirectoryReader,
    StorageContext,
)

documents = SimpleDirectoryReader("./data/").load_data()

# PostgreSQLグラフストアの初期化
graph_store = PostgresGraphStore(
    db_connection_string="postgresql://user:password@host:5432/dbname"
)

storage_context = StorageContext.from_defaults(graph_store=graph_store)

# ナレッジグラフインデックスの作成
index = KnowledgeGraphIndex.from_documents(
    documents=documents,
    storage_context=storage_context,
    max_triplets_per_chunk=2,
)

query_engine = index.as_query_engine(
    include_text=False, 
    response_mode="tree_summarize"
)

response = query_engine.query("Interleafについて詳しく教えてください")
print(response)
```

## パフォーマンスの最適化

### インデックスの作成

```sql
-- ベクトル検索のためのインデックス
CREATE INDEX ON pg_nodes USING ivfflat (embedding vector_cosine_ops);

-- テキスト検索のためのインデックス
CREATE INDEX ON pg_nodes (name);
CREATE INDEX ON pg_nodes (label);

-- 関係検索のためのインデックス
CREATE INDEX ON pg_relations (source_id);
CREATE INDEX ON pg_relations (target_id);
CREATE INDEX ON pg_relations (label);
```

### 接続プールの設定

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# 接続プールを使用した設定
engine = create_engine(
    "postgresql://user:password@host:5432/dbname",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

graph_store = PostgresPropertyGraphStore(
    db_connection_string="postgresql://user:password@host:5432/dbname",
    # その他のパラメータ...
)
```

## トラブルシューティング

### よくある問題

1. **pgvector拡張機能がインストールされていない**
   ```
   ERROR: extension "vector" is not available
   ```
   解決方法: PostgreSQLにpgvector拡張機能をインストールしてください。

2. **エンベディング次元の不一致**
   ```
   ERROR: dimension mismatch
   ```
   解決方法: このリポジトリでは embed_dim は 1024 固定です。使用するエンベディングモデルが1024次元の出力を生成することを確認してください。

3. **メモリ不足**
   大量のドキュメントを処理する際は、バッチサイズを調整してください：
   ```python
   index = PropertyGraphIndex.from_documents(
       documents,
       embed_model=embed_model,
       kg_extractors=extractors,
       property_graph_store=graph_store,
       show_progress=True,
       # バッチサイズを調整
       insert_batch_size=50,
   )
   ```

## まとめ

PostgreSQL統合により、LlamaIndexのプロパティグラフインデックスを本格的なデータベース環境で運用できます。ベクトル検索、関係の深度検索、グラフの可視化など、豊富な機能を活用して、知識グラフベースのアプリケーションを構築してください。

重要な点として、このリポジトリの実装では**embed_dim は 1024 固定**であることを覚えておいてください。使用するエンベディングモデルがこの次元に対応していることを確認してから利用してください。