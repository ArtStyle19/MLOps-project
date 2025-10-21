from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import base64
import cv2
import numpy as np
from ultralytics import YOLO
import os
import logging
import time
import io
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

from model_loader import download_model_from_s3, load_yolo_model

app = FastAPI(
    title="Safety Vest Detection API",
    description="Real-time safety vest detection using YOLO",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://settinel.lat",
        "https://www.settinel.lat", 
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Global variables
model = None
detection_stats: Dict[str, Dict] = {
    'global': {'sin_chaleco': 0, 'con_chaleco': 0}
}

# def process_frame_with_detection(frame: np.ndarray) -> dict:
#     """Process frame with YOLO detection and return detection info with annotated image"""
#     try:
#         logger.info(f"Processing frame - Shape: {frame.shape}")
        
#         # Perform detection
#         results = model(frame, verbose=False, conf=0.3)
        
#         detection_info = {
#             "detected": False,
#             "class_name": "Sin detección",
#             "confidence": 0.0,
#             "counts": {"sin_chaleco": 0, "con_chaleco": 0}
#         }
        
#         # Create a copy of the frame to draw on
#         annotated_frame = frame.copy()
        
#         if len(results[0].boxes) > 0:
#             boxes = results[0].boxes
#             class_names = getattr(results[0], 'names', {0: 'sin_chaleco', 1: 'con_chaleco'})
            
#             logger.info(f"Detections found: {len(boxes)}")
            
#             # Count all detections and draw boxes
#             for i, box in enumerate(boxes):
#                 box_confidence = float(box.conf[0])
#                 if box_confidence > 0.3:
#                     box_class_id = int(box.cls[0])
#                     box_class_name = class_names.get(box_class_id, f"Clase {box_class_id}")
                    
#                     # Get box coordinates
#                     x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
#                     # Define colors based on class
#                     if "sin_chaleco" in box_class_name.lower():
#                         color = (0, 0, 255)  # Red for no vest
#                         detection_info["counts"]["sin_chaleco"] += 1
#                     elif "con_chaleco" in box_class_name.lower():
#                         color = (0, 255, 0)  # Green for vest
#                         detection_info["counts"]["con_chaleco"] += 1
#                     else:
#                         color = (255, 255, 0)  # Yellow for other
                    
#                     # Draw bounding box
#                     cv2.rectangle(annotated_frame, 
#                                 (int(x1), int(y1)), 
#                                 (int(x2), int(y2)), 
#                                 color, 3)
                    
#                     # Draw label
#                     label = f"{box_class_name} {box_confidence:.2f}"
#                     label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    
#                     # Label background
#                     cv2.rectangle(annotated_frame,
#                                 (int(x1), int(y1) - label_size[1] - 10),
#                                 (int(x1) + label_size[0], int(y1)),
#                                 color, -1)
                    
#                     # Label text
#                     cv2.putText(annotated_frame, label,
#                             (int(x1), int(y1) - 5),
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
#             # Update detection info if any detections
#             if detection_info["counts"]["sin_chaleco"] > 0 or detection_info["counts"]["con_chaleco"] > 0:
#                 detection_info.update({
#                     "detected": True,
#                     "class_name": f"Detecciones: {detection_info['counts']}",
#                     "confidence": box_confidence
#                 })
            
#             logger.info(f"Detection counts: {detection_info['counts']}")
            
#             # Update global statistics
#             if detection_info["counts"]["sin_chaleco"] > 0:
#                 detection_stats['global']["sin_chaleco"] += detection_info["counts"]["sin_chaleco"]
#             if detection_info["counts"]["con_chaleco"] > 0:
#                 detection_stats['global']["con_chaleco"] += detection_info["counts"]["con_chaleco"]
        
#         # Add frame counter and info text
#         cv2.putText(annotated_frame, f"Detections: {detection_info['counts']}", 
#                 (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
#         cv2.putText(annotated_frame, f"Status: {detection_info['class_name']}", 
#                 (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
#         # Encode the annotated frame
#         _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
#         encoded_image = base64.b64encode(buffer).decode('utf-8')
        
#         detection_info["annotated_frame"] = encoded_image
        
#         return detection_info
        
#     except Exception as e:
#         logger.error(f"Detection error: {e}")
#         # Return original frame in case of error
#         _, buffer = cv2.imencode('.jpg', frame)
#         encoded_image = base64.b64encode(buffer).decode('utf-8')
        
#         return {
#             "detected": False, 
#             "class_name": f"Error: {str(e)}", 
#             "confidence": 0.0, 
#             "counts": {"sin_chaleco": 0, "con_chaleco": 0},
#             "annotated_frame": encoded_image
#         }



def process_frame_with_detection(frame: np.ndarray) -> dict:
    """Process frame with YOLO detection and return detection info with annotated image"""
    try:
        logger.info(f"🔄 Processing frame - Shape: {frame.shape}")
        
        # Verificar que el frame sea válido
        if frame is None or frame.size == 0:
            logger.error("❌ Invalid frame received")
            return create_error_response(frame, "Invalid frame")
        
        # Realizar detección con configuración robusta
        try:
            results = model(frame,device='cpu', verbose=False, conf=0.3, iou=0.5)
            logger.info(f"✅ Detection completed, {len(results[0].boxes) if len(results) > 0 else 0} boxes found")
        except Exception as e:
            logger.error(f"❌ YOLO detection error: {e}")
            return create_error_response(frame, f"Detection error: {str(e)}")
        
        detection_info = {
            "detected": False,
            "class_name": "Sin detección",
            "confidence": 0.0,
            "counts": {"sin_chaleco": 0, "con_chaleco": 0}
        }
        
        # Crear frame anotado
        annotated_frame = frame.copy()
        
        if len(results) > 0 and len(results[0].boxes) > 0:
            boxes = results[0].boxes
            class_names = getattr(results[0], 'names', {0: 'sin_chaleco', 1: 'con_chaleco'})
            
            logger.info(f"🎯 Detections found: {len(boxes)}")
            
            # Contar detecciones y dibujar cajas
            for i, box in enumerate(boxes):
                try:
                    box_confidence = float(box.conf[0])
                    if box_confidence > 0.3:  # Umbral de confianza
                        box_class_id = int(box.cls[0])
                        box_class_name = class_names.get(box_class_id, f"class_{box_class_id}")
                        
                        logger.info(f"📦 Box {i}: {box_class_name} ({box_confidence:.2f})")
                        
                        # Obtener coordenadas
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Definir colores basados en la clase
                        if "sin_chaleco" in box_class_name.lower():
                            color = (0, 0, 255)  # Rojo para sin chaleco
                            detection_info["counts"]["sin_chaleco"] += 1
                        elif "con_chaleco" in box_class_name.lower():
                            color = (0, 255, 0)  # Verde para con chaleco
                            detection_info["counts"]["con_chaleco"] += 1
                        else:
                            color = (255, 255, 0)  # Amarillo para otros
                            continue  # Saltar clases no relevantes
                        
                        # Dibujar bounding box
                        cv2.rectangle(annotated_frame, 
                                    (int(x1), int(y1)), 
                                    (int(x2), int(y2)), 
                                    color, 2)
                        
                        # Dibujar etiqueta
                        label = f"{box_class_name} {box_confidence:.2f}"
                        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                        
                        # Fondo de etiqueta
                        cv2.rectangle(annotated_frame,
                                    (int(x1), int(y1) - label_size[1] - 10),
                                    (int(x1) + label_size[0], int(y1)),
                                    color, -1)
                        
                        # Texto de etiqueta
                        cv2.putText(annotated_frame, label,
                                (int(x1), int(y1) - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        
                except Exception as e:
                    logger.error(f"❌ Error processing box {i}: {e}")
                    continue
            
            # Actualizar información de detección si hay detecciones
            if detection_info["counts"]["sin_chaleco"] > 0 or detection_info["counts"]["con_chaleco"] > 0:
                detection_info.update({
                    "detected": True,
                    "class_name": f"Detecciones: {detection_info['counts']}",
                    "confidence": box_confidence if 'box_confidence' in locals() else 0.0
                })
            create_error_response
            logger.info(f"📊 Detection counts: {detection_info['counts']}")
            
            # Actualizar estadísticas globales
            if detection_info["counts"]["sin_chaleco"] > 0:
                detection_stats['global']["sin_chaleco"] += detection_info["counts"]["sin_chaleco"]
            if detection_info["counts"]["con_chaleco"] > 0:
                detection_stats['global']["con_chaleco"] += detection_info["counts"]["con_chaleco"]
        
        # Agregar información del frame
        cv2.putText(annotated_frame, f"Detections: {detection_info['counts']}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(annotated_frame, f"Status: {detection_info['class_name']}", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Codificar frame anotado
        try:
            _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            encoded_image = base64.b64encode(buffer).decode('utf-8')
            detection_info["annotated_frame"] = encoded_image
            logger.info("✅ Frame encoded successfully")
        except Exception as e:
            logger.error(f"❌ Frame encoding error: {e}")
            detection_info["annotated_frame"] = ""
        
        return detection_info
        
    except Exception as e:
        logger.error(f"❌ Detection processing error: {e}")
        return create_error_response(frame, f"Processing error: {str(e)}")

def create_error_response(frame: np.ndarray, error_msg: str) -> dict:
    """Create error response with original frame"""
    try:
        _, buffer = cv2.imencode('.jpg', frame)
        encoded_image = base64.b64encode(buffer).decode('utf-8')
    except:
        encoded_image = ""
    
    return {
        "detected": False, 
        "class_name": error_msg, 
        "confidence": 0.0, 
        "counts": {"sin_chaleco": 0, "con_chaleco": 0},
        "annotated_frame": encoded_image
    }
# Load model on startup
@app.on_event("startup")
async def startup_event():
    global model
    try:
        logger.info("🚀 Iniciando carga del modelo desde S3...")
        weights_path = download_model_from_s3()
        model = load_yolo_model(weights_path)
        logger.info("✅ Modelo cargado correctamente desde S3")
    except Exception as e:
        logger.error(f"❌ Error al cargar el modelo: {e}")
        model = None

# Health check endpoints
@app.get("/")
async def root():
    return {
        "message": "Safety Vest Detection API", 
        "status": "running",
        "model_loaded": model is not None
    }

@app.get("/api")
async def api_root():
    model_status = "Safety vest model loaded" if model and hasattr(model, 'names') and any('chaleco' in name for name in model.names.values()) else "Pre-trained model (generic)"
    return {
        "message": f"Hello from FastAPI + Safety Vest Detection! - {model_status}",
        "model_loaded": model is not None
    }

@app.get("/api/status")
async def get_status():
    return {
        "status": "running",
        "model_loaded": model is not None,
        "model_type": "safety_vest" if model and hasattr(model, 'names') and any('chaleco' in name for name in model.names.values()) else "generic",
        "timestamp": time.time()
    }

@app.get("/api/statistics")
async def get_statistics():
    return detection_stats

@app.post("/api/reset_statistics")
async def reset_statistics():
    detection_stats['global'] = {'sin_chaleco': 0, 'con_chaleco': 0}
    return {"message": "Statistics reset successfully"}

# Main detection endpoint
@app.post("/api/detect")
async def detect_vests(file: UploadFile = File(...)):
    """
    Process an image and detect safety vests
    Accepts: image file (jpg, png, etc.)
    Returns: detection results with annotated image
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Detection model not loaded")
    
    try:
        # Read and validate image
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Convert to OpenCV format
        np_arr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Process detection
        detection_info = process_frame_with_detection(frame)
        
        # Add statistics to response
        detection_info["statistics"] = detection_stats['global'].copy()
        detection_info["timestamp"] = time.time()
        
        return JSONResponse(content=detection_info)
        
    except Exception as e:
        logger.error(f"Error in detection endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

# Alternative endpoint for base64 encoded images
@app.post("/api/detect-base64")
async def detect_vests_base64(data: dict):
    """
    Process base64 encoded image and detect safety vests
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Detection model not loaded")
    
    try:

        frame_data = data.get("frame_data", "")
        if not frame_data:
            raise HTTPException(status_code=400, detail="No frame data provided")
        
        if frame_data.startswith("data:image"):
            frame_data = frame_data.split(",")[1]

        logger.info(f"📨 Received frame data: {len(frame_data)} bytes")

        # # Convert base64 to image
        # img_bytes = base64.b64decode(frame_data)
        # np_arr = np.frombuffer(img_bytes, np.uint8)
        # frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        

        try:
            img_bytes = base64.b64decode(frame_data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is None:
                raise HTTPException(status_code=400, detail="Failed to decode image")
                
            logger.info(f"🖼️ Decoded frame: {frame.shape}")
        except Exception as e:
            logger.error(f"❌ Image decoding error: {e}")
            raise HTTPException(status_code=400, detail=f"Image decoding error: {str(e)}")

        # Process detection
        detection_info = process_frame_with_detection(frame)
        
        # Add statistics to response
        detection_info["statistics"] = detection_stats['global'].copy()
        detection_info["timestamp"] = time.time()
        
        return JSONResponse(content=detection_info)
        
    except Exception as e:
        logger.error(f"Error in base64 detection endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "model_loaded": model is not None
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        workers=1,
        log_level="info"
    )