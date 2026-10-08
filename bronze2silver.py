import io
import json
import boto3
import pandas as pd

BUCKET_NAME = "s3-itops-sophie"
PREFIX_BRONZE = "01-bronze/"
PREFIX_SILVER = "02-silver/"

s3_client = boto3.client("s3")

def ler_bronze():
    registros = []

    resposta = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX_BRONZE)
    for obj in resposta.get("Contents", []):
        chave = obj["Key"]
        if chave.endswith(".json"):
            arquivo = s3_client.get_object(Bucket=BUCKET_NAME, Key=chave)
            conteudo = json.loads(arquivo["Body"].read().decode("utf-8"))
            registros.append(conteudo)

    return pd.DataFrame(registros)

# calcular a vazão em mbps
def calcular_vazao(df):
    # ordena para que cada disposit fique em ordem de tempo
    df = df.sort_values(["id_dispositivo", "timestamp"])

    # diff() = valor atual menos o valor da linha anterior (do mesmo dispositivo)
    diff_bytes = df.groupby("id_dispositivo")["bytes_sent"].diff()
    diff_segundos = df.groupby("id_dispositivo")["timestamp"].diff().dt.total_seconds()

    # bytes -> bits (x8) -> megabit (/1.000.000) -> por segundo
    df["mbps"] = diff_bytes * 8 / diff_segundos / 1_000_000
    return df

def definir_status(linha):
    alertas = []
    if linha["active_conn"] > 40:
        alertas.append("alta densidade")
    if linha["cpu_usage"] > 80:
        alertas.append("gargalo de processamento")
    if linha["ram_usage"] > 75:
        alertas.append("sem memoria")

    if len(alertas) == 0:
        return "normal"
    return "|".join(alertas)


def main():
    df = ler_bronze()
    if df.empty:
        print("Nenhum dado na Bronze.")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # a antena tem id_antena, o firewall nao, criamos uma coluna unica
    df["id_dispositivo"] = df["id_antena"].fillna("firewall")
    df["active_conn"] = df["active_conn"].fillna(0)
    df = calcular_vazao(df)
    df["status_carga"] = df.apply(definir_status, axis=1)
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    buffer = io.StringIO()
    df.to_csv(buffer, index=False, sep=";")
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=PREFIX_SILVER + "dados_consolidados.csv",
        Body=buffer.getvalue(),
    )
    print("CSV salvo na Silver!")

main()