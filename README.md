# API — OCR & Procedimentos Médicos

## Visão Geral
Esta API processa PDFs e imagens contendo pedidos/exames médicos, extrai texto via OCR e identifica automaticamente os procedimentos existentes com base na tabela **procedimentos.csv**.

O fluxo é assíncrono: você envia o arquivo, recebe um `job_id` e consulta o resultado depois.

---

## 📌 Principais Funcionalidades
- Upload de arquivos (PDF / imagens)
- Processamento assíncrono com Celery
- OCR automático (PDF ou imagem)
- Identificação de procedimentos através de:
  - códigos numéricos
  - similaridade semântica (embeddings)
  - heurísticas inteligentes para textos quebrados
- Logs explicando como cada decisão foi tomada

---

## 🔎 Como funciona o Matching

### 1️⃣ OCR
- Conversão de PDF para imagem quando necessário
- Extração com **EasyOCR**
- Normalização básica

### 2️⃣ Detecção de códigos numéricos
Expressões numéricas como:

```
40302040
40316491
```

são mapeadas diretamente ao CSV.

### 3️⃣ Reconstrução de linhas quebradas
Exemplo:
```
Pcr
(proteina reativa) Quantitativo
```
vira:
```
Pcr (proteina reativa) Quantitativo
```

### 4️⃣ Embeddings (IA)
Utiliza:

```
sentence-transformers / all-mpnet-base-v2
```

para comparar frases com descrições da tabela.

### 5️⃣ Regras extras (para evitar erros)
- regra contains restrita
- rejeição de palavras genéricas
- aceitação controlada de siglas médicas

---

## 🧾 Logs de Decisão
Para cada job é registrado:
- texto OCR
- códigos detectados
- lista com decisões (`debug_trace`)
- explicação de cada etapa

Útil para auditoria e depuração.

---

## ⚙️ Requisitos Técnicos

### Linguagem / Framework
- Python 3.10
- FastAPI
- Celery
- Redis

### IA / NLP
- EasyOCR
- Sentence Transformers (all-mpnet-base-v2)
- Faiss

### Dados
Arquivo obrigatório:

```
/app/data/procedimentos.csv
```

com colunas:
```
CODIGO;DESCRICAO
```

---

## 🌍 Variáveis de Ambiente
```
PROCEDURES_CSV=/app/data/procedimentos.csv
DATA_DIR=/app/data
UPLOAD_DIR=/app/data/uploads
CELERY_BROKER_URL=redis://ocr_redis:6379/0
CELERY_RESULT_BACKEND=redis://ocr_redis:6379/1
MATCHER_THRESHOLD=0.88
```

---

## 🚀 Fluxo Básico

### 1️⃣ Enviar arquivo
`POST /ocr` → retorna job_id

### 2️⃣ Consultar resultado
`GET /ocr/{job_id}`

Retorno inclui:
- status
- texto OCR
- códigos encontrados
- caminho do log

---

## 📝 Próximos Passos Possíveis
- alias médicos configuráveis
- modelos de reranking
- endpoint de consulta de log
- mais heurísticas para laudos diferentes
