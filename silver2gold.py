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
# 3 - mapa de calor (qual antena consome mais internet)
# mbps médio de cada antena
mapa = antenas.groupby("id_dispositivo")["mbps"].mean()
mapa = mapa.reset_index()

# quanto cada antena representa do total (em %)
total = mapa["mbps"].sum()
mapa["percentual_do_total"] = mapa["mbps"] / total * 100

# a que mais consome fica em primeiro
mapa = mapa.sort_values("percentual_do_total", ascending=False)
mapa = mapa.round(2)

mapa.to_csv("relatorio_mapa_de_calor.csv", index=False, sep=";")
s3_client.upload_file(
    "relatorio_mapa_de_calor.csv", BUCKET_NAME, PREFIX_GOLD + "relatorio_mapa_de_calor.csv"
)

# cruzando com o firewall: o que sai pela internet
firewall_ok = firewall[firewall["mbps"] >= 0]
print("Mbps médio das antenas (soma):", round(total, 4))
print("Mbps médio de saída do firewall:", round(firewall_ok["mbps"].mean(), 4))

# 4 - gargalo de saída (CPU do firewall x sessões ativas)

# separa em dois grupos: CPU alta e CPU normal
cpu_alta = firewall[firewall["cpu_usage"] > 80]
cpu_normal = firewall[firewall["cpu_usage"] <= 80]

# correlação: perto de 1 = quando as sessões sobem, a CPU sobe junto
correlacao = firewall["cpu_usage"].corr(firewall["active_sessions"])

gargalo = pd.DataFrame(
    {
        "situacao": ["CPU acima de 80%", "CPU até 80%"],
        "sessoes_ativas_medias": [
            cpu_alta["active_sessions"].mean(),
            cpu_normal["active_sessions"].mean(),
        ],
        "qtd_medicoes": [len(cpu_alta), len(cpu_normal)],
        "correlacao_cpu_sessoes": [correlacao, correlacao],
    }
)
gargalo = gargalo.round(2)

gargalo.to_csv("relatorio_gargalo_saida.csv", index=False, sep=";")
s3_client.upload_file(
    "relatorio_gargalo_saida.csv", BUCKET_NAME, PREFIX_GOLD + "relatorio_gargalo_saida.csv"
)

print("Relatórios enviados para a camada Gold!")