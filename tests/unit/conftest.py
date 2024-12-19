from unittest.mock import patch

import pytest


@pytest.fixture
def mock_chroma_settings():
    with patch("src.extract_embeddings.Settings") as mock_chroma_settings:
        yield mock_chroma_settings


@pytest.fixture
def mock_settings():
    with patch("src.extract_embeddings.settings") as mock_settings:
        yield mock_settings


@pytest.fixture
def mock_instructor():
    with patch(
        "src.extract_embeddings.INSTRUCTOR"
    ) as mock_sentence_transformer:
        yield mock_sentence_transformer


@pytest.fixture
def mock_settings_for_client():
    with patch("src.extract_embeddings.pd.read_parquet") as mock_read_parquet:
        return mock_read_parquet


@pytest.fixture
def mock_chroma_http_client():
    with patch(
        "src.extract_embeddings.chromadb.HttpClient"
    ) as mock_chroma_http_client:
        yield mock_chroma_http_client


@pytest.fixture
def mock_embedding_function():
    with patch(
        "src.extract_embeddings.ThesisEmbeddingFunction"
    ) as mock_embedding_function:
        yield mock_embedding_function


@pytest.fixture
def mock_read_parquet():
    with patch("src.extract_embeddings.pd.read_parquet") as mock_read_parquet:
        yield mock_read_parquet


@pytest.fixture
def mock_create_batches():
    with patch("src.extract_embeddings.create_batches") as mock_create_batches:
        yield mock_create_batches
