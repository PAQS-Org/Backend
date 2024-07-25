import qrcode
from qrcode.image.pure import PyPNGImage
import qrcode.image.svg
import uuid
import os

def makeCode(gen_id:str, n: int, format: str) -> str:
    app_url = "http://localhost"
    product = f"product{n:06}"
    code = f"{app_url}/{gen_id}/{product}"
    qr = qrcode.make(code)
    filepath = f"qrcodes/data/{product}.{format}"
    qr.save(filepath)
    return filepath
    
def makeZip(qrCodes: list[str]) -> str:
    return ""

def generate(count: int, format: str, logo: str) -> str:
    gen_id = str(uuid.uuid4())
    qrCodes = []
    for n in range(count):
        qrCodes.append(makeCode(gen_id, n+1, format))
    zipFilePath = makeZip(qrCodes)
    return zipFilePath

if __name__ == "__main__":
    generate(3, "png", "")