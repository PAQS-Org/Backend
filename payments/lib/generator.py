import qrcode
import uuid
import os
import shutil
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def makeImage(n: int, format: str, path: str, comp: str, prod: str, batch: str, logo: str | None = None) -> str:
    app_url = "http://localhost"
    gen_id = str(uuid.uuid4())  # Generate a new UUID for each QR code
    company = f"{comp}"
    product = f"{prod}"
    batch_number = f"{batch}"
    code = f"{app_url}/{gen_id}/{company}/{product}"
    qr = qrcode.make(code)
    filepath = f"{path}/{company}_{product}_{batch_number}_{n}.{format}"  # Updated filepath format
    os.makedirs(os.path.dirname(filepath), exist_ok=True)  # Create directories if they don't exist
    qr.save(filepath)
    return gen_id, filepath


def makeZip(path: str, comp: str, prod: str, batch: str, gen_id: str) -> str:
    zip_filename = f"{comp}_{prod}_{batch}_{gen_id}.zip"  # Updated zip file name format
    zipPath = shutil.make_archive(base_name=f"qrcodes/data/{gen_id}", format="zip", root_dir=path)
    with open(zipPath, 'rb') as zip_file:
        file_name = f"qrcodes/{zip_filename}"
        content = ContentFile(zip_file.read())
        s3_file_path = default_storage.save(file_name, content)
    
    os.remove(zipPath)
    print("creating the zip")
    return default_storage.url(s3_file_path)

def generate(count: int, format: str, comp: str, prod: str, batch: str, logo: str | None = None) -> str:
    if not os.path.exists("qrcodes/data"):
        os.mkdir("qrcodes/data")
    
    gen_id = str(uuid.uuid4()) 
    path = f"qrcodes/data/{gen_id}"
    
    os.mkdir(path)
    qr_code_data = []
    for n in range(count):
        qr_code_gen_id, filepath = makeImage(n+1, format, path, comp, prod, batch, logo)
        qr_code_data.append((qr_code_gen_id, filepath))

    zipFilePath = makeZip(path, comp, prod, batch, gen_id)
    print("zipPath", zipFilePath)
    return zipFilePath, qr_code_data


