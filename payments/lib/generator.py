import qrcode
import uuid
import os
import shutil
import redis
from PIL import Image, ImageDraw, ImageFont
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from celery import shared_task
from io import BytesIO

redis_client = redis.StrictRedis(host=os.environ.get("REDIS_URL"), port=6379, db=0)

@shared_task
def makeImage(n: int, format: str, path: str, comp: str, prod: str, batch: str, logo: str | None = None) -> str:
    app_url = "http://localhost"
    gen_id = str(uuid.uuid4())  # Generate a new UUID for each QR code
    code = f"{app_url}/{gen_id}/{comp}/{prod}"
    
    # Cache key for QR code
    cache_key = f"qr_code:{comp}:{prod}:{batch}:{gen_id}:{n}"
    cached_qr = redis_client.get(cache_key)

    if cached_qr:
        filepath = cached_qr.decode("utf-8")
        return gen_id, filepath

    qr = qrcode.make(code)
    qr = qr.convert("RGBA")

    if logo:
        logo_image = Image.open(logo).convert("RGBA") 
        logo_image = logo_image.resize((qr.size[0] // 4, qr.size[1] // 4)) 
        logo_box = (qr.size[0] // 2 - logo_image.size[0] // 2, 
                    qr.size[1] // 2 - logo_image.size[1] // 2)
        qr.paste(logo_image, logo_box, mask=logo_image)
    print('logo')
    # Draw additional text
    draw = ImageDraw.Draw(qr)
    font = ImageFont.load_default()  
    text = f"This is managed by PAQS for {comp}"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_position = ((qr.size[0] - text_bbox[2]) // 2, qr.size[1] - text_bbox[3] - 10)
    draw.text(text_position, text, font=font, fill=(0, 0, 0))

    if format.lower() in ["jpeg", "jpg"]:
        qr = qr.convert("RGB")

    buffer = BytesIO()
    qr.save(buffer, format=format.upper())
    buffer.seek(0)

    filepath = f"qrcodes/{comp}_{prod}_{batch}_{n}.{format}"
    default_storage.save(filepath, ContentFile(buffer.read()))

    redis_client.setex(cache_key, 3600, filepath)

    return gen_id, filepath


@shared_task
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

@shared_task
def generate(count: int, format: str, comp: str, prod: str, batch: str, logo: str | None = None) -> str:
    gen_id = str(uuid.uuid4())
    path = f"qrcodes/data/{gen_id}"
    os.makedirs(path, exist_ok=True)

    qr_code_data = []
    tasks = []
    print("generate task")
    for n in range(count):
        task = makeImage(n+1, format, comp, prod, batch, logo)
        tasks.append(task)

    # Collect results as they complete
    for task in tasks:
        qr_code_gen_id, filepath = task.get()
        qr_code_data.append((qr_code_gen_id, filepath))

    zip_file_path = makeZip(path, comp, prod, batch, gen_id).get()

    return zip_file_path, qr_code_data


