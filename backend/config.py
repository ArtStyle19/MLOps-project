import os
from decouple import config

class Settings:
    """Application settings"""
    ENVIRONMENT = config('ENVIRONMENT', default='production')
    MODEL_PATH = config('MODEL_PATH', default='weights/epoch20.pt')
    DEFAULT_CAMERA_INDEX = config('DEFAULT_CAMERA_INDEX', default=0, cast=int)
    CONFIDENCE_THRESHOLD = config('CONFIDENCE_THRESHOLD', default=0.5, cast=float)
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_MODEL_KEY = os.getenv("S3_MODEL_KEY", "weights/best.pt")
    LOCAL_MODEL_PATH = os.getenv("LOCAL_MODEL_PATH", "weights/epoch20.pt")
    CUDA_VISIBLE_DEVICES = '-1'
settings = Settings()