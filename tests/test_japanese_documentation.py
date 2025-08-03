"""Tests for Japanese documentation files."""

import os
from pathlib import Path


def test_japanese_readme_exists():
    """Test that the Japanese README file exists."""
    readme_ja_path = Path(__file__).parent.parent / "README_ja.md"
    assert readme_ja_path.exists(), "README_ja.md should exist"


def test_japanese_readme_content():
    """Test that the Japanese README contains expected content."""
    readme_ja_path = Path(__file__).parent.parent / "README_ja.md"
    
    with open(readme_ja_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for key sections in Japanese
    assert "LlamaIndex Graph Stores Integration: PostgreSQL" in content
    assert "インストール" in content
    assert "使用方法" in content
    assert "Property Graph Store" in content
    assert "Knowledge Graph Store" in content
    assert "PostgresPropertyGraphStore" in content
    assert "PostgresGraphStore" in content
    
    # Check for code examples
    assert "```python" in content
    assert "from llama_index.graph_stores.postgres import" in content


def test_property_graph_guide_exists():
    """Test that the Property Graph guide in Japanese exists."""
    guide_path = Path(__file__).parent.parent / "PROPERTY_GRAPH_GUIDE_ja.md"
    assert guide_path.exists(), "PROPERTY_GRAPH_GUIDE_ja.md should exist"


def test_property_graph_guide_content():
    """Test that the Property Graph guide contains expected content."""
    guide_path = Path(__file__).parent.parent / "PROPERTY_GRAPH_GUIDE_ja.md"
    
    with open(guide_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for key sections
    assert "Property Graph Index とは" in content
    assert "PostgreSQL Property Graph Store の特徴" in content
    assert "実装の詳細" in content
    assert "抽出器（Extractors）の種類" in content
    assert "高度な使用例" in content
    assert "パフォーマンス最適化" in content
    
    # Check for reference to LlamaIndex guide
    assert "https://docs.llamaindex.ai/en/stable/module_guides/indexing/lpg_index_guide/" in content
    
    # Check for technical content
    assert "SimpleLLMPathExtractor" in content
    assert "SchemaLLMPathExtractor" in content
    assert "ImplicitPathExtractor" in content
    assert "pgvector" in content


def test_setup_guide_exists():
    """Test that the setup guide in Japanese exists."""
    setup_path = Path(__file__).parent.parent / "SETUP_GUIDE_ja.md"
    assert setup_path.exists(), "SETUP_GUIDE_ja.md should exist"


def test_setup_guide_content():
    """Test that the setup guide contains expected content."""
    setup_path = Path(__file__).parent.parent / "SETUP_GUIDE_ja.md"
    
    with open(setup_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for key sections
    assert "PostgreSQL Graph Stores セットアップガイド" in content
    assert "前提条件" in content
    assert "PostgreSQLの準備" in content
    assert "データベースの設定" in content
    assert "Pythonパッケージのインストール" in content
    assert "基本的な動作確認" in content
    assert "トラブルシューティング" in content
    
    # Check for installation commands
    assert "pip install" in content
    assert "CREATE EXTENSION IF NOT EXISTS vector" in content
    assert "postgresql://" in content


def test_documentation_encoding():
    """Test that all Japanese documentation files are properly UTF-8 encoded."""
    doc_files = [
        "README_ja.md",
        "PROPERTY_GRAPH_GUIDE_ja.md", 
        "SETUP_GUIDE_ja.md"
    ]
    
    base_path = Path(__file__).parent.parent
    
    for doc_file in doc_files:
        file_path = base_path / doc_file
        assert file_path.exists(), f"{doc_file} should exist"
        
        # Try to read the file as UTF-8
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Check that we can read Japanese characters
                assert len(content) > 0, f"{doc_file} should not be empty"
        except UnicodeDecodeError:
            assert False, f"{doc_file} should be properly UTF-8 encoded"


def test_documentation_links():
    """Test that documentation files contain proper cross-references."""
    readme_ja_path = Path(__file__).parent.parent / "README_ja.md"
    
    with open(readme_ja_path, "r", encoding="utf-8") as f:
        readme_content = f.read()
    
    # Check for reference to LlamaIndex documentation
    assert "https://docs.llamaindex.ai/" in readme_content
    
    setup_guide_path = Path(__file__).parent.parent / "SETUP_GUIDE_ja.md"
    
    with open(setup_guide_path, "r", encoding="utf-8") as f:
        setup_content = f.read()
    
    # Check for cross-references to other documentation files
    assert "README_ja.md" in setup_content
    assert "PROPERTY_GRAPH_GUIDE_ja.md" in setup_content


def test_code_examples_syntax():
    """Test that code examples in documentation have proper syntax."""
    doc_files = [
        "README_ja.md",
        "PROPERTY_GRAPH_GUIDE_ja.md",
        "SETUP_GUIDE_ja.md"
    ]
    
    base_path = Path(__file__).parent.parent
    
    for doc_file in doc_files:
        file_path = base_path / doc_file
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for proper code block formatting
        python_blocks = content.count("```python")
        sql_blocks = content.count("```sql")
        bash_blocks = content.count("```bash")
        
        # Each opening should have a corresponding closing
        total_code_blocks = python_blocks + sql_blocks + bash_blocks
        if total_code_blocks > 0:
            # Count total ``` occurrences (should be even - opening and closing)
            total_backticks = content.count("```")
            assert total_backticks % 2 == 0, f"Code blocks in {doc_file} should be properly closed"
            assert total_backticks >= total_code_blocks * 2, f"Code blocks in {doc_file} should have proper syntax"