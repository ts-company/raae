from pathlib import Path
from decimal import Decimal

BASE_DIR = Path(__file__).resolve().parent

subscription_price = 9999
service_fee = 500
creator_fee_rate = Decimal("0.1")
license_types = ["MP3 lease", "WAV lease", "Trackout", "Unlimited", "Exclusive"]
allowed_tags = {"dark", "chill", "hype", "moody", "aggressive", "dreamy",
      "nostalgic", "romantic", "gritty", "uplifting", "sad", "energetic"}