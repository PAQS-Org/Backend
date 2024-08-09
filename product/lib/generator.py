import qrcode
import uuid
import os
import shutil

def makeImage(n: int, format: str, path: str, comp: str, prod: str, logo: str | None = None, ) -> str:
    app_url = "http://localhost"
    gen_id = str(uuid.uuid4())  # Generate a new UUID for each QR code
    company = f"{comp}"
    product = f"{prod}"
    code = f"{app_url}/{gen_id}/{company}/{product}"
    qr = qrcode.make(code)
    filepath = f"{path}/{product}.{format}"
    qr.save(filepath)
    return filepath

def makeZip(path: str, gen_id: str) -> str:
    zipPath = shutil.make_archive(base_name=f"qrcodes/data/{gen_id}", format="zip", root_dir=path)
    return zipPath

def generate(count: int, format: str, comp: str, prod: str, logo: str | None = None, ) -> str:
    if not os.path.exists("qrcodes/data"):
        os.mkdir("qrcodes/data")
    
    gen_id = str(uuid.uuid4()) 
    path = f"qrcodes/data/{gen_id}"
    
    os.mkdir(path)
    
    for n in range(count):
        makeImage(n+1, format, path, comp, prod, logo)
        
    zipFilePath = makeZip(path, gen_id)
    return zipFilePath

# if __name__ == "__main__":
#     result = generate(3, "jpg", "")
#     print(result)
