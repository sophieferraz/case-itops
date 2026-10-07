import json
import random
import time
from datetime import datetime
import boto3
import psutil

BUCKET_NAME = "s3-itops-sophie"
PREFIX_BRONZE = "01-bronze"
INTERVALO_SEGUNDOS = 60
ANTENAS = ["ap_01", "ap_02", "ap_03"]
PESOS = {"ap_01": 0.5, "ap_02": 0.3, "ap_03": 0.2}

s3_client = boto3.client("s3")

def capturar_metricas_antena(id_antena):
    io = psutil.net_io_counters()
    return {
        "timestamp": datetime.now().isoformat(),
        "tipo_dispositivo": "antena",
        "id_antena": id_antena,
        "bytes_sent": int(io.bytes_sent * PESOS[id_antena]),
        "bytes_recv": int(io.bytes_recv * PESOS[id_antena]),
        "active_conn": random.randint(5, 50),
        "cpu_usage": psutil.cpu_percent(interval=1),
        "ram_usage": psutil.virtual_memory().percent,
    }

def salvar_no_s3(dados, nome_arquivo):
    chave = f"{PREFIX_BRONZE}/{nome_arquivo}"
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=chave,
        Body=json.dumps(dados),
        ContentType="application/json",
    )
    print(f"Enviado: s3://{BUCKET_NAME}/{chave}")

def main():
    while True:
        inicio = time.time()
        texto = datetime.now().strftime("%Y-%m-%d_%H-%M")

        for ap in ANTENAS:
            try:
                dados = capturar_metricas_antena(ap)
                nome = f"{texto}_{ap.replace('_', '')}.json" 
                salvar_no_s3(dados, nome)
            except Exception as e:
                print(f"Erro ao enviar {ap}: {e}")

        time.sleep(max(0, INTERVALO_SEGUNDOS - (time.time() - inicio)))

main()