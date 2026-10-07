import boto3
import pandas as pd
 
BUCKET_NAME = "s3-itops-sophie"
ARQUIVO_SILVER = "02-silver/dados_consolidados.csv"
PREFIX_GOLD = "03-gold/"
 
s3_client = boto3.client("s3")
 
resposta = s3_client.get_object(Bucket=BUCKET_NAME, Key=ARQUIVO_SILVER)
df = pd.read_csv(resposta["Body"], sep=";")
 
# separa a tabela em duas: antenas e firewall
antenas = df[df["tipo_dispositivo"] == "antena"].copy()
firewall = df[df["tipo_dispositivo"] == "firewall"].copy()
 
# tira os valores de mbps vazios ou negativos
antenas = antenas[antenas["mbps"] >= 0]
 
# 1 - zonas mortas (quais antenas tem menos trafego)
zonas_mortas = antenas.groupby("id_dispositivo")["mbps"].mean()
zonas_mortas = zonas_mortas.reset_index()
zonas_mortas = zonas_mortas.sort_values("mbps")
 
zonas_mortas.to_csv("relatorio_zonas_mortas.csv", index=False, sep=";")
s3_client.upload_file(
    "relatorio_zonas_mortas.csv", BUCKET_NAME, PREFIX_GOLD + "relatorio_zonas_mortas.csv"
)

# 2 - pacotes bloqueados pelo firewall por hora
# os 13 primeiros caracteres do timestamp são a data + hora: "2026-04-06 10"
firewall["hora"] = firewall["timestamp"].str[:13]

bloqueados = firewall.groupby("hora")["dropped_packets"].sum()
bloqueados = bloqueados.reset_index()

bloqueados.to_csv("relatorio_pacotes_bloqueados.csv", index=False, sep=";")
s3_client.upload_file(
    "relatorio_pacotes_bloqueados.csv",
    BUCKET_NAME,
    PREFIX_GOLD + "relatorio_pacotes_bloqueados.csv",
)