from unittest.mock import MagicMock

import pandas as pd

from src.extract_embeddings import (
    ThesisEmbeddingFunction,
    add_documents_to_collection,
    create_chroma_client,
    create_thesis_collection,
    preprocess_thesis_data,
)


def test_embedding_function(mock_sentence_transformer, mock_settings):
    mock_settings.MODEL_NAME_OR_PATH = "test_model"
    mock_settings.DEVICE = "cpu"
    mock_model = MagicMock()
    mock_model.encode.return_value = [1, 2, 3]
    mock_sentence_transformer.return_value = mock_model

    embedding_function = ThesisEmbeddingFunction()
    documents = ["exemplo de resumo de tese"]
    embedding_function(documents)

    mock_sentence_transformer.assert_called_once_with(
        "test_model", device="cpu"
    )
    mock_model.encode.assert_called_once_with(documents)


def test_create_chroma_client(mock_chroma_http_client, mock_chroma_settings):
    auth_provider = "test_provider"
    auth_credentials = "test_credentials"
    host = "localhost"
    port = 8000

    create_chroma_client.fn(
        host=host,
        port=port,
        auth_provider=auth_provider,
        auth_credentials=auth_credentials,
    )
    mock_chroma_http_client.assert_called_once_with(
        host=host,
        port=port,
        settings=mock_chroma_settings(
            chroma_client_auth_provider=auth_provider,
            chroma_client_auth_credentials=auth_credentials,
        ),
    )


def test_create_thesis_collection(mock_embedding_function):
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    collection = create_thesis_collection.fn(mock_client)

    mock_client.get_or_create_collection.assert_called_once_with(
        name="thesis_capes", embedding_function=mock_embedding_function()
    )
    assert collection == mock_collection


def test_preprocess_thesis_data(mock_read_parquet):
    data = {
        "AN_BASE": [2024],
        "SG_ENTIDADE_ENSINO": ["UNI"],
        "NM_ENTIDADE_ENSINO": ["UNIVERSIDADE"],
        "NM_PRODUCAO": ["Um título de tese"],
        "NM_SUBTIPO_PRODUCAO": ["Tese"],
        "NM_GRAU_ACADEMICO": ["Doutorado"],
        "NM_REGIAO": ["Região de Teste"],
        "SG_UF_IES": ["RT"],
        "NM_UF_IES": ["UF de Teste"],
        "NM_GRANDE_AREA_CONHECIMENTO": ["Ciências Exatas e da Terra"],
        "NM_AREA_CONHECIMENTO": ["Ciência da Computação"],
        "DS_RESUMO": ["Um resumo de tese"],
    }
    df = pd.DataFrame(data)
    mock_read_parquet.return_value = df

    processed_df = preprocess_thesis_data.fn("test_path")

    mock_read_parquet.assert_called_once_with(
        "test_path",
        columns=[
            "AN_BASE",
            "SG_ENTIDADE_ENSINO",
            "NM_ENTIDADE_ENSINO",
            "NM_PRODUCAO",
            "NM_SUBTIPO_PRODUCAO",
            "NM_GRAU_ACADEMICO",
            "NM_REGIAO",
            "SG_UF_IES",
            "NM_UF_IES",
            "NM_GRANDE_AREA_CONHECIMENTO",
            "NM_AREA_CONHECIMENTO",
            "DS_RESUMO",
        ],
    )
    assert not processed_df.empty
    assert "id" in processed_df.columns


def test_add_documents_to_collection(mock_create_batches):
    mock_client = MagicMock()
    mock_collection = MagicMock()
    ids = ["id1"]
    documents = ["resumo de tese"]
    metadatas = [{"meta": "data"}]

    mock_batch = (ids, None, metadatas, documents)
    mock_create_batches.return_value = [mock_batch]

    add_documents_to_collection.fn(
        mock_client, mock_collection, ids, documents, metadatas
    )

    mock_create_batches.assert_called_once_with(
        api=mock_client, ids=ids, documents=documents, metadatas=metadatas
    )
    mock_collection.add.assert_called_once_with(
        ids=ids, documents=documents, metadatas=metadatas
    )
