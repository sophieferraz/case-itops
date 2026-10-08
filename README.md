# ITOps: Data Lake de monitoramento de rede na AWS

Projeto da disciplina de Sistemas Operacionais (SPTech). Simula a coleta de métricas de **antenas (access points)** e de um **firewall**, guarda os dados em um **Data Lake no Amazon S3** (camadas Bronze, Silver e Gold) e gera relatórios que respondem perguntas de negócio de ITOps.

## Como funciona

```
Máquina local                      AWS
┌────────────────────┐      ┌─────────────────────────────────────────┐
│ local2bronze_aps   │─────▶│  S3: 01-bronze  (JSONs brutos)          │
│ local2bronze_fw    │─────▶│        │                                │
└────────────────────┘      │        ▼   EC2: bronze2silver.py        │
                            │  S3: 02-silver  (CSV tratado)           │
                            │        │                                │
                            │        ▼   EC2: silver2gold.py │
                            │  S3: 03-gold    (relatórios em CSV)     │
                            └─────────────────────────────────────────┘
```

## Estrutura do bucket

```
s3-itops-sophie/
├── 01-bronze/   dados brutos, exatamente como foram coletados (JSON)
├── 02-silver/   dados limpos, tipados e com colunas calculadas (CSV)
└── 03-gold/     relatórios prontos para análise (CSV)
```

## Scripts

### Camada 01: Bronze (rodam na máquina local)

| Script | O que faz |
|---|---|
| `local2bronze_aps.py` | Simula 3 antenas (`ap_01`, `ap_02`, `ap_03`). Coleta bytes enviados/recebidos com `psutil` (multiplicados por um peso de cada antena), sorteia conexões ativas e registra CPU e RAM. |
| `local2bronze_firewall.py` | Simula o firewall: sessões ativas, pacotes descartados, IP bloqueado, CPU, RAM e bytes enviados/recebidos. |

Os dois rodam em loop e enviam **1 arquivo JSON por dispositivo a cada 1 minuto**, com nomes como `2026-04-06_10-30_ap01.json`. Se um envio falha, o script mostra o erro e continua.

### Camada 02: Silver (roda na EC2)

| Script | O que faz |
|---|---|
| `bronze2silver.py` | Lê todos os JSONs da Bronze e junta numa única tabela (pandas). Formata o timestamp, calcula a **vazão em Mbps** (diferença de bytes entre medições de cada dispositivo) e cria a coluna **`status_carga`**. Salva o CSV em `02-silver/`. |

Regras do `status_carga`:

| Condição | Status |
|---|---|
| `active_conn` > 40 | alta densidade |
| `cpu_usage` > 80% | gargalo de processamento |
| `ram_usage` > 75% | OOM (Out Of Memory) |
| nenhuma das anteriores | normal |

### Camada 03: Gold (roda na EC2)

| Script | O que faz |
|---|---|
| `silver2gold.py` | Lê o CSV da Silver e gera 4 relatórios em `03-gold/`. |

| Relatório | Pergunta que responde |
|---|---|
| `relatorio_zonas_mortas.csv` | Quais antenas têm menos tráfego e podem ser subutilizadas? |
| `relatorio_pacotes_bloqueados.csv` | Quantos pacotes o firewall bloqueou por hora? Houve pico de ataque? |
| `relatorio_mapa_de_calor.csv` | Qual antena (setor do prédio) consome mais internet? |
| `relatorio_gargalo_saida.csv` | Quando a CPU do firewall está alta, as sessões ativas também estão? O hardware está saturado? |

## Como executar

### 1. Coleta (máquina local)

```bash
pip install boto3 psutil
aws configure                       
aws configure set aws_session_token <seu_token>

python local2bronze_aps.py          # em um terminal
python local2bronze_firewall.py     # em outro terminal
```

### 2. Tratamento (instância EC2)

A EC2 precisa ter a função IAM **LabInstanceProfile** associada, para acessar o S3 sem credenciais no código.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv -y
python3 -m venv venv
source venv/bin/activate
pip install pandas boto3

python3 bronze2silver.py
python3 silver2gold_completo.py
```

### 3. Automação (opcional, com cron)

Em `crontab -e`, para rodar a cada hora:

```
0 * * * * /home/ubuntu/venv/bin/python /home/ubuntu/bronze2silver.py
5 * * * * /home/ubuntu/venv/bin/python /home/ubuntu/silver2gold_completo.py
```

## Tecnologias

- Python (pandas, boto3, psutil)
- Amazon S3 (Data Lake)
- Amazon EC2 (processamento)
- AWS IAM (permissões da instância)
- cron (agendamento)

## Observações

- Os dados são **simulados**. O `psutil` mede a máquina real onde o script roda, e as demais métricas (conexões, sessões, pacotes) são sorteadas com `random`. Por isso, algumas correlações e previsões não refletem uma rede de verdade.
- As credenciais do AWS Academy (Learner Lab) expiram a cada sessão. 

## Autora

Sophie Ferraz, 1º ano de Ciência da Computação, SPTech.
