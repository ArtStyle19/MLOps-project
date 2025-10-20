// import { useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";

// import React, { useEffect, useState } from "react";
import React, { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("Loading...");
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [detectionInfo, setDetectionInfo] = useState({
    class_name: "Esperando inicio...",
    confidence: 0,
    detected: false,
    statistics: { sin_chaleco: 0, con_chaleco: 0 },
  });
  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [lastUpdate, setLastUpdate] = useState("--");
  const [cameraIndex, setCameraIndex] = useState(0);

  const videoFeedRef = useRef(null);
  const ws = useRef(null);

  // Check backend status on component mount
  useEffect(() => {
    fetch(`https://api.settinel.lat/api`)
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => setMessage("Error: " + err.message));
  }, []);

  const connectWebSocket = () => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//api.settinel.lat/ws/camera`;

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      setIsConnected(true);
      setConnectionStatus("connected");
      console.log("WebSocket connected");
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      setIsStreaming(false);
      setConnectionStatus("disconnected");
      console.log("WebSocket disconnected");
    };

    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      setConnectionStatus("error");
    };
  };

  const handleWebSocketMessage = (data) => {
    updateLastUpdate();

    switch (data.type) {
      case "frame":
        if (videoFeedRef.current) {
          videoFeedRef.current.src = `data:image/jpeg;base64,${data.data}`;
        }
        if (data.detection) {
          setDetectionInfo(data.detection);
        }
        break;
      case "error":
        console.error("Server error:", data.message);
        alert(`Error del servidor: ${data.message}`);
        break;
      case "info":
        console.log("Server info:", data.message);
        break;
      default:
        console.log("Unknown message type:", data.type);
    }
  };

  const startStream = () => {
    if (ws.current && isConnected) {
      ws.current.send(
        JSON.stringify({
          action: "start_stream",
          camera_index: cameraIndex,
        })
      );
      setIsStreaming(true);
      setConnectionStatus("streaming");
    }
  };

  const stopStream = () => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify({ action: "stop_stream" }));
      setIsStreaming(false);
      setConnectionStatus("connected");
      // Clear video feed
      if (videoFeedRef.current) {
        videoFeedRef.current.src = "";
      }
    }
  };

  const disconnectWebSocket = () => {
    if (ws.current) {
      ws.current.close();
    }
  };

  const resetStatistics = async () => {
    try {
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
        }));
      }
    } catch (error) {
      console.error("Error resetting statistics:", error);
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
    if (!detectionInfo.detected) return "🔍 Buscando...";
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
        return "Error";
      default:
        return "Desconectado";
    }
  };

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <h1>🔍 Detección de Chalecos de Seguridad</h1>
          <p>Sistema de visión artificial para detección en tiempo real</p>
        </div>

        <div className={`connection-status ${connectionStatus}`}>
          {getConnectionStatusText()}
        </div>

        <div className="controls">
          <div className="control-group">
            <h3>Control de Cámara</h3>
            <button
              className={`btn btn-primary ${!isConnected ? "" : "disabled"}`}
              onClick={connectWebSocket}
              disabled={isConnected}
            >
              ▶️ Conectar
            </button>
            <button
              className={`btn btn-success ${
                isConnected && !isStreaming ? "" : "disabled"
              }`}
              onClick={startStream}
              disabled={!isConnected || isStreaming}
            >
              📹 Iniciar Detección
            </button>
            <button
              className={`btn btn-danger ${isStreaming ? "" : "disabled"}`}
              onClick={stopStream}
              disabled={!isStreaming}
            >
              ⏹️ Detener
            </button>
          </div>

          <div className="control-group">
            <h3>Configuración</h3>
            <select
              className="camera-select"
              value={cameraIndex}
              onChange={(e) => setCameraIndex(parseInt(e.target.value))}
              disabled={isStreaming}
            >
              <option value={0}>Cámara Predeterminada</option>
              <option value={1}>Cámara Externa 1</option>
              <option value={2}>Cámara Externa 2</option>
            </select>
            <button className="btn btn-warning" onClick={resetStatistics}>
              🔄 Reiniciar Estadísticas
            </button>
          </div>
        </div>

        <div className="main-content">
          <div className="video-container">
            <img
              ref={videoFeedRef}
              id="videoFeed"
              alt="Video Feed"
              style={{ display: isStreaming ? "block" : "none" }}
            />
            {!isStreaming && (
              <div className="placeholder-text">
                <h2>Presiona "Iniciar Detección" para comenzar</h2>
                <p>El video en tiempo real aparecerá aquí</p>
              </div>
            )}
          </div>

          <div className="info-panel">
            <div className="info-card">
              <h3>Estado de Detección</h3>
              <div className={`detection-status ${getDetectionStatusClass()}`}>
                {getDetectionDisplayText()}
              </div>
              <div className="status-item">
                <strong>Confianza:</strong>
                <span id="confidenceValue">
                  {detectionInfo.detected
                    ? `${(detectionInfo.confidence * 100).toFixed(1)}%`
                    : "--"}
                </span>
              </div>
              <div className="status-item">
                <strong>Modelo:</strong>
                <span>{message}</span>
              </div>
            </div>

            <div className="info-card">
              <h3>Estadísticas</h3>
              <div className="statistics">
                <div className="stat-item">
                  <div>Sin Chaleco</div>
                  <div className="stat-value">
                    {detectionInfo.statistics.sin_chaleco}
                  </div>
                </div>
                <div className="stat-item">
                  <div>Con Chaleco</div>
                  <div className="stat-value">
                    {detectionInfo.statistics.con_chaleco}
                  </div>
                </div>
              </div>
            </div>

            <div className="info-card">
              <h3>Información del Sistema</h3>
              <div className="status-item">
                <strong>Conectado:</strong>
                <span>{isConnected ? "Sí" : "No"}</span>
              </div>
              <div className="status-item">
                <strong>Transmitiendo:</strong>
                <span>{isStreaming ? "Sí" : "No"}</span>
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
