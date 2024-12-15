FROM ghcr.io/mlflow/mlflow:v2.19.0

RUN pip install psycopg2-binary boto3

CMD ["bash"]
