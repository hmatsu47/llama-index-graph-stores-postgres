# LlamaIndex Graph Stores Integration: PostgreSQL（日本語版）

PostgreSQLは35年以上の開発実績を持つ強力なオープンソースのオブジェクトリレーショナルデータベースシステムです。pgvector拡張機能により、PostgreSQLはベクトル操作をサポートし、AIアプリケーションやベクトル類似性検索に適しています。

このプロジェクトでは、PostgreSQLをグラフストアとして統合し、LlamaIndexのグラフデータを保存し、PostgreSQLのSQLインターフェースを使用してグラフデータをクエリできるようにしています。

- プロパティグラフストア: `PostgresPropertyGraphStore`
- ナレッジグラフストア: `PostgresGraphStore`

## インストール

```shell
pip install llama-index
pip install git+https://github.com/hmatsu47/llama-index-graph-stores-postgres.git
```

## 使用方法

### プロパティグラフストア

**注意**: `PostgresPropertyGraphStore`を使用するには、PostgreSQLデータベースにpgvector拡張機能がインストールされている必要があります。

**重要**: このリポジトリのコードでは embed_dim は 1024 固定です。

`PostgresPropertyGraphStore`の簡単な使用例：

```python
from llama_index.core import PropertyGraphIndex, Settings, SimpleDirectoryReader
from llama_index.embeddings.bedrock import BedrockEmbedding, Models
from llama_index.llms.bedrock_converse import BedrockConverse
from llama_index.core.indices.property_graph import (
    ImplicitPathExtractor,
    SimpleLLMPathExtractor,
)
from llama_index.graph_stores.postgres import PostgresPropertyGraphStore

documents = SimpleDirectoryReader("../../../examples/data/paul_graham/").load_data()

graph_store = PostgresPropertyGraphStore(
    db_connection_string="postgresql://user:password@host:5432/dbname",
)

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

index = PropertyGraphIndex.from_documents(
    documents,
    embed_model=embed_model,
    kg_extractors=[
        SimpleLLMPathExtractor(llm=llm),
        ImplicitPathExtractor(),
    ],
    property_graph_store=graph_store,
    show_progress=True,
)

query_engine = index.as_query_engine(include_text=True)
response = query_engine.query("InterleafとViawebで何が起こったのですか？")
print(response)
```

### ナレッジグラフストア

`PostgresGraphStore`の簡単な使用例：

```python
from llama_index.graph_stores.postgres import PostgresGraphStore
from llama_index.core import (
    KnowledgeGraphIndex,
    SimpleDirectoryReader,
    StorageContext,
)

documents = SimpleDirectoryReader(
    "../../../examples/data/paul_graham/"
).load_data()

graph_store = PostgresGraphStore(
    db_connection_string="postgresql://user:password@host:5432/dbname"
)
storage_context = StorageContext.from_defaults(graph_store=graph_store)
index = KnowledgeGraphIndex.from_documents(
    documents=documents,
    storage_context=storage_context,
    max_triplets_per_chunk=2,
)
query_engine = index.as_query_engine(
    include_text=False, response_mode="tree_summarize"
)
response = query_engine.query(
    "Interleafについて詳しく教えてください",
)
print(response)
```

## 詳細なドキュメント

より詳細な使用方法、設定オプション、トラブルシューティングについては、[プロパティグラフガイド（日本語版）](PROPERTY_GRAPH_GUIDE_ja.md)をご覧ください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。