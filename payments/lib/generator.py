import qrcode
from PIL import Image, ImageDraw, ImageFont
import uuid
import os
import shutil
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import gc


def makeImage(n: int, format: str, path: str, comp: str, prod: str, batch: str, logo: str | None = None) -> str:
    app_url = "http://localhost"
    gen_id = str(uuid.uuid4())  # Generate a new UUID for each QR code
    company = f"{comp}"
    product = f"{prod}"
    batch_number = f"{batch}"
    code = f"{app_url}/{gen_id}/{company}/{product}/{batch_number}"
    qr = qrcode.make(code)

    qr = qr.convert("RGBA")  # Ensure QR code is in RGBA mode

    # Add the logo in the middle of the QR code if provided
    if logo:
        logo_image = Image.open(logo).convert("RGBA")  # Ensure the logo is in RGBA mode
        logo_image = logo_image.resize((qr.size[0] // 4, qr.size[1] // 4))  # Resize logo as needed

        # Calculate the position where the logo will be placed
        logo_box = (qr.size[0] // 2 - logo_image.size[0] // 2, 
                    qr.size[1] // 2 - logo_image.size[1] // 2)
        
        # Paste the logo onto the QR code, using the logo's alpha channel to maintain transparency
        qr.paste(logo_image, logo_box, mask=logo_image)

    draw = ImageDraw.Draw(qr)
    font = ImageFont.load_default()  # You can use a custom font here
    text = f"This is managed by PAQS for {comp}. \nTo scan, go to \n\033[1myhttps://www.paqs.com\033[0m"

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    text_position = ((qr.size[0] - text_width) // 2, qr.size[1] - text_height - 10)  # Position it just above the bottom
    draw.text(text_position, text, font=font, fill=(0, 0, 0))

    if format.lower() in ["jpeg", "jpg"]:
        qr = qr.convert("RGB")  # Convert to RGB if the final format is JPEG

    filepath = f"{path}/{company}_{product}_{batch_number}_{n}.{format}"  # Updated filepath format
    os.makedirs(os.path.dirname(filepath), exist_ok=True)  # Create directories if they don't exist
    qr.save(filepath)
    
    # Explicitly delete the objects to free memory
    del draw, qr
    if logo:
        del logo_image
    gc.collect()  # Run garbage collection

    return gen_id, filepath


def makeZip(path: str, comp: str, prod: str, batch: str, gen_id: str) -> str:
    zip_filename = f"{comp}/{prod}/{batch}_{gen_id}.zip"  # Updated zip file name format
    zipPath = shutil.make_archive(base_name=f"qrcodes/data/{gen_id}", format="zip", root_dir=path)
    with open(zipPath, 'rb') as zip_file:
        file_name = f"qrcodes/{zip_filename}"
        content = ContentFile(zip_file.read())
        s3_file_path = default_storage.save(file_name, content)

    os.remove(zipPath)
    print("creating the zip")
    return default_storage.url(s3_file_path)


def generate(count: int, format: str, comp: str, prod: str, batch: str, logo: str | None = None, batch_size: int = 100) -> str:
    if not os.path.exists("qrcodes/data"):
        os.mkdir("qrcodes/data")

    gen_id = str(uuid.uuid4()) 
    path = f"qrcodes/data/{gen_id}"
    os.mkdir(path)
    
    qr_code_data = []
    num_batches = (count + batch_size - 1) // batch_size  # Calculate the number of batches

    for batch_num in range(num_batches):
        start = batch_num * batch_size + 1
        end = min(start + batch_size - 1, count)
        for n in range(start, end + 1):
            qr_code_gen_id, filepath = makeImage(n, format, path, comp, prod, batch, logo)
            qr_code_data.append((qr_code_gen_id, filepath))

        # Optionally remove processed images from disk after each batch to save disk space
        if batch_num != num_batches - 1:  # Keep the last batch files for zipping
            for _, filepath in qr_code_data[-batch_size:]:
                os.remove(filepath)

    zipFilePath = makeZip(path, comp, prod, batch, gen_id)
    print("zipPath", zipFilePath)

    # Cleanup all generated files after zipping
    shutil.rmtree(path)
    
    return zipFilePath, qr_code_data
