from unittest import mock

import pytest

from src.web.mypages.rag.qa import (
    get_agent_response,
    load_prompts,
    search_documents,
)


def test_load_prompts():
    prompt_chroma = "Prompt para o Chroma"
    prompt_rag = "Prompt para o RAG"
    mock_files = mock.mock_open()
    mock_files.side_effect = lambda filename, *args, **kwargs: {
        "src/assets/prompt-text-to-chroma.txt": mock.mock_open(
            read_data=prompt_chroma
        )(),
        "src/assets/prompt-rag.txt": mock.mock_open(read_data=prompt_rag)(),
    }[filename]

    with mock.patch("builtins.open", mock_files):
        chroma_prompt, rag_prompt = load_prompts()

    assert chroma_prompt == prompt_chroma
    assert rag_prompt == prompt_rag


def test_search_documents_success():
    collection = mock.Mock()
    collection.query.return_value = {
        "metadatas": [
            [{"id": 1, "title": "Document 1"}],
            [{"id": 2, "title": "Document 2"}],
        ]
    }

    results = search_documents(collection, query="test_query")

    assert results == [
        {"id": 1, "title": "Document 1"},
        {"id": 2, "title": "Document 2"},
    ]


def test_get_agent_response_success():
    client = mock.Mock()
    completion = mock.Mock()
    completion.choices = [
        mock.Mock(message=mock.Mock(content='{"answer": "Está é a resposta"}'))
    ]
    client.chat.completions.create.return_value = completion

    response = get_agent_response(
        text="user question", prompt="system prompt", client=client
    )

    assert response == {"answer": "Está é a resposta"}


def test_get_agent_response_invalid_json():
    client = mock.Mock()
    completion = mock.Mock()
    completion.choices = [
        mock.Mock(message=mock.Mock(content="Não retornou JSON"))
    ]
    client.chat.completions.create.return_value = completion

    with pytest.raises(ValueError):
        get_agent_response(
            text="user question", prompt="system prompt", client=client
        )
