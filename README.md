# Buscador de Teses e Dissertações

É uma ferramenta que permite consultar informações sobre teses e dissertações do Brasil que se encontram disponíveis na Plataforma Sucupira e no Portal de Dados Abertos da CAPES.


## Tecnologias:

- [Prefect](https://www.prefect.io/)
- [ChromaDB](https://www.trychroma.com/)
- [MinIO](https://min.io/)
- [MLFlow](https://mlflow.org/)
- [Typer](https://typer.tiangolo.com/)
- [Postgres](https://www.postgresql.org/)
- [Docker](https://www.docker.com/)
- [uv](https://docs.astral.sh/uv/)

## Como executar o projeto

1. Realiza o clone do projeto
    ```bash
    https://github.com/jessicacardoso/buscador-teses.git
    ```

2. Instalar as dependências
    ```bash
    pip install -r requirements.txt
    ```

3. Exportar as variáveis de ambientes definidas no `.env.example`

4. Baixar os dados do Portal de Dados Abertos da CAPES

    ```bash
    typer src/download.py run --output-dir s3://teses/data/raw
    ```

5. Extrair embeddings e armazenar no ChromaDB
    ```bash
    typer src/extract_embeddings.py run --file-path s3://teses/data/raw/catalogo_de_teses_e_dissertacoes.parquet
    ```

6. Executar a aplicação
    ```bash
    streamlit run app.py
    ```

## Executando os testes

Nós utilizamos o nox para executar os testes nas versões 3.10, 3.11 e 3.12 do Python. Para executar os testes, use o comando abaixo na raiz do projeto:

```bash
nox
```
