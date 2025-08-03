# LlamaIndex Graph Stores Integration: PostgreSQL

PostgreSQLは35年以上の開発実績を持つ、強力なオープンソースのオブジェクトリレーショナルデータベースシステムです。pgvector拡張機能により、PostgreSQLはベクトル演算をサポートし、AIアプリケーションやベクトル類似性検索に適したデータベースとなっています。

このプロジェクトでは、PostgreSQLをグラフストアとして統合し、LlamaIndexのグラフデータを保存します。PostgreSQLのSQLインターフェースを使用してグラフデータをクエリできるため、PostgreSQLを使ってLlamaIndexのグラフインデックスと対話することが可能です。

## 提供される機能

- **Property Graph Store**: `PostgresPropertyGraphStore`
- **Knowledge Graph Store**: `PostgresGraphStore`

## インストール

```shell
pip install llama-index
pip install git+https://github.com/hmatsu47/llama-index-graph-stores-postgres.git
```

## Property Graph Store について

Property Graph Store（プロパティグラフストア）は、LlamaIndexの最新のグラフインデックス機能です。従来のKnowledge Graph Storeと比較して、より柔軟で表現力豊かなグラフ構造を提供します。

### 主な特徴

1. **エンティティとリレーションシップの詳細な表現**: ノードとエッジの両方にプロパティを持たせることができます
2. **ベクトル埋め込みのサポート**: pgvector拡張機能を活用したベクトル検索が可能です
3. **複雑なクエリの実行**: グラフ構造とベクトル検索を組み合わせた高度なクエリが実行できます
4. **スケーラビリティ**: PostgreSQLの堅牢性とスケーラビリティを活用できます

詳細については、[LlamaIndex Property Graph Index ガイド](https://docs.llamaindex.ai/en/stable/module_guides/indexing/lpg_index_guide/)を参照してください。

## 使用方法

### Property Graph Store の使用

**注意**: `PostgresPropertyGraphStore`を使用するには、PostgreSQLデータベースにpgvector拡張機能がインストールされている必要があります。

#### pgvector拡張機能のインストール

PostgreSQLデータベースでpgvector拡張機能を有効にするには、以下のSQLコマンドを実行してください：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 基本的な使用例

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
documents = SimpleDirectoryReader("../../../examples/data/paul_graham/").load_data()

# PostgreSQL Property Graph Storeの初期化
graph_store = PostgresPropertyGraphStore(
    db_connection_string="postgresql://user:password@host:5432/dbname",
)

# LLMと埋め込みモデルの設定
llm = BedrockConverse(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name="us-west-2",
    temperature=0.0,
)
embed_model = BedrockEmbedding(
    model_name=Models.TITAN_EMBEDDING_V2_0, region_name="us-west-2"
)

Settings.llm = llm
Settings.embed_model = embed_model

# Property Graph Indexの作成
index = PropertyGraphIndex.from_documents(
    documents,
    embed_model=embed_model,
    kg_extractors=[
        SimpleLLMPathExtractor(llm=llm),  # LLMを使用したパス抽出
        ImplicitPathExtractor(),          # 暗黙的なパス抽出
    ],
    property_graph_store=graph_store,
    show_progress=True,
)

# クエリエンジンの作成と実行
query_engine = index.as_query_engine(include_text=True)
response = query_engine.query("InterleafとViawebで何が起こったのですか？")
print(response)
```

#### Property Graph Storeの詳細設定

Property Graph Storeでは、以下のような詳細な設定が可能です：

```python
# より詳細な設定例
graph_store = PostgresPropertyGraphStore(
    db_connection_string="postgresql://user:password@host:5432/dbname",
    table_name="custom_property_graph",  # カスタムテーブル名
    embed_dim=1536,                      # 埋め込みベクトルの次元数
)

# カスタム抽出器の使用
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor

# スキーマベースの抽出器
schema_extractor = SchemaLLMPathExtractor(
    llm=llm,
    possible_entities=["Person", "Company", "Product", "Event"],
    possible_relations=["WORKED_AT", "FOUNDED", "CREATED", "HAPPENED_AT"],
)

index = PropertyGraphIndex.from_documents(
    documents,
    embed_model=embed_model,
    kg_extractors=[schema_extractor],
    property_graph_store=graph_store,
    show_progress=True,
)
```

### Knowledge Graph Store の使用

Knowledge Graph Store（ナレッジグラフストア）は、従来のトリプレット形式（主語-述語-目的語）でグラフデータを管理します。

#### 基本的な使用例

```python
from llama_index.graph_stores.postgres import PostgresGraphStore
from llama_index.core import (
    KnowledgeGraphIndex,
    SimpleDirectoryReader,
    StorageContext,
)

# ドキュメントの読み込み
documents = SimpleDirectoryReader(
    "../../../examples/data/paul_graham/"
).load_data()

# PostgreSQL Graph Storeの初期化
graph_store = PostgresGraphStore(
    db_connection_string="postgresql://user:password@host:5432/dbname"
)

# ストレージコンテキストの作成
storage_context = StorageContext.from_defaults(graph_store=graph_store)

# Knowledge Graph Indexの作成
index = KnowledgeGraphIndex.from_documents(
    documents=documents,
    storage_context=storage_context,
    max_triplets_per_chunk=2,  # チャンクあたりの最大トリプレット数
)

# クエリエンジンの作成と実行
query_engine = index.as_query_engine(
    include_text=False,           # テキストを含めない
    response_mode="tree_summarize"  # ツリー要約モード
)
response = query_engine.query(
    "Interleafについて詳しく教えてください",
)
print(response)
```

## データベース設定

### PostgreSQLの準備

1. **PostgreSQLのインストール**: PostgreSQL 12以上を推奨
2. **pgvector拡張機能のインストール**: Property Graph Storeを使用する場合は必須
3. **データベースの作成**: 専用のデータベースを作成することを推奨

```sql
-- データベースの作成
CREATE DATABASE llamaindex_graphs;

-- pgvector拡張機能の有効化（Property Graph Store使用時）
\c llamaindex_graphs
CREATE EXTENSION IF NOT EXISTS vector;
```

### 接続文字列の形式

```python
# 基本的な接続文字列
db_connection_string = "postgresql://username:password@hostname:port/database_name"

# SSL接続を使用する場合
db_connection_string = "postgresql://username:password@hostname:port/database_name?sslmode=require"

# 接続プールの設定
db_connection_string = "postgresql://username:password@hostname:port/database_name?pool_size=10&max_overflow=20"
```

## パフォーマンスの最適化

### インデックスの作成

Property Graph Storeを使用する場合、以下のインデックスを作成することでパフォーマンスが向上します：

```sql
-- ベクトル検索用のインデックス
CREATE INDEX ON property_graph_nodes USING ivfflat (embedding vector_cosine_ops);

-- テキスト検索用のインデックス
CREATE INDEX ON property_graph_nodes USING gin (to_tsvector('english', name));
CREATE INDEX ON property_graph_nodes USING gin (to_tsvector('english', properties));
```

### 設定の調整

```python
# バッチサイズの調整
index = PropertyGraphIndex.from_documents(
    documents,
    embed_model=embed_model,
    kg_extractors=[SimpleLLMPathExtractor(llm=llm)],
    property_graph_store=graph_store,
    show_progress=True,
    # バッチ処理の設定
    insert_batch_size=100,  # 挿入バッチサイズ
)
```

## トラブルシューティング

### よくある問題と解決方法

1. **pgvector拡張機能が見つからない**
   ```
   ERROR: extension "vector" is not available
   ```
   解決方法: pgvector拡張機能をインストールしてください

2. **接続エラー**
   ```
   psycopg2.OperationalError: could not connect to server
   ```
   解決方法: 接続文字列、ファイアウォール設定、PostgreSQLサービスの状態を確認してください

3. **メモリ不足エラー**
   ```
   OutOfMemoryError: Unable to allocate memory
   ```
   解決方法: バッチサイズを小さくするか、PostgreSQLのメモリ設定を調整してください

## 高度な使用例

### カスタムスキーマの定義

```python
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor

# カスタムエンティティとリレーションシップの定義
custom_schema_extractor = SchemaLLMPathExtractor(
    llm=llm,
    possible_entities=[
        "Person", "Company", "Technology", "Product", 
        "Location", "Event", "Concept"
    ],
    possible_relations=[
        "WORKS_AT", "FOUNDED", "DEVELOPED", "LOCATED_IN",
        "PARTICIPATED_IN", "RELATED_TO", "INFLUENCED_BY"
    ],
    # 抽出の詳細設定
    num_workers=4,
    max_paths_per_chunk=10,
)
```

### 複合クエリの実行

```python
# 複数の検索戦略を組み合わせたクエリエンジン
query_engine = index.as_query_engine(
    include_text=True,
    response_mode="tree_summarize",
    # ベクトル検索とキーワード検索の組み合わせ
    similarity_top_k=10,
    # グラフトラバーサルの深度
    explore_global_knowledge=True,
)

# 複雑なクエリの実行
response = query_engine.query(
    "Paul Grahamが関わった会社とその技術的な特徴について、"
    "時系列順に整理して説明してください。"
)
```

## まとめ

このLlamaIndex PostgreSQL Graph Stores統合により、PostgreSQLの堅牢性とスケーラビリティを活用しながら、高度なグラフベースの検索と推論が可能になります。Property Graph StoreとKnowledge Graph Storeの両方をサポートしており、用途に応じて適切な選択ができます。

詳細な技術仕様や最新の機能については、[LlamaIndex公式ドキュメント](https://docs.llamaindex.ai/)を参照してください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 貢献

プロジェクトへの貢献を歓迎します。バグレポート、機能リクエスト、プルリクエストをお待ちしています。

## サポート

問題や質問がある場合は、GitHubのIssuesページでお知らせください。