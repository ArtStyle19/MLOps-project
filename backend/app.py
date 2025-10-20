# from flask import Flask, jsonify
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)

# @app.route('/api')
# def hello():
#     return jsonify(message="Hello from Flask + Gunicorn!")

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)



from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import json
import base64
import cv2
import numpy as np
import asyncio
from ultralytics import YOLO
import os
from pathlib import Path
from typing import Optional, Dict, Any
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.camera_instances: Dict[str, cv2.VideoCapture] = {}
        self.detection_stats: Dict[str, Dict[str, int]] = {}

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
        if client_id in self.camera_instances:
            self.camera_instances[client_id].release()
            del self.camera_instances[client_id]
        logger.info(f"Client disconnected: {client_id}")

    def get_camera(self, client_id: str, camera_index: int = 0) -> Optional[cv2.VideoCapture]:
        """Get or create camera instance for client"""
        if client_id not in self.camera_instances:
            try:
                cap = cv2.VideoCapture(camera_index)
                # Set camera properties for better performance
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                
                if cap.isOpened():
                    self.camera_instances[client_id] = cap
                    logger.info(f"Camera {camera_index} opened for: {client_id}")
                else:
                    logger.error(f"Failed to open camera {camera_index} for: {client_id}")
                    return None
            except Exception as e:
                logger.error(f"Error opening camera: {e}")
                return None
        return self.camera_instances[client_id]

    async def process_frame_with_detection(self, frame: np.ndarray, model, client_id: str) -> tuple:
        """Process frame with YOLO detection and return annotated frame + detection info"""
        try:
            # Perform detection
            results = model(frame, verbose=False, conf=0.5)  # Confidence threshold
            
            detection_info = {
                "detected": False,
                "class_name": "Sin detección",
                "confidence": 0.0,
                "counts": {"sin_chaleco": 0, "con_chaleco": 0}
            }
            
            annotated_frame = frame.copy()
            
            if len(results[0].boxes) > 0:
                # Use the highest confidence detection for main info
                boxes = results[0].boxes
                max_confidence_idx = np.argmax([float(box.conf[0]) for box in boxes])
                box = boxes[max_confidence_idx]
                
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                
                # Get class names from model
                class_names = getattr(results[0], 'names', {0: 'sin_chaleco', 1: 'con_chaleco'})
                class_name = class_names.get(class_id, f"Clase {class_id}")
                
                detection_info.update({
                    "detected": True,
                    "class_name": class_name,
                    "confidence": confidence
                })
                
                # Count all detections above confidence threshold
                for box in boxes:
                    box_confidence = float(box.conf[0])
                    if box_confidence > 0.5:  # Only count confident detections
                        box_class_id = int(box.cls[0])
                        box_class_name = class_names.get(box_class_id, f"Clase {box_class_id}")
                        
                        if "sin_chaleco" in box_class_name.lower():
                            detection_info["counts"]["sin_chaleco"] += 1
                        elif "con_chaleco" in box_class_name.lower():
                            detection_info["counts"]["con_chaleco"] += 1
                
                # Update global statistics (only count unique frames)
                if detection_info["counts"]["sin_chaleco"] > 0:
                    self.detection_stats[client_id]["sin_chaleco"] += 1
                if detection_info["counts"]["con_chaleco"] > 0:
                    self.detection_stats[client_id]["con_chaleco"] += 1
                
                # Get annotated frame
                annotated_frame = results[0].plot()
            
            return annotated_frame, detection_info
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return frame, {
                "detected": False, 
                "class_name": "Error en detección", 
                "confidence": 0.0, 
                "counts": {"sin_chaleco": 0, "con_chaleco": 0}
            }

    async def capture_frame(self, client_id: str, model, camera_index: int = 0) -> tuple:
        """Capture and process a single frame"""
        cap = self.get_camera(client_id, camera_index)
        if not cap:
            return None, None

        try:
            ret, frame = cap.read()
            if ret:
                # Process frame with detection
                processed_frame, detection_info = await self.process_frame_with_detection(frame, model, client_id)
                
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                jpeg_data = base64.b64encode(buffer).decode('utf-8')
                
                return jpeg_data, detection_info
            else:
                logger.warning(f"Failed to read frame from camera for client: {client_id}")
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            
        return None, None

# Global instances
connection_manager = ConnectionManager()

# -----------------------------
# 🔥 Cargar modelo desde S3 al iniciar
# -----------------------------
weights_path = download_model_from_s3()
model = load_yolo_model(weights_path)

@app.on_event("startup")
async def startup_event():
    global model
    try:
        logger.info("🚀 Iniciando carga del modelo desde S3...")
        weights_path = download_model_from_s3()
        model = load_yolo_model(weights_path)  # ✅ Pasar el path
        logger.info("✅ Modelo cargado correctamente desde S3")
    except Exception as e:
        logger.error(f"❌ Error al cargar el modelo: {e}")
        model = None


# Add CORS headers manually
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response
# Add CORS headers manually
@app.middleware("https")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Safety Vest Detection API", 
        "status": "running",
        "model_loaded": model is not None
    }

@app.get("/api")
async def api_root():
    """API endpoint for frontend"""
    model_status = "Safety vest model loaded" if model and hasattr(model, 'names') and any('chaleco' in name for name in model.names.values()) else "Pre-trained model (generic)"
    return {
        "message": f"Hello from FastAPI + Safety Vest Detection! - {model_status}",
        "model_loaded": model is not None
    }

@app.get("/api/status")
async def get_status():
    """Get API status"""
    return {
        "status": "running",
        "model_loaded": model is not None,
        "model_type": "safety_vest" if model and hasattr(model, 'names') and any('chaleco' in name for name in model.names.values()) else "generic",
        "active_connections": len(connection_manager.active_connections),
        "timestamp": time.time()
    }

@app.get("/api/statistics")
async def get_statistics():
    """Get detection statistics"""
    return connection_manager.detection_stats

@app.post("/api/reset_statistics")
async def reset_statistics():
    """Reset all detection statistics"""
    for client_id in connection_manager.detection_stats:
        connection_manager.detection_stats[client_id] = {'sin_chaleco': 0, 'con_chaleco': 0}
    return {"message": "Statistics reset successfully"}

@app.websocket("/ws/camera")
async def websocket_camera(websocket: WebSocket):
    """WebSocket endpoint for real-time camera streaming with detection"""
    client_id = f"client_{id(websocket)}_{int(time.time())}"
    
    await connection_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Wait for client message
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action")
            
            if action == "start_stream":
                camera_index = message.get("camera_index", 0)
                logger.info(f"Starting stream for {client_id} on camera {camera_index}")
                
                # Start streaming frames
                stream_active = True
                while stream_active and client_id in connection_manager.active_connections:
                    try:
                        # Check for new messages (non-blocking)
                        try:
                            new_data = await asyncio.wait_for(websocket.receive_text(), timeout=0.001)
                            new_message = json.loads(new_data)
                            if new_message.get("action") == "stop_stream":
                                logger.info(f"Stop stream received for {client_id}")
                                stream_active = False
                                break
                        except asyncio.TimeoutError:
                            pass  # No new message, continue streaming
                        
                        if model is None:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Detection model not loaded"
                            })
                            await asyncio.sleep(1)
                            continue
                        
                        # Capture and process frame
                        frame_data, detection_info = await connection_manager.capture_frame(
                            client_id, model, camera_index
                        )
                        
                        if frame_data and detection_info:
                            # Add statistics to detection info
                            detection_info["statistics"] = connection_manager.detection_stats[client_id].copy()
                            
                            await websocket.send_json({
                                "type": "frame",
                                "data": frame_data,
                                "detection": detection_info,
                                "timestamp": time.time()
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Failed to capture frame"
                            })
                    
                    except Exception as e:
                        logger.error(f"Stream error for {client_id}: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Stream error: {str(e)}"
                        })
                        break
                    
                    # Control frame rate
                    await asyncio.sleep(0.033)  # ~30 FPS
                
                logger.info(f"Stream ended for {client_id}")
                
            elif action == "stop_stream":
                logger.info(f"Stop stream requested for {client_id}")
                # Stream will be stopped in the loop
                await websocket.send_json({
                    "type": "info",
                    "message": "Stream stopped"
                })
                
            elif action == "capture_photo":
                # Implement photo capture functionality
                await websocket.send_json({
                    "type": "info", 
                    "message": "Photo capture feature coming soon"
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
        connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        connection_manager.disconnect(client_id)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down application...")
    
    # Clean up camera resources
    for client_id in list(connection_manager.camera_instances.keys()):
        try:
            connection_manager.camera_instances[client_id].release()
            logger.info(f"Released camera for {client_id}")
        except Exception as e:
            logger.error(f"Error releasing camera for {client_id}: {e}")
    
    logger.info("Application shutdown complete")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for load balancers and monitoring"""
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
        reload=False,  # Set to False in production
        workers=1,     # WebSocket connections work best with 1 worker
        log_level="info"
    )