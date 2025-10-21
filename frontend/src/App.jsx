import React, { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("Loading...");
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
  const [apiMessages, setApiMessages] = useState([]);

  const videoRef = useRef(null);
  const processedVideoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const frameIntervalRef = useRef(null);
  const frameCountRef = useRef(0);
  const lastFpsUpdateRef = useRef(Date.now());

  // Check backend status on load
  useEffect(() => {
    checkBackendStatus();
  }, []);

  const addApiMessage = (message) => {
    setApiMessages((prev) => [
      ...prev.slice(-9),
      `${new Date().toLocaleTimeString()}: ${message}`,
    ]);
  };

  const checkBackendStatus = async () => {
    try {
      const response = await fetch("https://api.settinel.lat/api/status");
      const data = await response.json();
      setMessage(data.message || "Backend connected");
      setConnectionStatus("connected");
      addApiMessage("Backend status: Connected");
    } catch (error) {
      setMessage("Error connecting to backend");
      setConnectionStatus("error");
      addApiMessage(`Backend Error: ${error.message}`);
    }
  };

  const updateFps = () => {
    frameCountRef.current++;
    const now = Date.now();
    const elapsed = now - lastFpsUpdateRef.current;

    if (elapsed >= 1000) {
      setFps(Math.round((frameCountRef.current * 1000) / elapsed));
      frameCountRef.current = 0;
      lastFpsUpdateRef.current = now;
    }
  };

  const updateLastUpdate = () => {
    const now = new Date();
    setLastUpdate(now.toLocaleTimeString());
  };

  // Start camera
  const startCamera = async () => {
    try {
      console.log("📷 Requesting camera access...");
      addApiMessage("Requesting camera access...");

      const constraints = {
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 10 },
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
        addApiMessage("Camera started successfully");
      }

      return true;
    } catch (error) {
      console.error("❌ Error accessing camera:", error);
      addApiMessage(`Camera Error: ${error.message}`);

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

  // Stop camera
  const stopCamera = () => {
    console.log("🛑 Stopping camera...");
    addApiMessage("Stopping camera...");

    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
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

  // Capture frame and send to API
  const captureAndSendFrame = async () => {
    if (!videoRef.current || !isStreaming) {
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
      const imageData = canvas.toDataURL("image/jpeg", 0.7);
      const base64Data = imageData.split(",")[1];

      // Send frame to server
      try {
        setIsProcessing(true);

        const response = await fetch(
          "https://api.settinel.lat/api/detect-base64",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              frame_data: base64Data,
              timestamp: Date.now(),
            }),
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        updateLastUpdate();
        updateFps();

        addApiMessage(`Detection: ${data.class_name}`);

        if (data) {
          console.log("🎯 Detection result:", data);
          setDetectionInfo((prev) => ({
            ...prev,
            ...data,
            statistics: data.statistics || prev.statistics,
          }));
        }

        // Display processed frame with detections
        if (data.annotated_frame && processedVideoRef.current) {
          const imageUrl = `data:image/jpeg;base64,${data.annotated_frame}`;
          processedVideoRef.current.src = imageUrl;
          console.log("🖼️ Updated processed video frame");
        }
      } catch (error) {
        console.error("❌ Error sending frame:", error);
        addApiMessage(`API Error: ${error.message}`);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const startStream = async () => {
    console.log("🎬 Starting stream...");
    addApiMessage("Starting stream...");

    // Start camera
    const cameraStarted = await startCamera();
    if (!cameraStarted) {
      return;
    }

    // Wait for video to be ready
    if (videoRef.current) {
      const waitForVideo = () => {
        if (videoRef.current.readyState >= 2) {
          console.log("🎥 Video is ready, starting frame capture");
          addApiMessage("Video ready, starting frame capture");
          setIsStreaming(true);
          setConnectionStatus("streaming");

          // Configure canvas
          if (canvasRef.current) {
            canvasRef.current.width = videoRef.current.videoWidth;
            canvasRef.current.height = videoRef.current.videoHeight;
          }

          // Start frame capture with interval (every 500ms = 2 FPS)
          frameIntervalRef.current = setInterval(captureAndSendFrame, 500);
        } else {
          setTimeout(waitForVideo, 100);
        }
      };
      waitForVideo();
    }
  };

  const stopStream = () => {
    console.log("⏹️ Stopping stream...");
    addApiMessage("Stopping stream...");
    setIsStreaming(false);
    setConnectionStatus("connected");
    stopCamera();
  };

  const resetStatistics = async () => {
    try {
      console.log("🔄 Resetting statistics...");
      addApiMessage("Resetting statistics...");
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
        addApiMessage("Statistics reset successfully");
      }
    } catch (error) {
      console.error("❌ Error resetting statistics:", error);
      addApiMessage(`Reset Error: ${error.message}`);
    }
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
      stopCamera();
    };
  }, []);

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <h1>🔍 Detección de Chalecos de Seguridad</h1>
          <p>Detección en tiempo real con IA - Sin WebSockets</p>
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
                className={`btn btn-success ${!isStreaming ? "" : "disabled"}`}
                onClick={startStream}
                disabled={isStreaming}
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
              <button className="btn btn-info" onClick={checkBackendStatus}>
                🔍 Verificar Backend
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
                maxWidth: "100%",
                height: "auto",
                border: "2px solid #333",
                borderRadius: "8px",
              }}
            />

            {!isStreaming && (
              <div className="placeholder-text">
                <h2>🎥 Presiona "Iniciar Detección"</h2>
                <p>Se solicitará acceso a tu cámara web</p>
                <p>Los cuadros de detección aparecerán aquí</p>
                {connectionStatus === "error" && (
                  <p className="warning">
                    ⚠️ Problema de conexión con el backend
                  </p>
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
              <h3>🔧 Debug API</h3>
              <div className="api-log">
                {apiMessages.map((msg, index) => (
                  <div key={index} className="log-entry">
                    {msg}
                  </div>
                ))}
              </div>
            </div>

            <div className="info-card">
              <h3>⚙️ Sistema</h3>
              <div className="status-item">
                <strong>Backend:</strong>
                <span>
                  {connectionStatus === "connected" ||
                  connectionStatus === "streaming"
                    ? "✅ Conectado"
                    : "❌ Desconectado"}
                </span>
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
