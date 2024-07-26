import qrcode
import uuid
import os
import shutil

def makeCode(gen_id:str, n: int, format: str, path) -> str:
    app_url = "http://localhost"
    product = f"product{n:06}"
    code = f"{app_url}/{gen_id}/{product}"
    qr = qrcode.make(code)
    path = f"qrcodes/data/{gen_id}"
    filepath = f"{path}/{product}.{format}"
    qr.save(filepath)
    return filepath
    
def makeZip(path: str, gen_id:str) -> str:
    zipPath = shutil.make_archive(base_name=path, format="zip", root_dir=path)
    return zipPath

def generate(count: int, format: str, logo: str) -> str:
    gen_id = str(uuid.uuid4())
    print(gen_id)
    path = f"qrcodes/data/{gen_id}"
    os.mkdir(path)
    
    for n in range(count):
        makeCode(gen_id, n+1, format, path)
        
    zipFilePath = makeZip(path, gen_id)
    return zipFilePath

if __name__ == "__main__":
    generate(3, "png", "")