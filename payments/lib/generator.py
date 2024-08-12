import qrcode
import uuid
import os
import shutil
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


def makeImage(n: int, format: str, path: str, comp: str, prod: str, logo: str | None = None, ) -> str:
    app_url = "http://localhost"
    gen_id = str(uuid.uuid4())  # Generate a new UUID for each QR code
    company = f"{comp}"
    product = f"{prod}"
    logo = f"{logo}"
    code = f"{app_url}/{gen_id}/{company}/{product}/{logo}"
    qr = qrcode.make(code)
    filepath = f"{path}/{company}_{n}.{format}"
    qr.save(filepath)
    return gen_id, filepath

def makeZip(path: str, gen_id: str) -> str:
    zipPath = shutil.make_archive(base_name=f"qrcodes/data/{gen_id}", format="zip", root_dir=path)
    with open(zipPath, 'rb') as zip_file:
        file_name = f"qrcodes/{gen_id}.zip"
        content = ContentFile(zip_file.read())
        s3_file_path = default_storage.save(file_name, content)
    
    os.remove(zipPath)
    print("creating the zip")
    return default_storage.url(s3_file_path)
    # return zipPath

def generate(count: int, format: str, comp: str, batch: str, prod: str, logo: str | None = None, ) -> str:
    if not os.path.exists("qrcodes/data"):
        os.mkdir("qrcodes/data")
    
    gen_id = str(uuid.uuid4()) 
    path = f"qrcodes/data/{comp}/{batch}/{gen_id}"
    
    os.mkdir(path)
    qr_code_data = []
    for n in range(count):
        qr_code_gen_id, filepath= makeImage(n+1, format, path, comp, prod, logo)
        qr_code_data.append((qr_code_gen_id, filepath))

    zipFilePath = makeZip(path, gen_id)
    print("zipPath", zipFilePath)
    return zipFilePath, qr_code_data

# if __name__ == "__main__":
#     result = generate(3, "jpg", "scala", "papa")
#     print(result)
