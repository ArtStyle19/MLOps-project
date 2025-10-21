import os
import boto3
import torch
import logging
from botocore.exceptions import NoCredentialsError, ClientError
from ultralytics import YOLO

logger = logging.getLogger(__name__)

def download_model_from_s3():
    """Descarga el modelo desde S3 si no está en el servidor"""
    local_path = "weights/epoch20.pt"   # Dónde se guardará localmente
    bucket_name = "mlops-bucket-vicari"
    s3_key = "epoch20.pt"                 

    if os.path.exists(local_path):
        logger.info(f"Modelo ya existe en {local_path}")
        return local_path

    logger.info(f"⬇Descargando modelo desde S3: {bucket_name}/{s3_key}")

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id="AKIA53Y7UDPZVDWB4TFZ",
            aws_secret_access_key="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",
            region_name="us-east-1",
        )

        # Crear carpeta si no existe
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Descargar modelo directamente al archivo local
        s3.download_file(bucket_name, s3_key, local_path)

        logger.info("Modelo descargado correctamente desde S3.")
        return local_path

    except NoCredentialsError:
        logger.error("Credenciales AWS no configuradas correctamente.")
        raise
    except ClientError as e:
        logger.error(f"Error descargando modelo: {e}")
        raise


def load_yolo_model(weights_path: str):
    try:
        device = torch.device('cpu')
        logger.info("🚀 Cargando modelo YOLO...")
        # Intenta cargar normalmente
        model = YOLO(weights_path)
        model.to(device)
        logger.info("Model loaded directly to CPU")

        
        logger.info("Modelo YOLO cargado correctamente")
        return model

    except Exception as e:
        logger.error(f"Error al cargar el modelo YOLO: {e}")
        # Intento alternativo si falla
        try:
            logger.warning("Reintentando con weights_only=False...")
            state_dict = torch.load(weights_path, map_location="cpu", weights_only=False)
            model = YOLO()
            model.model.load_state_dict(state_dict)
            logger.info("Modelo cargado con método alternativo")
            return model
        except Exception as e2:
            logger.error(f"Segundo intento fallido: {e2}")
            raise