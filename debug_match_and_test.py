#teste que retorna os macthes passando theshold
import os
import sys
import traceback
from pprint import pprint

# Importa matcher real
try:
    from app.matcher import get_matcher
except Exception:
    print("ERRO AO IMPORTAR app.matcher:")
    traceback.print_exc()
    sys.exit(1)

# Threshold local para filtro fuzzy
FUZZY_FILTER_THRESHOLD = 90

# Texto OCR de teste (você pode substituir pelo do seu job)
OCR_TEXT = """Data do Pedido:
[Data]
Introdução:
Este formulário é utilizado para solicitar a realização de exames de sangue,
com
objetivo de monitorar a saúde do paciente
diagnosticar possíveis condições médicas.
Exames Recomendados:
Tipagem Sanguínea
2. Pesquisa de Anticorpos
3. Coagulograma
Exames de Hormônios (TSH, T4 livre)
5. Teste de Diabetes (Hemoglobina Glicada)
Justificativa:
Os exames solicitados são necessários para um acompanhamento mais eficaz da saúde e podem ajudar na prevenção de
doenças
Instruções:
Comparecer ao laboratório no horário agendado.
2 Manter jejum conforme instruído e trazer documento de identificação
3. Para mais informacões
paciente pode liaar para [Número do Telefone do Consultóriol.
"""

def header(title):
    print("\n" + "="*80)
    print(title)
    print("="*80 + "\n")

# --------------------------------------------------------------------------------------
header("1) Carregando matcher")

try:
    matcher = get_matcher()
except Exception:
    print("ERRO AO INICIALIZAR MATCHER:")
    traceback.print_exc()
    sys.exit(1)

print(f"PROCEDURES_CSV env: {os.environ.get('PROCEDURES_CSV')}")
print(f"MATCHER_THRESHOLD env: {os.environ.get('MATCHER_THRESHOLD')}")

print("\n--- Matcher basic summary ---")
print("type(_index_by_code):", type(matcher._index_by_code))
print("len(_index_by_code):", len(matcher._index_by_code))
print("len(_descs):", len(matcher._descs))
print("_rf_choices present?:", bool(matcher._rf_choices))

# Mostrar algumas chaves
print("\nSample first 20 keys (repr):")
for i, k in enumerate(list(matcher._index_by_code.keys())[:20]):
    print(f"- {repr(k)}")
print()

# --------------------------------------------------------------------------------------
header("2) Executando match_codes_from_text()")

try:
    codes = matcher.match_codes_from_text(OCR_TEXT)
    print("MATCHER CODES RETURNED:\n", codes)
except Exception:
    print("ERRO NO matcher.match_codes_from_text:")
    traceback.print_exc()
    sys.exit(2)

# --------------------------------------------------------------------------------------
header("3) Fuzzy debugging (apenas scores >= 93)")

# Apenas se rapidfuzz estiver disponível
try:
    from rapidfuzz import fuzz, process
    _HAS_RF = True
except Exception:
    _HAS_RF = False

if not _HAS_RF:
    print("Rapidfuzz não disponível — ignorando diagnóstico fuzzy.")
else:
    print(f"Filtro: apenas scores >= {FUZZY_FILTER_THRESHOLD}\n")

    # normaliza e gera linhas
    def normalize(s):
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        return " ".join(s.split()).lower()

    norm_text = normalize(OCR_TEXT)
    lines = [ln.strip() for ln in norm_text.split("\n") if ln.strip()]

    # rodar fuzzy por linha
    for ln in lines:
        print(f"\nLine: '{ln}'")

        try:
            results = process.extract(
                ln,
                matcher._rf_choices,
                scorer=fuzz.partial_ratio,
                limit=25
            )
        except Exception as e:
            print(f"  ERRO rapidfuzz.extract: {e}")
            continue

        # Filtrar por score >= 93
        filtered = [(txt, score, key) for txt, score, key in results if score >= FUZZY_FILTER_THRESHOLD]

        if not filtered:
            print("  Nenhum match com score >= 93")
            continue

        for txt, score, key in filtered:
            print(f"score={score:5.1f} | key='{key}' | text='{txt}'")

# --------------------------------------------------------------------------------------
header("4) Teste finalizado")

print("Tudo certo. Se quiser testar outro OCR_TEXT, edite o arquivo.")
