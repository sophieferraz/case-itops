import json
import random
import time
from datetime import datetime
import boto3
import psutil

BUCKET_NAME = "s3-itops-sophie"
PREFIX_BRONZE = "01-bronze"
INTERVALO_SEGUNDOS = 60


s3_client = boto3.client("s3")

def capturar_metricas_firewall():
    io = psutil.net_io_counters()
    return {
        "timestamp": datetime.now().isoformat(),
        "tipo_dispositivo": "firewall",
        "active_sessions": random.randint(100, 500),
        "dropped_packets": random.randint(0, 50),
        "top_blocked_ip": f"192.168.1.{random.randint(100, 250)}",
        "cpu_usage": psutil.cpu_percent(interval=1),
        "ram_usage": psutil.virtual_memory().percent,
        "bytes_sent": io.bytes_sent,
        "bytes_recv": io.bytes_recv,
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

        try:
            dados = capturar_metricas_firewall()
            salvar_no_s3(dados, f"{texto}_firewall.json")
        except Exception as e:
            print(f"Erro ao enviar firewall: {e}")

        time.sleep(max(0, INTERVALO_SEGUNDOS - (time.time() - inicio)))

main()