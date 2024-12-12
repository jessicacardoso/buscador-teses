"""Script para download de arquivos do Catálogo de Teses e Dissertações da
CAPES a partir de 2013."""

import datetime
from pathlib import Path

import pandas as pd
import requests
from prefect import flow, task
from prefect.cache_policies import INPUTS
from prefect.runtime import flow_run, task_run
from tqdm.auto import tqdm

CAPES_API_URL = "https://dadosabertos.capes.gov.br/api/3/action"
TIMEOUT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0",  # noqa
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",  # noqa
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "host": "dadosabertos.capes.gov.br",
}
DT_FORMAT = "%d/%m/%Y %H:%M:%S"


def generate_flow_run_name():
    """
    Gera o nome do fluxo de execução.
    """
    flow_name = flow_run.flow_name
    date = datetime.datetime.now(datetime.timezone.utc)
    date = date.isoformat()
    return f"{flow_name}_{date}"


def generate_task_name():
    """
    Gera o nome da tarefa de execução.
    """
    flow_name = flow_run.flow_name
    task_name = task_run.task_name
    parameters = task_run.parameters
    filename = parameters["url"].split("/")[-1]

    return f"{flow_name}-{task_name}_{filename}"


@task(
    name="Obter todos os conjuntos de dados com recursos",
    retries=3,
    retry_delay_seconds=5,
)
def get_all_datasets_with_resources(
    q: str = "catalogo-de-teses-e-dissertacoes",
    rows: int = 10,
) -> pd.DataFrame:
    """Obtém todos os conjuntos de dados com recursos.

    Args:
        q (str, optional): grupo de conjuntos de dados. Defaults to
        "catalogo-de-teses-e-dissertacoes".
        rows (int, optional): quantidade de registros. Defaults to 10.

    Returns:
        pd.DataFrame: retorna um DataFrame com os conjuntos de dados
    """

    # Obter todos os conjuntos de dados com recursos
    response = requests.get(
        f"{CAPES_API_URL}/package_search",
        params={"q": q, "rows": rows},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r_json = response.json()
    datasets = r_json["result"]["results"]

    # Obter todos os recursos
    resources = []
    for dataset in datasets:
        for resource in dataset["resources"]:
            resource["dataset_name"] = dataset["title"]
            resources.append(resource)

    # Converter para DataFrame
    df = pd.DataFrame(resources)
    return df


@task(
    name="Filtrar catalogo de teses e dissertações",
    description="Filtrar para baixar os arquivos a partir de 2013.",
)
def filter_datasets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra o catalogo de teses e dissertações para baixar apenas os arquivos
    a partir de 2013.

    Parameters:
    df (pd.DataFrame): DataFrame com os conjuntos de dados.

    Returns:
    pd.DataFrame: retorna um DataFrame filtrado.
    """
    filtered_df = df.loc[
        (df["format"] == "XLSX")
        & (df["dataset_name"].str.contains("Catálogo de Teses e Dissertações"))
        & (df["description"].str.contains("Ano 20"))
    ]
    return filtered_df


@task(
    name="Obter ETag do recurso",
    description="Obtém o ETag para fins de cache.",
)
def get_resource_etag(url: str) -> str:
    """Obtém o ETag de um recurso.

    Args:
        url (str): URL do recurso.

    Returns:
        str: retorna o ETag do recurso.
    """
    response = requests.head(url, headers=HEADERS, timeout=TIMEOUT)
    return response.headers.get("ETag")


@task(
    name="Download de arquivo",
    description="Realiza o download de um arquivo.",
    retries=3,
    retry_delay_seconds=[1, 10, 100],
    log_prints=True,
    cache_policy=INPUTS,
    cache_expiration=datetime.timedelta(days=7),
    task_run_name=generate_task_name,
)
def download(
    url: str, output_dir: str = "./data", etag: str | None = None
) -> str:
    """Realiza o download de um arquivo.

    Args:
        url (str): url do arquivo
        dest_dir (str, optional): diretório de destino. Defaults to "./data".

    Returns:
        str: caminho do arquivo baixado
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = Path(output_dir) / url.split("/")[-1]

    response_headers = requests.head(url, timeout=TIMEOUT).headers
    total = int(response_headers.get("content-length", 0))

    with open(filename, "wb") as f:
        with requests.get(
            url, stream=True, headers=HEADERS, timeout=TIMEOUT
        ) as r:
            r.raise_for_status()
            tqdm_params = {
                "desc": url.split("/")[-1],
                "total": total,
                "miniters": 1,
                "unit": "B",
                "unit_scale": True,
                "unit_divisor": 1024,
                "leave": True,
            }
            with tqdm(**tqdm_params) as pb:
                for chunk in r.iter_content(chunk_size=8192):
                    pb.update(len(chunk))
                    f.write(chunk)
    del etag
    return str(filename)


@task(
    name="Carregar e processar dados",
    description="Unir os catálogos de teses e dissertações e salvar em parquet.",  # noqa
    log_prints=True,
)
def load_and_process_data(output_dir: str = "./data") -> None:
    """Carrega e processa os dados do Catálogo de Teses e Dissertações.

    Args:
        output_dir (str, optional): diretório dos dados. Defaults to "data".
    """
    output_dir = Path(output_dir)
    files = list(output_dir.glob("*.xlsx"))
    dfs = []

    print("Carregando catálogos de teses e dissertações...")
    for file in files:
        df = pd.read_excel(file)
        dfs.append(df)

    print("Unindo conjunto de dados...")
    df = pd.concat(dfs, ignore_index=True)

    df["DH_INICIO_AREA_CONC"] = pd.to_datetime(
        df["DH_INICIO_AREA_CONC"], format=DT_FORMAT
    )
    df["DH_FIM_AREA_CONC"] = pd.to_datetime(
        df["DH_FIM_AREA_CONC"], format=DT_FORMAT
    )
    df["DH_INICIO_LINHA"] = pd.to_datetime(
        df["DH_INICIO_LINHA"], format=DT_FORMAT
    )
    df["DH_FIM_LINHA"] = pd.to_datetime(df["DH_FIM_LINHA"], format=DT_FORMAT)
    df["DT_TITULACAO"] = pd.to_datetime(df["DT_TITULACAO"], format=DT_FORMAT)
    df["DT_MATRICULA"] = pd.to_datetime(df["DT_MATRICULA"], format=DT_FORMAT)

    print("Salvando em parquet...")
    df = df.drop_duplicates()
    df.to_parquet(output_dir / "catalogo_de_teses_e_dissertacoes.parquet")


@flow(
    name="Download do Catálogo de Teses e Dissertações",
    flow_run_name=generate_flow_run_name,
)
def main(output_dir: str = "./data") -> None:
    """Realiza o download dos arquivos do Catálogo de Teses e Dissertações.

    Args:
        output_dir (str, optional): diretório de destino. Defaults to "./data".
    """
    df = get_all_datasets_with_resources().pipe(filter_datasets)
    urls = df["url"].to_list()
    for url in urls:
        etag = get_resource_etag(url)
        download(url, etag=etag, output_dir=output_dir)
    load_and_process_data(output_dir)
