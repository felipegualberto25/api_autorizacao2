# debugar retornando uma lista com os valores de threshold
"""
Teste rápido para validar o matcher após as alterações.
Roda no mesmo ambiente/venv/container da aplicação.

Uso:
    python debug_match_and_test.py
"""

import sys
import os
import traceback
from pprint import pprint

TARGET_CODE = "40302750"

# texto extraído (o mesmo que você forneceu)
OCR_TEXT = """'diolife
Glicemia Jejum
T3 Total
Lillpograma
T4 Livre
T4 Livre
Ferro Sérico
Pcr (proteina € Reativa)
Quantitativo
Psa
Calcio
Vit D
Dr. Fabricio Parra Garcia
CRM:16744
Dr
Car
Fabricic
"""

print("PYTHON:", sys.executable)
print("CWD:", os.getcwd())
print("PROCEDURES_CSV env:", os.environ.get("PROCEDURES_CSV"))

# importa get_matcher
try:
    from app.matcher import get_matcher
except Exception:
    print("Erro ao importar app.matcher.get_matcher():")
    traceback.print_exc()
    sys.exit(1)

# instancia matcher
try:
    matcher = get_matcher(csv_path="/app/data/procedimentos.csv")
except Exception:
    print("Erro ao instanciar matcher via get_matcher():")
    traceback.print_exc()
    sys.exit(1)

print("\n--- Matcher basic summary ---")
idx = getattr(matcher, "_index_by_code", None)
descs = getattr(matcher, "_descs", None)
rf_choices = getattr(matcher, "_rf_choices", None)

print("type(_index_by_code):", type(idx).__name__)
print("len(_index_by_code):", len(idx) if idx is not None else "N/A")
print("len(_descs):", len(descs) if descs is not None else "N/A")
print("_rf_choices present?:", bool(rf_choices))

# quick peek at keys where target might appear (show nearby keys to target)
if idx:
    # print a sample of keys around where the numeric region could be
    sample_keys = list(idx.keys())[:200]
    print("\nSample first 120 keys (repr):")
    for k in sample_keys[:120]:
        print(" -", repr(k))

# check whether target code is present in index_by_code
present_direct = TARGET_CODE in (idx or {})
present_strip = any(str(k).strip() == TARGET_CODE for k in (idx or {}))
present_clean = any(str(k).replace("\ufeff","").replace("\u00A0","").strip() == TARGET_CODE for k in (idx or {}))

print("\nTARGET_CODE presence checks:")
print(" - direct in keys:", present_direct)
print(" - any str(k).strip() == TARGET_CODE:", present_strip)
print(" - any cleaned key == TARGET_CODE:", present_clean)

if present_direct or present_strip or present_clean:
    found_key = None
    for k in (idx or {}):
        if str(k).strip() == TARGET_CODE or str(k).replace("\ufeff","").replace("\u00A0","").strip() == TARGET_CODE:
            found_key = k
            break
    print("\nFound key repr:", repr(found_key))
    print("Associated entry (raw):")
    pprint(idx.get(found_key))

# Run the matcher on your OCR_TEXT
print("\n--- Running matcher.match_codes_from_text on OCR_TEXT ---")
try:
    codes = matcher.match_codes_from_text(OCR_TEXT)
    print("matcher returned codes:", codes)
except Exception:
    print("matcher.match_codes_from_text raised an exception:")
    traceback.print_exc()

# If rapidfuzz available, show top rapidfuzz matches for each OCR line
try:
    from rapidfuzz import fuzz, process
    RF = True
except Exception:
    RF = False

if RF and rf_choices:
    print("\n--- rapidfuzz top matches per OCR line ---")
    lines = [ln.strip() for ln in OCR_TEXT.splitlines() if ln.strip()]
    for ln in lines:
        try:
            res = process.extract(ln, rf_choices, scorer=fuzz.partial_ratio, limit=8)
        except Exception as e:
            print(" rapidfuzz.extract failed for line:", repr(ln)[:120], "error:", e)
            res = []
        if not res:
            continue
        print("\nLine:", repr(ln)[:200])
        for text_match, score, key in res:
            print(f" score={score:5.1f} key={repr(key)} match_text={repr(text_match)[:120]}")
        if any(str(key).strip() == TARGET_CODE for _, _, key in res):
            print(" -> TARGET_CODE appeared in the top matches for this line.")
else:
    print("\nrapidfuzz not available or rf_choices empty; skipping rapidfuzz diagnostics.")

print("\n--- End of test ---")
