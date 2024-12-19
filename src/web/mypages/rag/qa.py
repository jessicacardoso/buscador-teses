import datetime as dt
import json
from functools import wraps

import pandas as pd
import streamlit as st
from chromadb.api.models.Collection import Collection
from openai import OpenAI

from src.config import settings
from src.extract_embeddings import (
    create_chroma_client,
    create_thesis_collection,
)


def log_step(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        tic = dt.datetime.now()
        result = func(*args, **kwargs)
        time_taken = str(dt.datetime.now() - tic)
        print(f"just ran step {func.__name__} took {time_taken}s")
        return result

    return wrapper


def load_prompts():
    with open("src/assets/prompt-text-to-chroma.txt", encoding="utf-8") as f:
        prompt_chroma = f.read()

    with open("src/assets/prompt-rag.txt", encoding="utf-8") as f:
        prompt_rag = f.read()

    return prompt_chroma, prompt_rag


@st.cache_resource
def load_prompts_with_cache() -> tuple[str, str]:
    return load_prompts()


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


@log_step
def search_documents(
    collection: Collection,
    query: str,
    where: dict = None,
    n_results=20,
) -> list[dict]:
    """Realiza uma busca na coleção de documentos.

    Args:
        collection (Collection): Objeto da coleção de documentos.
        query (str): Texto da consulta.
        where (dict, optional): Filtros da consulta. Defaults to None.
        n_results (int, optional): Número de resultados. Defaults to 20.
    """
    try:
        results = collection.query(
            query_texts=[query],
            where=where,
            n_results=n_results,
        )
        return [item for items in results["metadatas"] for item in items]
    except ValueError:
        return []


@log_step
def get_agent_response(text: str, prompt: str, client: OpenAI) -> dict:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(
        completion.choices[0].message.content.strip("```json").strip("```")
    )


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

    client = OpenAI()
    collection = load_collection()

    prompt_chroma, prompt_rag = load_prompts_with_cache()
    search = st.text_input("Faça uma consulta:")

    if st.button("🔍 Buscar", type="tertiary") and search.strip():
        with st.spinner("Montando consulta..."):
            chroma_query = get_agent_response(search, prompt_chroma, client)
            print(chroma_query)
        with st.spinner("Recuperando dados..."):
            results = search_documents(collection, **chroma_query)
            final_query = f"""
            - Query: {search}
            - Documents:
            {results}
            """
            response = get_agent_response(final_query, prompt_rag, client)

        answer = response.get(
            "answer", "Não foi possível encontrar uma resposta."
        )
        ids = response.get("ids", [])
        st.write(answer)
        if ids:
            df = pd.DataFrame(results)
            df = df[df["id"].isin(ids)][
                [
                    "AN_BASE",
                    "NM_PRODUCAO",
                    "DS_RESUMO",
                    "NM_AREA_CONHECIMENTO",
                    "NM_GRANDE_AREA_CONHECIMENTO",
                    "NM_GRAU_ACADEMICO",
                    "SG_ENTIDADE_ENSINO",
                    "SG_UF_IES",
                ]
            ]

            df = df.rename(
                columns={
                    "AN_BASE": "Ano",
                    "NM_PRODUCAO": "Título",
                    "DS_RESUMO": "Resumo",
                    "NM_AREA_CONHECIMENTO": "Área de Conhecimento",
                    "NM_GRANDE_AREA_CONHECIMENTO": "Grande Área de Conhecimento",  # noqa
                    "NM_GRAU_ACADEMICO": "Grau Acadêmico",
                    "SG_ENTIDADE_ENSINO": "Sigla da Instituição",
                    "SG_UF_IES": "Sigla do Estado da Instituição",
                }
            )

            st.write(df)
