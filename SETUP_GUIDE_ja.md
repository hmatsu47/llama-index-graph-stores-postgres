# PostgreSQL Graph Stores セットアップガイド

このガイドでは、LlamaIndex PostgreSQL Graph Storesを使い始めるための手順を説明します。

## 前提条件

- Python 3.9以上
- PostgreSQL 12以上
- pgvector拡張機能（Property Graph Store使用時）

## 1. PostgreSQLの準備

### PostgreSQLのインストール

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

#### macOS (Homebrew)
```bash
brew install postgresql
brew services start postgresql
```

#### Windows
PostgreSQL公式サイトからインストーラーをダウンロードしてインストールしてください。

### pgvector拡張機能のインストール

#### Ubuntu/Debian
```bash
sudo apt install postgresql-14-pgvector
```

#### macOS (Homebrew)
```bash
brew install pgvector
```

#### ソースからのビルド
```bash
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

## 2. データベースの設定

### データベースとユーザーの作成

```sql
-- PostgreSQLに管理者としてログイン
sudo -u postgres psql

-- 新しいユーザーの作成
CREATE USER llamaindex_user WITH PASSWORD 'your_secure_password';

-- 新しいデータベースの作成
CREATE DATABASE llamaindex_graphs OWNER llamaindex_user;

-- ユーザーに必要な権限を付与
GRANT ALL PRIVILEGES ON DATABASE llamaindex_graphs TO llamaindex_user;

-- データベースに接続
\c llamaindex_graphs

-- pgvector拡張機能の有効化（Property Graph Store使用時）
CREATE EXTENSION IF NOT EXISTS vector;

-- 権限の確認
GRANT USAGE ON SCHEMA public TO llamaindex_user;
GRANT CREATE ON SCHEMA public TO llamaindex_user;
```

## 3. Pythonパッケージのインストール

### 基本パッケージ
```bash
pip install llama-index
pip install git+https://github.com/hmatsu47/llama-index-graph-stores-postgres.git
```

### 追加の依存関係（必要に応じて）
```bash
# AWS Bedrock使用時
pip install llama-index-llms-bedrock-converse
pip install llama-index-embeddings-bedrock

# OpenAI使用時
pip install llama-index-llms-openai
pip install llama-index-embeddings-openai

# 可視化ツール
pip install pyvis networkx matplotlib
```

## 4. 基本的な動作確認

### 接続テスト

```python
from llama_index.graph_stores.postgres import PostgresPropertyGraphStore

# 接続文字列（実際の値に置き換えてください）
db_connection_string = "postgresql://llamaindex_user:your_secure_password@localhost:5432/llamaindex_graphs"

try:
    # Property Graph Storeの初期化
    graph_store = PostgresPropertyGraphStore(
        db_connection_string=db_connection_string,
    )
    print("✅ PostgreSQL Property Graph Storeへの接続に成功しました")
except Exception as e:
    print(f"❌ 接続エラー: {e}")
```

### 簡単なテスト

```python
from llama_index.core import PropertyGraphIndex, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.indices.property_graph import SimpleLLMPathExtractor

# テスト用のドキュメント
test_documents = [
    Document(text="Apple Inc.は1976年にSteve JobsとSteve Wozniakによって設立されました。"),
    Document(text="Appleは革新的な製品で知られており、iPhoneやMacなどを開発しています。"),
]

# LLMと埋め込みモデルの設定（OpenAI APIキーが必要）
Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.0)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")

# Property Graph Indexの作成
try:
    index = PropertyGraphIndex.from_documents(
        test_documents,
        kg_extractors=[SimpleLLMPathExtractor(llm=Settings.llm)],
        property_graph_store=graph_store,
        show_progress=True,
    )
    
    # クエリの実行
    query_engine = index.as_query_engine(include_text=True)
    response = query_engine.query("Appleについて教えてください")
    print(f"✅ テスト成功: {response}")
    
except Exception as e:
    print(f"❌ テストエラー: {e}")
```

## 5. 環境変数の設定

セキュリティのため、接続情報は環境変数で管理することを推奨します。

### .envファイルの作成

```bash
# .env
DATABASE_URL=postgresql://llamaindex_user:your_secure_password@localhost:5432/llamaindex_graphs
OPENAI_API_KEY=your_openai_api_key
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-west-2
```

### Python-dotenvの使用

```bash
pip install python-dotenv
```

```python
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

db_connection_string = os.getenv("DATABASE_URL")
openai_api_key = os.getenv("OPENAI_API_KEY")
```

## 6. トラブルシューティング

### よくある問題

#### 1. pgvector拡張機能が見つからない
```
ERROR: extension "vector" is not available
```
**解決方法**: pgvector拡張機能をインストールし、PostgreSQLを再起動してください。

#### 2. 接続権限エラー
```
psycopg2.OperationalError: FATAL: permission denied for database
```
**解決方法**: ユーザーに適切な権限が付与されているか確認してください。

#### 3. メモリ不足
```
OutOfMemoryError: Unable to allocate memory
```
**解決方法**: PostgreSQLのメモリ設定を調整するか、バッチサイズを小さくしてください。

### デバッグ用のSQL

```sql
-- テーブルの確認
\dt

-- ノード数の確認
SELECT COUNT(*) FROM property_graph_nodes;

-- エッジ数の確認  
SELECT COUNT(*) FROM property_graph_edges;

-- インデックスの確認
\di
```

## 7. 次のステップ

セットアップが完了したら、以下のドキュメントを参照してください：

- [README_ja.md](README_ja.md) - 基本的な使用方法
- [PROPERTY_GRAPH_GUIDE_ja.md](PROPERTY_GRAPH_GUIDE_ja.md) - Property Graph Indexの詳細ガイド

## サポート

問題が発生した場合は、GitHubのIssuesページでお知らせください。