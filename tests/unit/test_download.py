import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import vcr
from prefect.testing.utilities import prefect_test_harness

from src.download import (
    download,
    filter_datasets,
    generate_flow_run_name,
    generate_task_name,
    get_all_datasets_with_resources,
    get_resource_etag,
    load_and_process_data,
    main,
)

my_vcr = vcr.VCR(
    cassette_library_dir="tests/fixtures/vcr_cassettes",
    record_mode="once",
)


@patch("src.download.datetime")
@patch("src.download.flow_run")
def test_generate_flow_run_name(mock_flow_run, mock_datetime):
    mock_flow_run.flow_name = "test_flow"
    mock_datetime.datetime.now.return_value = datetime.datetime(2024, 12, 25)
    result = generate_flow_run_name()
    assert result == "test_flow_2024-12-25T00:00:00"


@patch("src.download.flow_run")
@patch("src.download.task_run")
def test_generate_task_name(mock_task_run, mock_flow_run):
    mock_flow_run.flow_name = "test_flow"
    mock_task_run.task_name = "test_task"
    mock_task_run.parameters = {
        "url": "https://dadosabertos.capes.gov.br/catalogo.xlsx"
    }
    result = generate_task_name()
    assert result == "test_flow-test_task_catalogo.xlsx"


@my_vcr.use_cassette("get_all_datasets_with_resources.yaml")
def test_get_all_datasets_with_resources():
    result = get_all_datasets_with_resources.fn()
    expected_url = "https://dadosabertos.capes.gov.br/dataset/{package_id}/resource/{id}/download/{name}.csv"
    assert isinstance(result, pd.DataFrame)
    assert not result.empty

    assert "name" in result.columns
    assert "package_id" in result.columns
    assert "id" in result.columns
    assert "url" in result.columns

    # URL Esperada
    expected_url = expected_url.format(
        package_id=result["package_id"].iloc[0],
        id=result["id"].iloc[0],
        name=result["name"].iloc[0].lower(),
    )
    assert expected_url in result["url"].iloc[0]


def test_filter_datasets():
    data = {
        "format": ["XLSX", "CSV"],
        "dataset_name": ["Catálogo de Teses e Dissertações", "Outro Dataset"],
        "description": ["Ano 2020", "Ano 2019"],
        "url": [
            "http://example.com/file1.xlsx",
            "http://example.com/file2.pdf",
        ],
    }
    df = pd.DataFrame(data)
    result = filter_datasets.fn(df)
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert result.shape[0] == 1
    assert result.iloc[0]["url"] == "http://example.com/file1.xlsx"


@patch("src.download.requests.head")
def test_get_resource_etag(mock_head):
    mock_response = MagicMock()
    mock_response.headers = {"ETag": "12345"}
    mock_head.return_value = mock_response
    result = get_resource_etag.fn("http://example.com/file.xlsx")
    assert result == "12345"


@patch("src.download.requests.get")
@patch("src.download.requests.head")
@patch("src.download.os.makedirs")
@patch("src.download.so.open")
def test_download(mock_head, mock_get, mock_mkdir, mock_open):
    mock_head.return_value.headers = {"content-length": "1024"}
    mock_response = MagicMock()
    mock_response.iter_content = lambda: [b"data"] * 128
    mock_get.return_value = mock_response

    mock_mkdir.return_value = MagicMock()

    mock_open.return_value.__enter__.return_value = MagicMock()
    mock_open.return_value.__enter__.return_value.write = MagicMock()

    result = download.fn(
        "http://example.com/file.xlsx", output_dir="./test_data"
    )
    assert result == "./test_data/file.xlsx"


@patch("src.download.pd.read_excel")
@patch("src.download.pd.concat")
@patch("src.download.pd.DataFrame.to_parquet")
def test_load_and_process_data(mock_to_parquet, mock_concat, mock_read_excel):
    data = [
        {
            "AN_BASE": 2013,
            "ID_PRODUCAO_INTELECTUAL": 98980,
            "DH_INICIO_AREA_CONC": "01/01/2012 00:00:00",
            "DH_FIM_AREA_CONC": "11/11/2015 00:00:00",
            "DH_INICIO_LINHA": pd.NA,
            "DH_FIM_LINHA": pd.NA,
            "DT_TITULACAO": "16/04/2013 00:00:00",
            "DT_MATRICULA": "01/03/2011 00:00:00",
        },
        {
            "AN_BASE": 2013,
            "ID_PRODUCAO_INTELECTUAL": 97334,
            "DH_INICIO_AREA_CONC": "01/01/2011 00:00:00",
            "DH_FIM_AREA_CONC": pd.NA,
            "DH_INICIO_LINHA": "01/01/2011 00:00:00",
            "DH_FIM_LINHA": pd.NA,
            "DT_TITULACAO": "16/08/2013 00:00:00",
            "DT_MATRICULA": "29/03/2011 00:00:00",
        },
    ]
    df = pd.DataFrame(data)
    mock_concat.return_value = df
    mock_to_parquet.return_value = df
    mock_read_excel.return_value = df

    load_and_process_data.fn(output_dir="./test_data")

    mock_concat.assert_called_once()


@patch("src.download.get_all_datasets_with_resources")
@patch("src.download.filter_datasets")
@patch("src.download.get_resource_etag")
@patch("src.download.download")
@patch("src.download.load_and_process_data")
def test_main(
    mock_load_and_process_data,
    mock_download,
    mock_get_resource_etag,
    mock_filter_datasets,
    mock_get_all_datasets_with_resources,
):
    urls = [f"http://example.com/catalogo{i}.xlsx" for i in range(1, 5)]
    etags = [f"etag{i}" for i in range(1, 5)]

    mock_df = pd.DataFrame({"url": urls})
    mock_get_all_datasets_with_resources.return_value = mock_df
    mock_filter_datasets.return_value = mock_df

    mock_get_resource_etag.side_effect = etags

    mock_load_and_process_data.return_value = None

    with prefect_test_harness():
        main(output_dir="./test_data")

    mock_get_all_datasets_with_resources.assert_called_once()
    mock_filter_datasets.assert_called_once_with(mock_df)
    for url in urls:
        mock_get_resource_etag.assert_any_call(url)

    for url, etag in zip(urls, etags):
        mock_download.assert_any_call(url, etag=etag, output_dir="./test_data")
