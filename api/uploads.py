"""Validering av uppladdade filer: storleksgränser och tillåtna filtyper."""
import base64
import binascii
import os
import tempfile

from fastapi import HTTPException, UploadFile

MB = 1024 * 1024
MAX_MESH_BYTES = int(os.environ.get("MAX_MESH_UPLOAD_MB", "500")) * MB
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_UPLOAD_MB", "20")) * MB
MESH_EXTENSIONS = {"stl", "obj", "ply"}
CHUNK = 1 * MB


def save_mesh_upload(file: UploadFile) -> str:
    """Sparar en STL/OBJ-uppladdning till en temporär fil och returnerar sökvägen.
    Anroparen ansvarar för att ta bort filen."""
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in MESH_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Endast .stl-, .obj- och .ply-filer stöds.")

    written = 0
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp_path = tmp.name
        try:
            while chunk := file.file.read(CHUNK):
                written += len(chunk)
                if written > MAX_MESH_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"3D-filen är för stor (max {MAX_MESH_BYTES // MB} MB).",
                    )
                tmp.write(chunk)
        except BaseException:
            tmp.close()
            os.unlink(tmp_path)
            raise
    return tmp_path


def read_image_upload(file: UploadFile) -> bytes:
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Filen måste vara en bild.")
    data = file.file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail=f"Bilden är för stor (max {MAX_IMAGE_BYTES // MB} MB).")
    return data


def decode_base64_image(data: str) -> bytes:
    """Avkodar base64 (med eller utan data:-prefix) med storleksgräns."""
    if "," in data:
        data = data.split(",", 1)[1]
    # base64 är ~4/3 av binärstorleken
    if len(data) > MAX_IMAGE_BYTES * 4 // 3 + 4:
        raise HTTPException(status_code=413, detail=f"Bilden är för stor (max {MAX_IMAGE_BYTES // MB} MB).")
    try:
        return base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Ogiltig bilddata (base64).")
