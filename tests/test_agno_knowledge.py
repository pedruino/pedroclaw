"""Tests for Agno Knowledge Base integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pedroclaw.knowledge.agno_kb import create_knowledge_base, get_knowledge_base, search_knowledge


class TestAgnoKnowledge:
    """Test Agno Knowledge Base functionality."""

    @patch("pedroclaw.knowledge.agno_kb.PgVector")
    @patch("pedroclaw.knowledge.agno_kb.Knowledge")
    @patch("pedroclaw.knowledge.agno_kb.OpenAIEmbedder")
    def test_create_knowledge_base(self, mock_embedder: MagicMock, mock_knowledge: MagicMock, mock_pgvector: MagicMock) -> None:
        """Test knowledge base creation with correct configuration."""
        # Mock the dependencies
        mock_pgvector_instance = MagicMock()
        mock_pgvector.return_value = mock_pgvector_instance
        mock_knowledge_instance = MagicMock()
        mock_knowledge.return_value = mock_knowledge_instance

        # Create knowledge base
        kb = create_knowledge_base("test_table")

        # Verify PgVector was configured correctly
        mock_pgvector.assert_called_once()
        call_args = mock_pgvector.call_args
        assert call_args.kwargs["table_name"] == "test_table"
        assert "db_url" in call_args.kwargs
        assert call_args.kwargs["search_type"] is not None  # SearchType.hybrid

        # Verify Knowledge was created with PgVector
        mock_knowledge.assert_called_once_with(vector_db=mock_pgvector_instance)

        # Verify embedder was configured
        mock_embedder.assert_called_once()

    def test_get_knowledge_base_singleton(self) -> None:
        """Test that get_knowledge_base returns singleton instance."""
        with patch("pedroclaw.knowledge.agno_kb._kb_instance", None):
            with patch("pedroclaw.knowledge.agno_kb.create_knowledge_base") as mock_create:
                mock_kb = MagicMock()
                mock_create.return_value = mock_kb

                # First call should create instance
                kb1 = get_knowledge_base()
                mock_create.assert_called_once()

                # Second call should return same instance
                kb2 = get_knowledge_base()
                assert mock_create.call_count == 1  # Still only called once
                assert kb1 is kb2

    @patch("pedroclaw.knowledge.agno_kb.get_knowledge_base")
    async def test_search_knowledge(self, mock_get_kb: MagicMock) -> None:
        """Test search knowledge functionality."""
        # Mock knowledge base and search results
        mock_kb = MagicMock()
        mock_get_kb.return_value = mock_kb
        
        mock_results = [
            {
                "id": "doc1",
                "content": "Test content about authentication",
                "name": "Authentication Guide",
                "reranking_score": 0.95,
                "meta_data": {"source_type": "issue", "source_id": "123"}
            },
            {
                "id": "doc2", 
                "content": "Another relevant document",
                "name": "Security Policy",
                "reranking_score": 0.87,
                "meta_data": {"source_type": "mr", "source_id": "456"}
            }
        ]
        mock_kb.asearch.return_value = mock_results

        # Test search
        results = await search_knowledge("authentication issues", limit=5)

        # Verify search was called correctly
        mock_kb.asearch.assert_called_once_with("authentication issues", limit=5)

        # Verify results are formatted correctly
        assert len(results) == 2
        assert results[0]["id"] == "doc1"
        assert results[0]["title"] == "Authentication Guide"
        assert results[0]["content"] == "Test content about authentication"
        assert results[0]["score"] == 0.95
        assert results[0]["meta_data"]["source_type"] == "issue"

        assert results[1]["id"] == "doc2"
        assert results[1]["title"] == "Security Policy"
        assert results[1]["score"] == 0.87

    @patch("pedroclaw.knowledge.agno_kb.get_knowledge_base")
    async def test_search_knowledge_empty_results(self, mock_get_kb: MagicMock) -> None:
        """Test search with no results."""
        mock_kb = MagicMock()
        mock_get_kb.return_value = mock_kb
        mock_kb.asearch.return_value = []

        results = await search_knowledge("nonexistent query", limit=3)

        assert len(results) == 0
        mock_kb.asearch.assert_called_once_with("nonexistent query", limit=3)

    @patch("pedroclaw.knowledge.agno_kb.get_knowledge_base")
    async def test_search_knowledge_error_handling(self, mock_get_kb: MagicMock) -> None:
        """Test search error handling."""
        mock_kb = MagicMock()
        mock_get_kb.return_value = mock_kb
        mock_kb.asearch.side_effect = Exception("Search failed")

        # Should not raise exception, but return empty list
        results = await search_knowledge("test query", limit=5)

        assert len(results) == 0
        mock_kb.asearch.assert_called_once_with("test query", limit=5)


class TestKnowledgeAdapter:
    """Test knowledge adapter functions for backward compatibility."""

    @patch("pedroclaw.knowledge.agno_store.get_knowledge_base")
    async def test_upsert_entry(self, mock_get_kb: MagicMock) -> None:
        """Test upsert_entry adapter function."""
        mock_kb = MagicMock()
        mock_get_kb.return_value = mock_kb

        from pedroclaw.knowledge.agno_store import upsert_entry

        await upsert_entry(
            source_type="issue",
            source_id=123,
            project_id=1,
            title="Test Issue",
            content="Issue description",
            labels=["bug", "critical"],
            resolution="Fixed by updating dependencies"
        )

        # Verify ainsert was called with correct parameters
        mock_kb.ainsert.assert_called_once()
        call_args = mock_kb.ainsert.call_args
        assert "text" in call_args.kwargs
        assert "Test Issue" in call_args.kwargs["text"]
        assert "Issue description" in call_args.kwargs["text"]
        assert "bug" in call_args.kwargs["text"]
        assert "Fixed by updating dependencies" in call_args.kwargs["text"]
        
        # Verify metadata
        meta = call_args.kwargs["meta_data"]
        assert meta["source_type"] == "issue"
        assert meta["source_id"] == "123"
        assert meta["project_id"] == "1"
        assert meta["labels"] == ["bug", "critical"]
        assert meta["resolution"] == "Fixed by updating dependencies"

    @patch("pedroclaw.knowledge.agno_store.search_knowledge")
    async def test_search_similar_adapter(self, mock_search: MagicMock) -> None:
        """Test search_similar adapter function."""
        from pedroclaw.knowledge.agno_store import search_similar

        # Mock search results
        mock_search.return_value = [
            {
                "id": "doc1",
                "title": "Similar Issue",
                "content": "Content",
                "score": 0.92,
                "meta_data": {
                    "source_type": "issue",
                    "source_id": 456,
                    "labels": ["bug"],
                    "resolution": "Fixed"
                }
            }
        ]

        results = await search_similar(
            query_embedding=[0.1, 0.2, 0.3],  # Dummy embedding
            top_k=3,
            threshold=0.8
        )

        # Verify search was called
        mock_search.assert_called_once_with(query="", limit=3)

        # Verify results are formatted for old interface
        assert len(results) == 1
        assert results[0]["source_type"] == "issue"
        assert results[0]["source_id"] == 456
        assert results[0]["title"] == "Similar Issue"
        assert results[0]["score"] == 0.92
        assert results[0]["labels"] == ["bug"]
        assert results[0]["resolution"] == "Fixed"
