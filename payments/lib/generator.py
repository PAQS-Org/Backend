import qrcode
from PIL import Image, ImageDraw, ImageFont
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
    
    # Add the logo in the middle of the QR code if provided
    if logo:
        logo_image = Image.open(logo)
        logo_box = (qr.size[0] // 2 - logo_image.size[0] // 2, qr.size[1] // 2 - logo_image.size[1] // 2)
        qr.paste(logo_image, logo_box)

    # Add "Scan Me" text below the QR code
    qr = qr.convert("RGBA")
    draw = ImageDraw.Draw(qr)
    font = ImageFont.load_default()  # You can use a custom font here
    text = f"This is managed  by PAQS for {comp}"
    
    # Get the bounding box of the text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    text_position = ((qr.size[0] - text_width) // 2, qr.size[1] - text_height - 10)  # Position it just above the bottom
    draw.text(text_position, text, font=font, fill=(0, 0, 0))

    # Convert back to RGB if saving as JPEG
    if format.lower() == "jpeg" or format.lower() == "jpg":
        qr = qr.convert("RGB")

    # Save the QR code with the specified naming convention
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


