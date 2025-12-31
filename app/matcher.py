import os
import csv
import re

from sentence_transformers import SentenceTransformer
import faiss


PROCEDURES_CSV = os.environ.get("PROCEDURES_CSV", "/app/data/procedimentos.csv")
THRESHOLD = float(os.environ.get("MATCHER_THRESHOLD", 0.88))

CODE_REGEX = re.compile(r"\b\d{6,10}\b")


class ProcedureMatcher:

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.debug_trace = []

        self._index_by_code = {}
        self._descs = []

        self._load_csv()

        self.model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

        self.index, self.emb_matrix = self._build_index()

    # ======================================================
    # CSV robusto — encoding + delimitador detectado
    # ======================================================
    def _load_csv(self):
        encodings = ["utf-8-sig", "utf-8", "latin-1"]
        last_err = None

        for enc in encodings:
            try:
                with open(self.csv_path, encoding=enc, newline="") as f:
                    sample = f.read(2048)
                    f.seek(0)

                    delimiter = ";" if sample.count(";") > sample.count(",") else ","

                    reader = csv.DictReader(f, delimiter=delimiter)

                    for row in reader:
                        code = row["CODIGO"].strip()
                        desc = row["DESCRICAO"].strip()

                        self._index_by_code[code] = desc
                        self._descs.append((code, desc))

                return

            except Exception as e:
                last_err = e

        raise RuntimeError(
            f"Falha ao abrir CSV {self.csv_path}. Último erro: {last_err}"
        )

    # ======================================================
    def _build_index(self):
        descriptions = [d[1] for d in self._descs]

        emb = self.model.encode(
            descriptions,
            convert_to_numpy=True
        ).astype("float32")

        index = faiss.IndexFlatIP(emb.shape[1])
        faiss.normalize_L2(emb)
        index.add(emb)

        return index, emb

    # ======================================================
    def match_codes_from_text(self, text: str):
        self.debug_trace = []
        found_codes = set()

        # --------------------------------------------------
        # 1) Códigos numéricos diretos
        # --------------------------------------------------
        numeric = CODE_REGEX.findall(text)

        if numeric:
            self.debug_trace.append({
                "stage": "regex",
                "found": numeric,
                "explanation": "Códigos numéricos encontrados diretamente no texto"
            })

            for c in numeric:
                if c in self._index_by_code:
                    found_codes.add(c)

        # --------------------------------------------------
        # 2) Normalização de linhas — corrige quebras do OCR
        # --------------------------------------------------
        raw_lines = [l.strip() for l in text.splitlines() if l.strip()]
        lines = []

        CONTINUATION_WORDS = {
            "quantitativo",
            "qualitativo",
            "total",
            "livre",
            "digital",
            "ultra-sensivel",
            "alta sensibilidade",
            "basal",
            "seriado",
        }

        for line in raw_lines:
            lower = line.lower()

            if (
                lines
                and (
                    line.startswith(("(", "-", "–"))
                    or line[0].islower()
                    or any(lower.startswith(w) for w in CONTINUATION_WORDS)
                )
            ):
                lines[-1] = f"{lines[-1]} {line}".strip()
            else:
                lines.append(line)

        self.debug_trace.append({
            "stage": "line_normalization",
            "result": lines,
            "explanation": "Linhas unidas quando OCR quebrou indevidamente"
        })

        # helper
        def has_letters(s: str):
            return any(ch.isalpha() for ch in s)

        # stopwords genéricas (não devem disparar contains). Palavras para ignorar
        STOPWORDS = {
            "outros",
            "diversos",
            "exames",
            "resultado",
            "resultados",
            "observacoes",
            "observação",
            "observações",
        }

        # siglas válidas que podem ser palavra única
        KNOWN_SINGLE_EXAMS = {"psa", "pcr", "tsh", "t4", "t3", "vitd"}

        # --------------------------------------------------
        # 3) Embeddings linha a linha
        # --------------------------------------------------
        for line in lines:

            if CODE_REGEX.search(line):
                continue

            query_emb = self.model.encode(
                [line],
                convert_to_numpy=True
            ).astype("float32")

            faiss.normalize_L2(query_emb)

            scores, idx = self.index.search(query_emb, 1)
            score = float(scores[0][0])

            code, desc = self._descs[idx[0][0]]

            norm_line = line.lower().strip()
            norm_desc = desc.lower().strip()

            tokens = norm_line.split()
            is_single_word = len(tokens) == 1

            # ----------------------------------------------
            # 🔥 REGRA CONTAINS — RESTRITA
            # ----------------------------------------------
            if (
                norm_line
                and len(norm_line.replace(" ", "")) >= 3
                and has_letters(norm_line)
                and norm_line not in STOPWORDS
                and (
                    not is_single_word or norm_line in KNOWN_SINGLE_EXAMS
                )
                and norm_line in norm_desc
            ):
                self.debug_trace.append({
                    "stage": "rule_contains",
                    "text": line,
                    "candidate": {"code": code, "desc": desc},
                    "score": score,
                    "accepted": True,
                    "explanation": "Aceito porque o termo significativo aparece dentro da descrição"
                })
                found_codes.add(code)
                continue

            # ----------------------------------------------
            # Threshold normal
            # ----------------------------------------------
            accepted = score >= THRESHOLD

            self.debug_trace.append({
                "stage": "embeddings",
                "text": line,
                "candidate": {"code": code, "desc": desc},
                "score": score,
                "accepted": accepted,
                "explanation": (
                    "Aceito por similaridade"
                    if accepted else
                    "Rejeitado — similaridade insuficiente"
                )
            })

            if accepted:
                found_codes.add(code)

        return sorted(found_codes)


# =========================================================
# Singleton
# =========================================================
_matcher_instance = None


def get_matcher():
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = ProcedureMatcher(PROCEDURES_CSV)
    return _matcher_instance
