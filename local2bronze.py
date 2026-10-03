import json
import random
from datetime import datetime
import boto3
import psutil

BUCKET_NAME = "s3-itops-sophie"  
PREFIX_BRONZE = "01-bronze"

s3_client = boto3.client("s3")

def capturar_metricas_antena(id_antena="ap_01"):
    io_counters = psutil.net_io_counters()
    return {
        "timestamp": datetime.now().isoformat(),
        "tipo_dispositivo": "antena",
        "id_antena": id_antena,
        "bytes_sent": io_counters.bytes_sent,
        "bytes_recv": io_counters.bytes_recv,
        "active_conn": random.randint(5, 50),
        "cpu_usage": psutil.cpu_percent(interval=1),
        "ram_usage": psutil.virtual_memory().percent,
    }

def capturar_metricas_firewall():
    io_counters = psutil.net_io_counters()
    return {
        "timestamp": datetime.now().isoformat(),
        "tipo_dispositivo": "firewall",
        "active_sessions": random.randint(100, 500), # gera um número inteiro aleatório entre 100 e 500
        "dropped_packets": random.randint(0, 50),
        "top_blocked_ip": f"192.168.1.{random.randint(100, 250)}", # gera um IP aleatório
        "cpu_usage": psutil.cpu_percent(interval=1),
        "ram_usage": psutil.virtual_memory().percent,
        "bytes_sent": io_counters.bytes_sent,
        "bytes_recv": io_counters.bytes_recv,
    }

def salvar_no_s3(dados, nome_arquivo):
    chave_s3 = f"{PREFIX_BRONZE}/{nome_arquivo}"
    s3_client.put_object(
        Bucket=BUCKET_NAME, Key=chave_s3, Body=json.dumps(dados)
    )
    print(f"Enviado para S3: s3://{BUCKET_NAME}/{chave_s3}")

    texto = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # antena
    dados_ap = capturar_metricas_antena("ap_01")
    salvar_no_s3(dados_ap, f"{texto}_ap01.json")

    # firewall
    dados_fw = capturar_metricas_firewall()
    salvar_no_s3(dados_fw, f"{texto}_firewall.json")
