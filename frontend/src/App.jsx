import React, { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("Loading...");
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [detectionInfo, setDetectionInfo] = useState({
    class_name: "Esperando inicio...",
    confidence: 0,
    detected: false,
    counts: { sin_chaleco: 0, con_chaleco: 0 },
    statistics: { sin_chaleco: 0, con_chaleco: 0 },
  });
  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [lastUpdate, setLastUpdate] = useState("--");
  const [fps, setFps] = useState(0);

  const videoRef = useRef(null);
  const processedVideoRef = useRef(null); // Para mostrar el video procesado
  const canvasRef = useRef(null);
  const ws = useRef(null);
  const streamRef = useRef(null);
  const animationRef = useRef(null);
  const frameCountRef = useRef(0);
  const lastFpsUpdateRef = useRef(Date.now());

  // Check backend status
  useEffect(() => {
    fetch(`https://api.settinel.lat/api`)
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => setMessage("Error: " + err.message));
  }, []);

  const connectWebSocket = () => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//api.settinel.lat/ws/camera`;

    console.log("Connecting to WebSocket:", wsUrl);
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log("✅ WebSocket connected successfully");
      setIsConnected(true);
      setConnectionStatus("connected");
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("📨 WebSocket message received:", data.type);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error("❌ Error parsing WebSocket message:", error);
      }
    };

    ws.current.onclose = (event) => {
      console.log("🔌 WebSocket disconnected:", event.code, event.reason);
      setIsConnected(false);
      setIsStreaming(false);
      setIsProcessing(false);
      setConnectionStatus("disconnected");
      stopCamera();
    };

    ws.current.onerror = (error) => {
      console.error("💥 WebSocket error:", error);
      setConnectionStatus("error");
    };
  };

  const handleWebSocketMessage = (data) => {
    updateLastUpdate();
    updateFps();

    switch (data.type) {
      case "detection_result":
        setIsProcessing(false);

        if (data.detection) {
          console.log("🎯 Detection result:", data.detection);
          setDetectionInfo((prev) => ({
            ...prev,
            ...data.detection,
            statistics: data.detection.statistics || prev.statistics,
          }));
        }

        // MOSTRAR EL FRAME PROCESADO CON DETECCIONES
        if (data.annotated_frame && processedVideoRef.current) {
          const imageUrl = `data:image/jpeg;base64,${data.annotated_frame}`;
          processedVideoRef.current.src = imageUrl;
        }
        break;

      case "error":
        console.error("❌ Server error:", data.message);
        setIsProcessing(false);
        alert(`Error del servidor: ${data.message}`);
        break;

      case "info":
        console.log("ℹ️ Server info:", data.message);
        break;

      default:
        console.log("❓ Unknown message type:", data.type);
    }
  };

  const updateFps = () => {
    frameCountRef.current++;
    const now = Date.now();
    const elapsed = now - lastFpsUpdateRef.current;

    if (elapsed >= 1000) {
      // Update FPS every second
      setFps(Math.round((frameCountRef.current * 1000) / elapsed));
      frameCountRef.current = 0;
      lastFpsUpdateRef.current = now;
    }
  };

  // Iniciar cámara del usuario
  const startCamera = async () => {
    try {
      console.log("📷 Requesting camera access...");

      const constraints = {
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 15 },
          facingMode: "user",
        },
        audio: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        console.log("✅ Camera started successfully");
      }

      return true;
    } catch (error) {
      console.error("❌ Error accessing camera:", error);
      let errorMessage = `No se pudo acceder a la cámara: ${error.message}`;

      if (error.name === "NotAllowedError") {
        errorMessage =
          "Permiso de cámara denegado. Por favor permite el acceso a la cámara.";
      } else if (error.name === "NotFoundError") {
        errorMessage = "No se encontró ninguna cámara disponible.";
      } else if (error.name === "NotSupportedError") {
        errorMessage = "Tu navegador no soporta acceso a cámara.";
      }

      alert(errorMessage);
      return false;
    }
  };

  // Detener cámara
  const stopCamera = () => {
    console.log("🛑 Stopping camera...");

    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
        console.log("✅ Camera track stopped:", track.kind);
      });
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    if (processedVideoRef.current) {
      processedVideoRef.current.src = "";
    }

    setIsProcessing(false);
    setFps(0);
    frameCountRef.current = 0;
  };

  // Capturar y enviar frames
  const captureAndSendFrame = () => {
    if (
      !videoRef.current ||
      !ws.current ||
      ws.current.readyState !== WebSocket.OPEN ||
      !isStreaming
    ) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    if (video.videoWidth > 0 && video.videoHeight > 0) {
      // Update canvas size if needed
      if (
        canvas.width !== video.videoWidth ||
        canvas.height !== video.videoHeight
      ) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
      }

      // Draw current frame to canvas
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert to JPEG with reduced quality for performance
      const imageData = canvas.toDataURL("image/jpeg", 0.8);
      const base64Data = imageData.split(",")[1];

      // Send frame to server
      if (ws.current.readyState === WebSocket.OPEN) {
        setIsProcessing(true);
        ws.current.send(
          JSON.stringify({
            action: "process_frame",
            frame_data: base64Data,
            timestamp: Date.now(),
          })
        );
      }
    }

    // Continue capturing frames (with throttling)
    if (isStreaming) {
      animationRef.current = requestAnimationFrame(captureAndSendFrame);
    }
  };

  const startStream = async () => {
    if (!isConnected) {
      alert("⚠️ Primero debes conectar el WebSocket");
      return;
    }

    console.log("🎬 Starting stream...");

    // Start camera
    const cameraStarted = await startCamera();
    if (!cameraStarted) {
      return;
    }

    // Wait for video to be ready
    if (videoRef.current) {
      const waitForVideo = () => {
        if (videoRef.current.readyState >= 2) {
          // HAVE_CURRENT_DATA
          console.log("🎥 Video is ready, starting frame capture");
          setIsStreaming(true);
          setConnectionStatus("streaming");

          // Configure canvas
          if (canvasRef.current) {
            canvasRef.current.width = videoRef.current.videoWidth;
            canvasRef.current.height = videoRef.current.videoHeight;
          }

          // Start frame capture
          captureAndSendFrame();
        } else {
          setTimeout(waitForVideo, 100);
        }
      };
      waitForVideo();
    }
  };

  const stopStream = () => {
    console.log("⏹️ Stopping stream...");
    setIsStreaming(false);
    setConnectionStatus("connected");
    stopCamera();

    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify({ action: "stop_stream" }));
    }
  };

  const disconnectWebSocket = () => {
    console.log("🔌 Disconnecting WebSocket...");
    stopStream();
    if (ws.current) {
      ws.current.close();
    }
  };

  const resetStatistics = async () => {
    try {
      console.log("🔄 Resetting statistics...");
      const response = await fetch(
        "https://api.settinel.lat/api/reset_statistics",
        {
          method: "POST",
        }
      );
      if (response.ok) {
        setDetectionInfo((prev) => ({
          ...prev,
          statistics: { sin_chaleco: 0, con_chaleco: 0 },
          counts: { sin_chaleco: 0, con_chaleco: 0 },
        }));
        console.log("✅ Statistics reset successfully");
      }
    } catch (error) {
      console.error("❌ Error resetting statistics:", error);
    }
  };

  const updateLastUpdate = () => {
    const now = new Date();
    setLastUpdate(now.toLocaleTimeString());
  };

  const getDetectionStatusClass = () => {
    if (!detectionInfo.detected) return "detection-neutral";
    if (detectionInfo.class_name.includes("con_chaleco"))
      return "detection-safe";
    if (detectionInfo.class_name.includes("sin_chaleco"))
      return "detection-danger";
    return "detection-neutral";
  };

  const getDetectionDisplayText = () => {
    if (!detectionInfo.detected) return "🔍 Analizando...";
    if (detectionInfo.class_name.includes("con_chaleco"))
      return "✅ Con Chaleco";
    if (detectionInfo.class_name.includes("sin_chaleco"))
      return "❌ Sin Chaleco";
    return detectionInfo.class_name;
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case "connected":
        return "Conectado";
      case "streaming":
        return "Transmitiendo";
      case "error":
        return "Error de Conexión";
      default:
        return "Desconectado";
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (ws.current) {
        ws.current.close();
      }
      stopCamera();
    };
  }, []);

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <h1>🔍 Detección de Chalecos de Seguridad</h1>
          <p>Detección en tiempo real con IA</p>
        </div>

        <div className={`connection-status ${connectionStatus}`}>
          <span className="status-indicator"></span>
          {getConnectionStatusText()}
          {isProcessing && (
            <span className="processing-indicator">Procesando...</span>
          )}
        </div>

        <div className="controls">
          <div className="control-group">
            <h3>Control de Cámara</h3>
            <div className="button-group">
              <button
                className={`btn btn-primary ${!isConnected ? "" : "disabled"}`}
                onClick={connectWebSocket}
                disabled={isConnected}
              >
                🔗 Conectar
              </button>
              <button
                className={`btn btn-success ${
                  isConnected && !isStreaming ? "" : "disabled"
                }`}
                onClick={startStream}
                disabled={!isConnected || isStreaming}
              >
                🎬 Iniciar Detección
              </button>
              <button
                className={`btn btn-danger ${isStreaming ? "" : "disabled"}`}
                onClick={stopStream}
                disabled={!isStreaming}
              >
                ⏹️ Detener
              </button>
              <button className="btn btn-warning" onClick={resetStatistics}>
                🔄 Reiniciar Stats
              </button>
            </div>
          </div>
        </div>

        <div className="main-content">
          <div className="video-container">
            {/* Video OCULTO para captura */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={{ display: "none" }}
            />

            {/* Canvas oculto para procesamiento */}
            <canvas ref={canvasRef} style={{ display: "none" }} />

            {/* Video PROCESADO con detecciones - ESTE SE MUESTRA */}
            <img
              ref={processedVideoRef}
              alt="Detección en tiempo real"
              className="processed-video"
              style={{
                display: isStreaming ? "block" : "none",
              }}
            />

            {!isStreaming && (
              <div className="placeholder-text">
                <h2>🎥 Presiona "Iniciar Detección"</h2>
                <p>Se solicitará acceso a tu cámara web</p>
                <p>Los cuadros de detección aparecerán aquí</p>
                {!isConnected && (
                  <p className="warning">⚠️ Primero debes conectar</p>
                )}
              </div>
            )}
          </div>

          <div className="info-panel">
            <div className="info-card">
              <h3>🔍 Estado de Detección</h3>
              <div className={`detection-status ${getDetectionStatusClass()}`}>
                {getDetectionDisplayText()}
              </div>
              <div className="status-item">
                <strong>Confianza:</strong>
                <span className="confidence-value">
                  {detectionInfo.detected
                    ? `${(detectionInfo.confidence * 100).toFixed(1)}%`
                    : "--"}
                </span>
              </div>
              <div className="status-item">
                <strong>Modelo:</strong>
                <span>{message}</span>
              </div>
              <div className="status-item">
                <strong>FPS:</strong>
                <span>{fps}</span>
              </div>
            </div>

            <div className="info-card">
              <h3>📊 Detecciones Actuales</h3>
              <div className="statistics">
                <div className="stat-item">
                  <div className="stat-label">❌ Sin Chaleco</div>
                  <div className="stat-value danger">
                    {detectionInfo.counts.sin_chaleco || 0}
                  </div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">✅ Con Chaleco</div>
                  <div className="stat-value safe">
                    {detectionInfo.counts.con_chaleco || 0}
                  </div>
                </div>
              </div>
            </div>

            <div className="info-card">
              <h3>📈 Estadísticas Totales</h3>
              <div className="statistics">
                <div className="stat-item">
                  <div className="stat-label">Total Sin Chaleco</div>
                  <div className="stat-value danger">
                    {detectionInfo.statistics.sin_chaleco || 0}
                  </div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">Total Con Chaleco</div>
                  <div className="stat-value safe">
                    {detectionInfo.statistics.con_chaleco || 0}
                  </div>
                </div>
              </div>
            </div>

            <div className="info-card">
              <h3>⚙️ Sistema</h3>
              <div className="status-item">
                <strong>WebSocket:</strong>
                <span>{isConnected ? "✅ Conectado" : "❌ Desconectado"}</span>
              </div>
              <div className="status-item">
                <strong>Cámara:</strong>
                <span>{isStreaming ? "✅ Activa" : "❌ Inactiva"}</span>
              </div>
              <div className="status-item">
                <strong>Procesando:</strong>
                <span>{isProcessing ? "🔄 Sí" : "✅ No"}</span>
              </div>
              <div className="status-item">
                <strong>Última Actualización:</strong>
                <span>{lastUpdate}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
