import qrcode
import uuid
import os

def makeCode(gen_id:str, n: int, format: str, path) -> str:
    app_url = "http://localhost"
    product = f"product{n:06}"
    code = f"{app_url}/{gen_id}/{product}"
    qr = qrcode.make(code)
    path = f"qrcodes/data/{gen_id}"
    filepath = f"{path}/{product}.{format}"
    qr.save(filepath)
    return filepath
    
def makeZip(qrCodes: str) -> str:
    return ""

def generate(count: int, format: str, logo: str) -> str:
    gen_id = str(uuid.uuid4())
    path = f"qrcodes/data/{gen_id}"
    os.mkdir(path)
    
    for n in range(count):
        makeCode(gen_id, n+1, format, path)
        
    zipFilePath = makeZip(path)
    return zipFilePath

if __name__ == "__main__":
    generate(3, "png", "")