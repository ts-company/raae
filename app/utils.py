from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import cloudinary
import cloudinary.uploader
import os

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_BEAT_MIME_TYPES = {
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/flac",
    "audio/mp4",
}

MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 10_000_000
MAX_BEAT_SIZE = 20 * 1024 * 1024
MIN_BEAT_DURATION = 5
MAX_BEAT_DURATION = 600

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_image(file: UploadFile, folder: str):
    result = cloudinary.uploader.upload(
        file.file,
        folder=folder,
        transformation=[
            {"width": 256, "height": 256, "crop": "fill"},
            {"quality": "auto"}
        ]
    )
    return result["public_id"]

def generate_image_url(public_id):
    url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type="image",
    )
    return url

def delete_file(public_id: str, resource_type: str):
    cloudinary.uploader.destroy(public_id, resource_type=resource_type)

def is_valid_image(upload_file) -> bool:
    try:
        contents = upload_file.file.read()
        if not contents:
            return False
        if len(contents) > MAX_IMAGE_SIZE:
            return False
        if upload_file.content_type not in ALLOWED_IMAGE_TYPES:
            return False
        image = Image.open(BytesIO(contents))
        image.verify()
        image = Image.open(BytesIO(contents))
        width, height = image.size
        if width * height > MAX_IMAGE_PIXELS:
            return False
        if image.format not in {"JPEG", "PNG", "WEBP", "JPG"}:
            return False
        return True

    except (UnidentifiedImageError, OSError, ValueError):
        return False
    finally:
        upload_file.file.seek(0)