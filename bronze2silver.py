import io
import json
import boto3
import pandas as pd

BUCKET_NAME = "s3-itops-sophie"  
PREFIX_BRONZE = "01-bronze/"
PREFIX_SILVER = "02-silver/"

s3_client = boto3.client("s3")

def processar_bronze_para_silver():
    response = s3_client.list_objects_v2(
        Bucket=BUCKET_NAME, Prefix=PREFIX_BRONZE
    )

    if "Contents" not in response:
        print("Nenhum arquivo encontrado na camada Bronze.")
        return

    registros = []
    for obj in response["Contents"]:
        key = obj["Key"]
        if key.endswith(".json"):
            res = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
            conteudo = json.loads(res["Body"].read().decode("utf-8"))
            registros.append(conteudo)

    df = pd.DataFrame(registros)

    if df.empty:
        print("O DataFrame está vazio.")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    for col in ["active_conn", "cpu_usage", "ram_usage"]:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = df[col].fillna(0)

    def calcular_status_carga(row):
        alertas = []
        if row["active_conn"] > 40:
            alertas.append("alta densidade")
        if row["cpu_usage"] > 80:
            alertas.append("gargalo de processamento")
        if row["ram_usage"] > 75:
            alertas.append("OOM")
        return "|".join(alertas) if alertas else "normal"

    df["status_carga"] = df.apply(calcular_status_carga, axis=1)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, sep=";")

    chave_destinatario = f"{PREFIX_SILVER}dados_processados.csv"
    s3_client.put_object(
        Bucket=BUCKET_NAME, Key=chave_destinatario, Body=csv_buffer.getvalue()
    )
    print(f"Dados consolidados em: s3://{BUCKET_NAME}/{chave_destinatario}")

processar_bronze_para_silver()