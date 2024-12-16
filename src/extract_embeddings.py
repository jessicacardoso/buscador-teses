import hashlib

import chromadb
import pandas as pd
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.config import Settings
from chromadb.utils.batch_utils import create_batches
from prefect import flow, task
from prefect.cache_policies import INPUTS
from sentence_transformers import SentenceTransformer
from tqdm.auto import tqdm

from src.config import settings


class ThesisEmbeddingFunction(EmbeddingFunction):
    """Extração de embeddings dos resumos das teses.

    Esta classe é responsável por extrair os embeddings dos resumos das teses
    utilizando um modelo de linguagem pré-treinado.
    """

    def __init__(self) -> None:
        self.model = SentenceTransformer(
            settings.MODEL_NAME_OR_PATH, device=settings.DEVICE
        )

    def __call__(self, documents: Documents) -> Embeddings:
        """Recebe uma lista de documentos e retorna os embeddings.

        Args:
            documents (Documents): Uma lista de documentos, no caso, os
            resumos das teses.

        Returns:
            Uma lista de embeddings correspondentes aos documentos.
        """

        return self.model.encode(documents)


@task
def create_chroma_client(
    host: str, port: int, auth_provider: str, auth_credentials: str
) -> chromadb.HttpClient:
    """Crie um cliente ChromaDB.

    Args:
        host (str): O endereço do servidor ChromaDB.
        port (int): A porta do servidor ChromaDB.
        auth_provider (str): O provedor de autenticação.
        auth_credentials (str): As credenciais de autenticação.

    Returns:
        Uma instância de `chromadb.HttpClient` definida com as configurações
    """

    return chromadb.HttpClient(
        host=host,
        port=port,
        settings=Settings(
            chroma_client_auth_provider=auth_provider,
            chroma_client_auth_credentials=auth_credentials,
        ),
    )


@task(cache_policy=None)
def create_thesis_collection(
    client: chromadb.HttpClient,
) -> chromadb.Collection:
    """Cria uma coleção no ChromaDB para armazenar os embeddings das teses.

    Args:
        client (HttpClient): Um cliente ChromaDB.

    Returns:
        Uma instância de `chromadb.Collection`.
    """

    return client.get_or_create_collection(
        name="thesis_capes", embedding_function=ThesisEmbeddingFunction()
    )


@task(
    name="Pré-processamento dos dados das teses",
    description="Gera o identificador único para cada tese e seleciona colunas de interesse.",  # noqa
    cache_policy=INPUTS,
)
def preprocess_thesis_data(file_path: str) -> pd.DataFrame:
    """Pré-processamento dos dados das teses.

    Args:
        file_path (str): O caminho do arquivo contendo o conjunto de dados.

    Returns:
        Um DataFrame contendo registros únicos e sem valores nulos no
        campo do resumo.
    """

    print("Carregando dados...")
    df = pd.read_parquet(
        file_path,
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
    print("Removendo registros duplicados e valores nulos nos resumos...")
    df = df.drop_duplicates()
    df = df.dropna(subset=["DS_RESUMO"])

    print("Gerando identificadores únicos...")
    df["id"] = df.apply(
        lambda x: hashlib.md5(
            "_".join([str(value) for value in x.values]).encode(),
            usedforsecurity=False,
        ).hexdigest(),
        axis=1,
    )
    return df


@task(
    name="Adição de documentos à coleção",
    description="Armazena os embeddings das teses no ChromaDB.",
    cache_policy=None,
)
def add_documents_to_collection(
    chroma_client: chromadb.HttpClient,
    collection: chromadb.Collection,
    ids: list[str],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    """Adiciona os documentos e metadados à coleção.

    Args:
        chroma_client (HttpClient): Um cliente ChromaDB.
        collection (Collection): Coleção onde os documentos serão adicionados.
        ids (list[str]): Lista contendo os identificadores únicos de cada
        trabalho.
        documents (list[str]): Lista contendo os resumos das teses.
        metadatas (list[dict]): Uma lista de metadados associados as teses
        e dissertações.
    """

    batches = create_batches(
        api=chroma_client, ids=ids, documents=documents, metadatas=metadatas
    )
    for batch in tqdm(batches, desc="Adding documents"):
        batch_ids, _, batch_metadatas, batch_documents = batch
        collection.add(
            ids=batch_ids, documents=batch_documents, metadatas=batch_metadatas
        )


@flow(
    name="Extração de embeddings das teses",
)
def main(file_path: str = "./data/catalogo_de_teses_e_dissertacoes") -> None:
    chroma_client = create_chroma_client(
        host=settings.CHROMA_CLIENT_HOSTNAME,
        port=settings.CHROMA_CLIENT_PORT,
        auth_provider=settings.CHROMA_CLIENT_AUTH_PROVIDER,
        auth_credentials=(
            settings.CHROMA_CLIENT_AUTH_CREDENTIALS.get_secret_value()
        ),
    )
    collection = create_thesis_collection(client=chroma_client)

    df = preprocess_thesis_data(file_path=file_path)

    ids = df["id"].tolist()
    documents = df["DS_RESUMO"].tolist()
    metadatas = df.to_dict(orient="records")

    add_documents_to_collection(
        chroma_client=chroma_client,
        collection=collection,
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )
