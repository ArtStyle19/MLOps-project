# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn
# import json
# import base64
# import cv2
# import numpy as np
# import asyncio
# from ultralytics import YOLO
# import os
# import logging
# import time

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# from model_loader import download_model_from_s3, load_yolo_model

# app = FastAPI(
#     title="Safety Vest Detection API",
#     description="Real-time safety vest detection using YOLO and WebSockets",
#     version="1.0.0"
# )

# # CORS middleware - SOLO UNA VEZ
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: dict = {}
#         self.detection_stats: dict = {}

#     async def connect(self, websocket: WebSocket, client_id: str):
#         await websocket.accept()
#         self.active_connections[client_id] = websocket
#         self.detection_stats[client_id] = {'sin_chaleco': 0, 'con_chaleco': 0}
#         logger.info(f"Client connected: {client_id}")

#     def disconnect(self, client_id: str):
#         if client_id in self.active_connections:
#             del self.active_connections[client_id]
#         if client_id in self.detection_stats:
#             del self.detection_stats[client_id]
#         logger.info(f"Client disconnected: {client_id}")

#     async def process_frame_with_detection(self, frame: np.ndarray, model, client_id: str) -> dict:
#         """Process frame with YOLO detection and return detection info with annotated image"""
#         try:
#             logger.info(f"Processing frame for {client_id} - Frame shape: {frame.shape}")
            
#             # Perform detection
#             results = model(frame, verbose=False, conf=0.5)
            
#             detection_info = {
#                 "detected": False,
#                 "class_name": "Sin detección",
#                 "confidence": 0.0,
#                 "counts": {"sin_chaleco": 0, "con_chaleco": 0}
#             }
            
#             # Create a copy of the frame to draw on
#             annotated_frame = frame.copy()
            
#             if len(results[0].boxes) > 0:
#                 boxes = results[0].boxes
#                 class_names = getattr(results[0], 'names', {0: 'sin_chaleco', 1: 'con_chaleco'})
                
#                 logger.info(f"Detections found: {len(boxes)}")
                
#                 # Use the highest confidence detection for main info
#                 max_confidence_idx = np.argmax([float(box.conf[0]) for box in boxes])
#                 box = boxes[max_confidence_idx]
                
#                 confidence = float(box.conf[0])
#                 class_id = int(box.cls[0])
#                 class_name = class_names.get(class_id, f"Clase {class_id}")
                
#                 detection_info.update({
#                     "detected": True,
#                     "class_name": class_name,
#                     "confidence": confidence
#                 })
                
#                 # Count all detections and draw boxes
#                 for i, box in enumerate(boxes):
#                     box_confidence = float(box.conf[0])
#                     if box_confidence > 0.3:  # Bajar umbral para ver más detecciones
#                         box_class_id = int(box.cls[0])
#                         box_class_name = class_names.get(box_class_id, f"Clase {box_class_id}")
                        
#                         # Get box coordinates
#                         x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
#                         # Define colors based on class
#                         if "sin_chaleco" in box_class_name.lower():
#                             color = (0, 0, 255)  # Red for no vest
#                             detection_info["counts"]["sin_chaleco"] += 1
#                         elif "con_chaleco" in box_class_name.lower():
#                             color = (0, 255, 0)  # Green for vest
#                             detection_info["counts"]["con_chaleco"] += 1
#                         else:
#                             color = (255, 255, 0)  # Yellow for other
                        
#                         # Draw bounding box
#                         cv2.rectangle(annotated_frame, 
#                                     (int(x1), int(y1)), 
#                                     (int(x2), int(y2)), 
#                                     color, 3)
                        
#                         # Draw label
#                         label = f"{box_class_name} {box_confidence:.2f}"
#                         label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        
#                         # Label background
#                         cv2.rectangle(annotated_frame,
#                                     (int(x1), int(y1) - label_size[1] - 10),
#                                     (int(x1) + label_size[0], int(y1)),
#                                     color, -1)
                        
#                         # Label text
#                         cv2.putText(annotated_frame, label,
#                                 (int(x1), int(y1) - 5),
#                                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
#                 logger.info(f"Detection counts: {detection_info['counts']}")
                
#                 # Update global statistics
#                 if detection_info["counts"]["sin_chaleco"] > 0:
#                     self.detection_stats[client_id]["sin_chaleco"] += 1
#                 if detection_info["counts"]["con_chaleco"] > 0:
#                     self.detection_stats[client_id]["con_chaleco"] += 1
            
#             # Add frame counter and info text
#             cv2.putText(annotated_frame, f"Detections: {detection_info['counts']}", 
#                     (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
#             cv2.putText(annotated_frame, f"Status: {detection_info['class_name']}", 
#                     (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
#             # Encode the annotated frame
#             _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
#             encoded_image = base64.b64encode(buffer).decode('utf-8')
            
#             detection_info["annotated_frame"] = encoded_image
            
#             return detection_info
            
#         except Exception as e:
#             logger.error(f"Detection error: {e}")
#             # Return original frame in case of error
#             _, buffer = cv2.imencode('.jpg', frame)
#             encoded_image = base64.b64encode(buffer).decode('utf-8')
            
#             return {
#                 "detected": False, 
#                 "class_name": f"Error: {str(e)}", 
#                 "confidence": 0.0, 
#                 "counts": {"sin_chaleco": 0, "con_chaleco": 0},
#                 "annotated_frame": encoded_image
#             }
    



# # Global instances
# connection_manager = ConnectionManager()

# #####################3
# model = None

# # -----------------------------
# # 🔥 Cargar modelo SOLO UNA VEZ al iniciar
# # -----------------------------
# @app.on_event("startup")
# async def startup_event():
#     global model
#     try:
#         logger.info("🚀 Iniciando carga del modelo desde S3...")
#         weights_path = download_model_from_s3()
#         model = load_yolo_model(weights_path)
#         logger.info("✅ Modelo cargado correctamente desde S3")
#     except Exception as e:
#         logger.error(f"❌ Error al cargar el modelo: {e}")
#         model = None

# # Endpoints
# @app.get("/")
# async def root():
#     return {
#         "message": "Safety Vest Detection API", 
#         "status": "running",
#         "model_loaded": model is not None
#     }

# @app.get("/api")
# async def api_root():
#     model_status = "Safety vest model loaded" if model and hasattr(model, 'names') and any('chaleco' in name for name in model.names.values()) else "Pre-trained model (generic)"
#     return {
#         "message": f"Hello from FastAPI + Safety Vest Detection! - {model_status}",
#         "model_loaded": model is not None
#     }

# @app.get("/api/status")
# async def get_status():
#     return {
#         "status": "running",
#         "model_loaded": model is not None,
#         "model_type": "safety_vest" if model and hasattr(model, 'names') and any('chaleco' in name for name in model.names.values()) else "generic",
#         "active_connections": len(connection_manager.active_connections),
#         "timestamp": time.time()
#     }

# @app.get("/api/statistics")
# async def get_statistics():
#     return connection_manager.detection_stats

# @app.post("/api/reset_statistics")
# async def reset_statistics():
#     for client_id in connection_manager.detection_stats:
#         connection_manager.detection_stats[client_id] = {'sin_chaleco': 0, 'con_chaleco': 0}
#     return {"message": "Statistics reset successfully"}

# # WebSocket para procesar frames del CLIENTE
# @app.websocket("/ws/camera")
# async def websocket_camera(websocket: WebSocket):
#     """WebSocket endpoint para procesar frames del cliente"""
#     client_id = f"client_{id(websocket)}_{int(time.time())}"
    
#     await connection_manager.connect(websocket, client_id)
    
#     try:
#         while True:
#             # Recibir mensaje del cliente
#             data = await websocket.receive_text()
#             message = json.loads(data)
#             action = message.get("action")
            
#             if action == "process_frame":
#                 if model is None:
#                     await websocket.send_json({
#                         "type": "error",
#                         "message": "Detection model not loaded"
#                     })
#                     continue
                
#                 try:
#                     # Decodificar frame base64
#                     frame_data = message.get("frame_data", "")
#                     if not frame_data:
#                         await websocket.send_json({
#                             "type": "error", 
#                             "message": "No frame data received"
#                         })
#                         continue
                    
#                     # Convertir base64 a imagen OpenCV
#                     img_bytes = base64.b64decode(frame_data)
#                     np_arr = np.frombuffer(img_bytes, np.uint8)
#                     frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    
#                     if frame is None:
#                         await websocket.send_json({
#                             "type": "error",
#                             "message": "Failed to decode image"
#                         })
#                         continue
                    
#                     # Procesar frame con el modelo YOLO
#                     detection_info = await connection_manager.process_frame_with_detection(
#                         frame, model, client_id
#                     )

#                     # Agregar estadísticas y enviar resultado
#                     detection_info["statistics"] = connection_manager.detection_stats[client_id].copy()

#                     # Extraer el frame anotado para enviarlo por separado
#                     annotated_frame = detection_info.pop("annotated_frame", None)

#                     await websocket.send_json({
#                         "type": "detection_result",
#                         "detection": detection_info,
#                         "annotated_frame": annotated_frame,  # Enviar frame con cuadros
#                         "timestamp": time.time()
#                     })
                    
#                 except Exception as e:
#                     logger.error(f"Error processing frame: {e}")
#                     await websocket.send_json({
#                         "type": "error",
#                         "message": f"Processing error: {str(e)}"
#                     })
                    
#             elif action == "stop_stream":
#                 logger.info(f"Stop stream requested for {client_id}")
#                 await websocket.send_json({
#                     "type": "info",
#                     "message": "Stream stopped"
#                 })
                
#     except WebSocketDisconnect:
#         logger.info(f"WebSocket disconnected: {client_id}")
#         connection_manager.disconnect(client_id)
#     except Exception as e:
#         logger.error(f"WebSocket error for {client_id}: {e}")
#         connection_manager.disconnect(client_id)

# # Health check endpoint
# @app.get("/health")
# async def health_check():
#     return {
#         "status": "healthy",
#         "timestamp": time.time(),
#         "model_loaded": model is not None,
#         "active_connections": len(connection_manager.active_connections)
#     }

# if __name__ == "__main__":
#     uvicorn.run(
#         "app:app",
#         host="0.0.0.0",
#         port=5000,
#         reload=False,
#         workers=1,
#         log_level="info"
#     )


from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import base64
import cv2
import numpy as np
import asyncio
from ultralytics import YOLO
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from model_loader import download_model_from_s3, load_yolo_model

app = FastAPI(
    title="Safety Vest Detection API",
    description="Real-time safety vest detection using YOLO and WebSockets",
    version="1.0.0"
)

# CORS middleware - Configuración más específica
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://settinel.lat",
        "https://www.settinel.lat", 
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
        self.detection_stats: dict = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.detection_stats[client_id] = {'sin_chaleco': 0, 'con_chaleco': 0}
        logger.info(f"Client connected: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.detection_stats:
            del self.detection_stats[client_id]
        logger.info(f"Client disconnected: {client_id}")

    async def process_frame_with_detection(self, frame: np.ndarray, model, client_id: str) -> dict:
        """Process frame with YOLO detection and return detection info with annotated image"""
        try:
            logger.info(f"Processing frame for {client_id} - Frame shape: {frame.shape}")
            
            # Perform detection
            results = model(frame, verbose=False, conf=0.3)  # Reducir confianza para más detecciones
            
            detection_info = {
                "detected": False,
                "class_name": "Sin detección",
                "confidence": 0.0,
                "counts": {"sin_chaleco": 0, "con_chaleco": 0}
            }
            
            # Create a copy of the frame to draw on
            annotated_frame = frame.copy()
            
            if len(results[0].boxes) > 0:
                boxes = results[0].boxes
                class_names = getattr(results[0], 'names', {0: 'sin_chaleco', 1: 'con_chaleco'})
                
                logger.info(f"Detections found: {len(boxes)}")
                
                # Count all detections and draw boxes
                for i, box in enumerate(boxes):
                    box_confidence = float(box.conf[0])
                    if box_confidence > 0.3:
                        box_class_id = int(box.cls[0])
                        box_class_name = class_names.get(box_class_id, f"Clase {box_class_id}")
                        
                        # Get box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Define colors based on class
                        if "sin_chaleco" in box_class_name.lower():
                            color = (0, 0, 255)  # Red for no vest
                            detection_info["counts"]["sin_chaleco"] += 1
                        elif "con_chaleco" in box_class_name.lower():
                            color = (0, 255, 0)  # Green for vest
                            detection_info["counts"]["con_chaleco"] += 1
                        else:
                            color = (255, 255, 0)  # Yellow for other
                        
                        # Draw bounding box
                        cv2.rectangle(annotated_frame, 
                                    (int(x1), int(y1)), 
                                    (int(x2), int(y2)), 
                                    color, 3)
                        
                        # Draw label
                        label = f"{box_class_name} {box_confidence:.2f}"
                        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        
                        # Label background
                        cv2.rectangle(annotated_frame,
                                    (int(x1), int(y1) - label_size[1] - 10),
                                    (int(x1) + label_size[0], int(y1)),
                                    color, -1)
                        
                        # Label text
                        cv2.putText(annotated_frame, label,
                                (int(x1), int(y1) - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Update detection info if any detections
                if detection_info["counts"]["sin_chaleco"] > 0 or detection_info["counts"]["con_chaleco"] > 0:
                    detection_info.update({
                        "detected": True,
                        "class_name": f"Detecciones: {detection_info['counts']}",
                        "confidence": box_confidence
                    })
                
                logger.info(f"Detection counts: {detection_info['counts']}")
                
                # Update global statistics
                if detection_info["counts"]["sin_chaleco"] > 0:
                    self.detection_stats[client_id]["sin_chaleco"] += detection_info["counts"]["sin_chaleco"]
                if detection_info["counts"]["con_chaleco"] > 0:
                    self.detection_stats[client_id]["con_chaleco"] += detection_info["counts"]["con_chaleco"]
            
            # Add frame counter and info text
            cv2.putText(annotated_frame, f"Detections: {detection_info['counts']}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(annotated_frame, f"Status: {detection_info['class_name']}", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Encode the annotated frame
            _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            encoded_image = base64.b64encode(buffer).decode('utf-8')
            
            detection_info["annotated_frame"] = encoded_image
            
            return detection_info
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            # Return original frame in case of error
            _, buffer = cv2.imencode('.jpg', frame)
            encoded_image = base64.b64encode(buffer).decode('utf-8')
            
            return {
                "detected": False, 
                "class_name": f"Error: {str(e)}", 
                "confidence": 0.0, 
                "counts": {"sin_chaleco": 0, "con_chaleco": 0},
                "annotated_frame": encoded_image
            }

# Global instances
connection_manager = ConnectionManager()
model = None

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

# Endpoints (mantener los mismos que tenías)

# WebSocket para procesar frames del CLIENTE - VERSIÓN MEJORADA
@app.websocket("/ws/camera")
async def websocket_camera(websocket: WebSocket):
    """WebSocket endpoint para procesar frames del cliente"""
    client_id = f"client_{id(websocket)}_{int(time.time())}"
    
    await connection_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Recibir mensaje del cliente
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action")
            
            if action == "process_frame":
                if model is None:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Detection model not loaded"
                    })
                    continue
                
                try:
                    # Decodificar frame base64
                    frame_data = message.get("frame_data", "")
                    if not frame_data:
                        await websocket.send_json({
                            "type": "error", 
                            "message": "No frame data received"
                        })
                        continue
                    
                    # Convertir base64 a imagen OpenCV
                    img_bytes = base64.b64decode(frame_data)
                    np_arr = np.frombuffer(img_bytes, np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    
                    if frame is None:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to decode image"
                        })
                        continue
                    
                    # Procesar frame con el modelo YOLO
                    detection_info = await connection_manager.process_frame_with_detection(
                        frame, model, client_id
                    )

                    # Agregar estadísticas y enviar resultado
                    detection_info["statistics"] = connection_manager.detection_stats[client_id].copy()

                    # Extraer el frame anotado para enviarlo por separado
                    annotated_frame = detection_info.pop("annotated_frame", None)

                    await websocket.send_json({
                        "type": "detection_result",
                        "detection": detection_info,
                        "annotated_frame": annotated_frame,
                        "timestamp": time.time()
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing frame: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Processing error: {str(e)}"
                    })
                    
            elif action == "stop_stream":
                logger.info(f"Stop stream requested for {client_id}")
                await websocket.send_json({
                    "type": "info",
                    "message": "Stream stopped"
                })
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
        connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        connection_manager.disconnect(client_id)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "model_loaded": model is not None,
        "active_connections": len(connection_manager.active_connections)
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