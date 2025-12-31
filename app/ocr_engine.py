import easyocr
import numpy as np
import pypdfium2 as pdfium
import io
# compatibilidade Pillow >=10 (ANTIALIAS foi movido/removido)
from PIL import Image
if not hasattr(Image, "ANTIALIAS"):
    # Pillow >= 9.1 tem Image.LANCZOS e a nova API Image.Resampling
    try:
        Image.ANTIALIAS = Image.Resampling.LANCZOS
    except Exception:
        # fallback para versões antigas que ainda têm LANCZOS
        Image.ANTIALIAS = getattr(Image, "LANCZOS", 1)

reader = easyocr.Reader(["pt", "en"], gpu=False)


def render_page_to_pil(page, dpi=200):
    scale = dpi / 72
    try:
        return page.render(scale=scale).to_pil()
    except:
        return page.render_topil(scale=scale)


def pdf_to_images(pdf_bytes, dpi=200):
    pdf = pdfium.PdfDocument(pdf_bytes)
    images = []

    for i in range(len(pdf)):
        page = pdf.get_page(i)
        pil_img = render_page_to_pil(page, dpi=dpi).convert("RGB")
        images.append(pil_img)
        page.close()

    pdf.close()
    return images


def pil_to_numpy(img: Image.Image):
    return np.array(img).astype(np.uint8)


def ocr_image_bytes(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    arr = pil_to_numpy(img)
    text = reader.readtext(arr, detail=0)
    return "\n".join(text)


def ocr_pdf_bytes(pdf_bytes):
    images = pdf_to_images(pdf_bytes)
    texts = []
    for img in images:
        arr = pil_to_numpy(img)
        result = reader.readtext(arr, detail=0)
        texts.append("\n".join(result))
    return "\n\n=== Page Break ===\n\n".join(texts)


def ocr_auto(filename=None, file_bytes=None, file_path=None):
    """
    Pode receber:
      - filename + file_bytes     (upload direto)
      - file_path                 (arquivo salvo no disco)
    """

    # Se veio caminho no disco → abrimos e lemos bytes
    if file_path is not None and file_bytes is None:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # se filename não foi passado, inferimos
        if filename is None:
            filename = file_path.split("/")[-1]

    if filename is None or file_bytes is None:
        raise ValueError("É necessário informar filename+file_bytes OU file_path")

    ext = filename.lower().split(".")[-1]

    if ext == "pdf":
        return ocr_pdf_bytes(file_bytes)

    elif ext in ["png", "jpg", "jpeg", "bmp", "tiff"]:
        return ocr_image_bytes(file_bytes)

    else:
        raise ValueError(f"Formato não suportado: {ext}")

