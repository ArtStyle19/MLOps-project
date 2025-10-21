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
  const [websocketMessages, setWebsocketMessages] = useState([]);

  const videoRef = useRef(null);
  const processedVideoRef = useRef(null);
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

  const addWebsocketMessage = (message) => {
    setWebsocketMessages((prev) => [
      ...prev.slice(-9), // Mantener solo los últimos 10 mensajes
      `${new Date().toLocaleTimeString()}: ${message}`,
    ]);
  };

  // const connectWebSocket = () => {
  //   const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  //   const wsUrl = `${protocol}//api.settinel.lat/ws/camera`;

  //   console.log("Connecting to WebSocket:", wsUrl);
  //   addWebsocketMessage("Connecting to WebSocket...");

  //   ws.current = new WebSocket(wsUrl);

  //   ws.current.onopen = () => {
  //     console.log("✅ WebSocket connected successfully");
  //     addWebsocketMessage("WebSocket connected successfully");
  //     setIsConnected(true);
  //     setConnectionStatus("connected");
  //   };

  //   ws.current.onmessage = (event) => {
  //     try {
  //       const data = JSON.parse(event.data);
  //       console.log("📨 WebSocket message received:", data.type);
  //       addWebsocketMessage(`Received: ${data.type}`);
  //       handleWebSocketMessage(data);
  //     } catch (error) {
  //       console.error("❌ Error parsing WebSocket message:", error);
  //       addWebsocketMessage(`Error: ${error.message}`);
  //     }
  //   };

  //   ws.current.onclose = (event) => {
  //     console.log("🔌 WebSocket disconnected:", event.code, event.reason);
  //     addWebsocketMessage(`Disconnected: ${event.code} ${event.reason}`);
  //     setIsConnected(false);
  //     setIsStreaming(false);
  //     setIsProcessing(false);
  //     setConnectionStatus("disconnected");
  //     stopCamera();
  //   };

  //   ws.current.onerror = (error) => {
  //     console.error("💥 WebSocket error:", error);
  //     addWebsocketMessage("WebSocket error occurred");
  //     setConnectionStatus("error");
  //   };
  // };

  const connectWebSocket = () => {
    const wsUrl = `wss://api.settinel.lat/ws/camera`;

    console.log("Connecting to WebSocket:", wsUrl);
    addWebsocketMessage("Connecting to WebSocket...");

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log("✅ WebSocket connected successfully");
      addWebsocketMessage("WebSocket connected successfully");
      setIsConnected(true);
      setConnectionStatus("connected");

      // Test connection immediately
      ws.current.send(
        JSON.stringify({
          action: "test",
          message: "Connection test",
        })
      );
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("📨 WebSocket message received:", data.type);
        addWebsocketMessage(`Received: ${data.type}`);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error("❌ Error parsing WebSocket message:", error);
        addWebsocketMessage(`Error: ${error.message}`);
      }
    };

    ws.current.onclose = (event) => {
      console.log("🔌 WebSocket disconnected:", event.code, event.reason);
      addWebsocketMessage(`Disconnected: ${event.code} ${event.reason}`);
      setIsConnected(false);
      setIsStreaming(false);
      setIsProcessing(false);
      setConnectionStatus("disconnected");
      stopCamera();

      // Intentar reconectar después de 5 segundos
      setTimeout(() => {
        if (!isConnected) {
          console.log("🔄 Attempting to reconnect WebSocket...");
          connectWebSocket();
        }
      }, 5000);
    };

    ws.current.onerror = (error) => {
      console.error("💥 WebSocket error:", error);
      addWebsocketMessage("WebSocket error occurred");
      setConnectionStatus("error");
    };
  };

  const handleWebSocketMessage = (data) => {
    updateLastUpdate();
    updateFps();

    switch (data.type) {
      case "detection_result":
        setIsProcessing(false);
        addWebsocketMessage(`Detection: ${data.detection.class_name}`);

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
          console.log("🖼️ Updated processed video frame");
        } else {
          console.log("❌ No annotated_frame in response");
        }
        break;

      case "error":
        console.error("❌ Server error:", data.message);
        addWebsocketMessage(`Server Error: ${data.message}`);
        setIsProcessing(false);
        alert(`Error del servidor: ${data.message}`);
        break;

      case "info":
        console.log("ℹ️ Server info:", data.message);
        addWebsocketMessage(`Info: ${data.message}`);
        break;

      default:
        console.log("❓ Unknown message type:", data.type);
        addWebsocketMessage(`Unknown: ${data.type}`);
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

  // Iniciar cámara del usuario
  const startCamera = async () => {
    try {
      console.log("📷 Requesting camera access...");
      addWebsocketMessage("Requesting camera access...");

      const constraints = {
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 10 }, // Reducido para mejor performance
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
        addWebsocketMessage("Camera started successfully");
      }

      return true;
    } catch (error) {
      console.error("❌ Error accessing camera:", error);
      addWebsocketMessage(`Camera Error: ${error.message}`);

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
    addWebsocketMessage("Stopping camera...");

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
      const imageData = canvas.toDataURL("image/jpeg", 0.7);
      const base64Data = imageData.split(",")[1];

      // Send frame to server
      if (ws.current.readyState === WebSocket.OPEN) {
        setIsProcessing(true);
        const message = {
          action: "process_frame",
          frame_data: base64Data,
          timestamp: Date.now(),
        };

        ws.current.send(JSON.stringify(message));
        console.log("📤 Sent frame to server, size:", base64Data.length);
        addWebsocketMessage(`Sent frame: ${base64Data.length} bytes`);
      }
    }

    // Continue capturing frames (with throttling)
    if (isStreaming) {
      setTimeout(() => {
        animationRef.current = requestAnimationFrame(captureAndSendFrame);
      }, 200); // ~5 FPS para debugging
    }
  };

  const startStream = async () => {
    if (!isConnected) {
      alert("⚠️ Primero debes conectar el WebSocket");
      return;
    }

    console.log("🎬 Starting stream...");
    addWebsocketMessage("Starting stream...");

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
          addWebsocketMessage("Video ready, starting frame capture");
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
    addWebsocketMessage("Stopping stream...");
    setIsStreaming(false);
    setConnectionStatus("connected");
    stopCamera();

    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify({ action: "stop_stream" }));
    }
  };

  const disconnectWebSocket = () => {
    console.log("🔌 Disconnecting WebSocket...");
    addWebsocketMessage("Disconnecting WebSocket...");
    stopStream();
    if (ws.current) {
      ws.current.close();
    }
  };

  const resetStatistics = async () => {
    try {
      console.log("🔄 Resetting statistics...");
      addWebsocketMessage("Resetting statistics...");
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
        addWebsocketMessage("Statistics reset successfully");
      }
    } catch (error) {
      console.error("❌ Error resetting statistics:", error);
      addWebsocketMessage(`Reset Error: ${error.message}`);
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
                maxWidth: "100%",
                height: "auto",
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
              <h3>🔧 Debug WebSocket</h3>
              <div className="websocket-log">
                {websocketMessages.map((msg, index) => (
                  <div key={index} className="log-entry">
                    {msg}
                  </div>
                ))}
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
