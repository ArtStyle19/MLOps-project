import os
from decouple import config

class Settings:
    """Application settings"""
    ENVIRONMENT = config('ENVIRONMENT', default='production')
    MODEL_PATH = config('MODEL_PATH', default='weights/epoch20.pt')
    DEFAULT_CAMERA_INDEX = config('DEFAULT_CAMERA_INDEX', default=0, cast=int)
    CONFIDENCE_THRESHOLD = config('CONFIDENCE_THRESHOLD', default=0.5, cast=float)

settings = Settings()