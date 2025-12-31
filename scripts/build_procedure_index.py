import csv
import os
import pickle
import io
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

CSV_PATH = os.environ.get("PROCEDURES_CSV", "/app/data/procedimentos.csv")
OUT_DIR = "/app/data/vector_index"
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

os.makedirs(OUT_DIR, exist_ok=True)

print("Loading model:", MODEL_NAME)
model = SentenceTransformer(MODEL_NAME)

procedures = []

print("Reading CSV:", CSV_PATH)

# -------------------------------------------------
# Leitura robusta de CSV (binário + decode seguro)
# -------------------------------------------------
with open(CSV_PATH, "rb") as f:
    raw = f.read()

# tenta decodificar
for enc in ("utf-8", "latin-1", "cp1252"):
    try:
        text = raw.decode(enc)
        print(f"CSV decoded using: {enc}")
        break
    except UnicodeDecodeError:
        continue
else:
    # fallback extremo (nunca quebra)
    text = raw.decode("latin-1", errors="replace")
    print("CSV decoded using latin-1 with replacement")

# cria file-like object
fh = io.StringIO(text)

reader = csv.DictReader(fh, delimiter=";")

for row in reader:
    code = (
        row.get("codigo")
        or row.get("CODIGO")
        or row.get("code")
        or row.get("cod")
    )
    desc = (
        row.get("descricao")
        or row.get("DESCRICAO")
        or row.get("description")
        or ""
    )

    if code and desc:
        procedures.append({
            "code": str(code).strip(),
            "desc": desc.strip()
        })

if not procedures:
    raise RuntimeError("Nenhum procedimento carregado do CSV")

texts = [p["desc"] for p in procedures]

print(f"Generating embeddings for {len(texts)} procedures...")
embeddings = model.encode(
    texts,
    convert_to_numpy=True,
    show_progress_bar=True,
    normalize_embeddings=True
).astype("float32")

dim = embeddings.shape[1]

print("Building FAISS index...")
index = faiss.IndexHNSWFlat(dim, 32)
index.hnsw.efConstruction = 200
index.add(embeddings)

print("Saving index...")
faiss.write_index(index, f"{OUT_DIR}/procedures.index")

with open(f"{OUT_DIR}/procedures_meta.pkl", "wb") as f:
    pickle.dump(procedures, f)

print("DONE. Index criado com sucesso.")
