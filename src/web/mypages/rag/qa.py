import streamlit as st
from chromadb.api.models.Collection import Collection

from src.config import settings
from src.extract_embeddings import (
    create_chroma_client,
    create_thesis_collection,
)


@st.cache_resource
def load_collection():
    """Carrega a coleção de teses e dissertações.

    Returns:
        Collection: Coleção de teses e dissertações no Chroma.
    """
    client = create_chroma_client.fn(
        host=settings.CHROMA_CLIENT_HOSTNAME,
        port=settings.CHROMA_CLIENT_PORT,
        auth_provider=settings.CHROMA_CLIENT_AUTH_PROVIDER,
        auth_credentials=(
            settings.CHROMA_CLIENT_AUTH_CREDENTIALS.get_secret_value()
        ),
    )
    collection = create_thesis_collection.fn(client)
    return collection


def search_documents(query: str, collection: Collection) -> dict:
    """Realiza uma busca na coleção de documentos.

    Args:
        query (str): Texto da consulta.
        collection (Collection): Objeto da coleção de documentos.
    """
    return collection.query(
        query_texts=[query],
        n_results=5,
    )


def ask(text: str, collection: Collection):
    """Realiza uma pergunta ao sistema.

    Args:
        text (str): Texto da pergunta.
        collection (Collection): Coleção de documentos.
    """
    result = search_documents(text, collection)
    ids = result.get("ids", [])
    metadatas = result.get("metadatas", [])

    ids = ids[0] if ids else []
    metadatas = metadatas[0] if metadatas else []

    return {
        "text": text,
        "answer": "Esses foram os documentos encontrados:",
        "documents": metadatas,
    }


def main():
    st.markdown(
        """
        <main class="home_container">
        <h1>Buscador de Teses e Dissertações 2013-2022</h1>
        Este é um buscador de teses e dissertações defendidas entre 2013 e 2022.
        Você pode fazer perguntas sobre um tema de interesse e o sistema tentará retornar
        os documentos mais relevantes.
        </main>
        """,  # noqa
        unsafe_allow_html=True,
    )

    collection = load_collection()
    search = st.text_input("Faça uma consulta:")

    if st.button("🔍 Buscar", type="tertiary") and search.strip():
        result = ask(search, collection)
        st.write(result["answer"])
        st.write(result["documents"])
