// // import { useState } from "react";
// import reactLogo from "./assets/react.svg";
// import viteLogo from "/vite.svg";

// // import React, { useEffect, useState } from "react";
// import React, { useState, useEffect, useRef } from "react";
// import "./App.css";
// function App() {
//   const [message, setMessage] = useState("Loading...");
//   const [isConnected, setIsConnected] = useState(false);
//   const [isStreaming, setIsStreaming] = useState(false);
//   const [detectionInfo, setDetectionInfo] = useState({
//     class_name: "Esperando inicio...",
//     confidence: 0,
//     detected: false,
//     statistics: { sin_chaleco: 0, con_chaleco: 0 },
//   });
//   const [connectionStatus, setConnectionStatus] = useState("disconnected");
//   const [lastUpdate, setLastUpdate] = useState("--");
//   const [cameraIndex, setCameraIndex] = useState(0);

//   const videoFeedRef = useRef(null);
//   const ws = useRef(null);

//   // Check backend status on component mount
//   useEffect(() => {
//     fetch(`https://api.settinel.lat/api`)
//       .then((res) => res.json())
//       .then((data) => setMessage(data.message))
//       .catch((err) => setMessage("Error: " + err.message));
//   }, []);

//   const connectWebSocket = () => {
//     const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
//     const wsUrl = `${protocol}//api.settinel.lat/ws/camera`;
//     ws.current = new WebSocket(wsUrl);

//     ws.current.onopen = () => {
//       setIsConnected(true);
//       setConnectionStatus("connected");
//       console.log("WebSocket connected");
//     };

//     ws.current.onmessage = (event) => {
//       const data = JSON.parse(event.data);
//       handleWebSocketMessage(data);
//     };

//     ws.current.onclose = () => {
//       setIsConnected(false);
//       setIsStreaming(false);
//       setConnectionStatus("disconnected");
//       console.log("WebSocket disconnected");
//     };

//     ws.current.onerror = (error) => {
//       console.error("WebSocket error:", error);
//       setConnectionStatus("error");
//     };
//   };

//   const handleWebSocketMessage = (data) => {
//     updateLastUpdate();

//     switch (data.type) {
//       case "frame":
//         if (videoFeedRef.current) {
//           videoFeedRef.current.src = `data:image/jpeg;base64,${data.data}`;
//         }
//         if (data.detection) {
//           setDetectionInfo(data.detection);
//         }
//         break;
//       case "error":
//         console.error("Server error:", data.message);
//         alert(`Error del servidor: ${data.message}`);
//         break;
//       case "info":
//         console.log("Server info:", data.message);
//         break;
//       default:
//         console.log("Unknown message type:", data.type);
//     }
//   };

//   const startStream = () => {
//     if (ws.current && isConnected) {
//       ws.current.send(
//         JSON.stringify({
//           action: "start_stream",
//           camera_index: cameraIndex,
//         })
//       );
//       setIsStreaming(true);
//       setConnectionStatus("streaming");
//     }
//   };

//   const stopStream = () => {
//     if (ws.current && isConnected) {
//       ws.current.send(JSON.stringify({ action: "stop_stream" }));
//       setIsStreaming(false);
//       setConnectionStatus("connected");
//       // Clear video feed
//       if (videoFeedRef.current) {
//         videoFeedRef.current.src = "";
//       }
//     }
//   };

//   const disconnectWebSocket = () => {
//     if (ws.current) {
//       ws.current.close();
//     }
//   };

//   const resetStatistics = async () => {
//     try {
//       const response = await fetch(
//         "https://api.settinel.lat/api/reset_statistics",
//         {
//           method: "POST",
//         }
//       );
//       if (response.ok) {
//         setDetectionInfo((prev) => ({
//           ...prev,
//           statistics: { sin_chaleco: 0, con_chaleco: 0 },
//         }));
//       }
//     } catch (error) {
//       console.error("Error resetting statistics:", error);
//     }
//   };

//   const updateLastUpdate = () => {
//     const now = new Date();
//     setLastUpdate(now.toLocaleTimeString());
//   };

//   const getDetectionStatusClass = () => {
//     if (!detectionInfo.detected) return "detection-neutral";
//     if (detectionInfo.class_name.includes("con_chaleco"))
//       return "detection-safe";
//     if (detectionInfo.class_name.includes("sin_chaleco"))
//       return "detection-danger";
//     return "detection-neutral";
//   };

//   const getDetectionDisplayText = () => {
//     if (!detectionInfo.detected) return "🔍 Buscando...";
//     if (detectionInfo.class_name.includes("con_chaleco"))
//       return "✅ Con Chaleco";
//     if (detectionInfo.class_name.includes("sin_chaleco"))
//       return "❌ Sin Chaleco";
//     return detectionInfo.class_name;
//   };

//   const getConnectionStatusText = () => {
//     switch (connectionStatus) {
//       case "connected":
//         return "Conectado";
//       case "streaming":
//         return "Transmitiendo";
//       case "error":
//         return "Error";
//       default:
//         return "Desconectado";
//     }
//   };

//   return (
//     <div className="app">
//       <div className="container">
//         <div className="header">
//           <h1>🔍 Detección de Chalecos de Seguridad</h1>
//           <p>Sistema de visión artificial para detección en tiempo real</p>
//         </div>

//         <div className={`connection-status ${connectionStatus}`}>
//           {getConnectionStatusText()}
//         </div>

//         <div className="controls">
//           <div className="control-group">
//             <h3>Control de Cámara</h3>
//             <button
//               className={`btn btn-primary ${!isConnected ? "" : "disabled"}`}
//               onClick={connectWebSocket}
//               disabled={isConnected}
//             >
//               ▶️ Conectar
//             </button>
//             <button
//               className={`btn btn-success ${
//                 isConnected && !isStreaming ? "" : "disabled"
//               }`}
//               onClick={startStream}
//               disabled={!isConnected || isStreaming}
//             >
//               📹 Iniciar Detección
//             </button>
//             <button
//               className={`btn btn-danger ${isStreaming ? "" : "disabled"}`}
//               onClick={stopStream}
//               disabled={!isStreaming}
//             >
//               ⏹️ Detener
//             </button>
//           </div>

//           <div className="control-group">
//             <h3>Configuración</h3>
//             <select
//               className="camera-select"
//               value={cameraIndex}
//               onChange={(e) => setCameraIndex(parseInt(e.target.value))}
//               disabled={isStreaming}
//             >
//               <option value={0}>Cámara Predeterminada</option>
//               <option value={1}>Cámara Externa 1</option>
//               <option value={2}>Cámara Externa 2</option>
//             </select>
//             <button className="btn btn-warning" onClick={resetStatistics}>
//               🔄 Reiniciar Estadísticas
//             </button>
//           </div>
//         </div>

//         <div className="main-content">
//           <div className="video-container">
//             <img
//               ref={videoFeedRef}
//               id="videoFeed"
//               alt="Video Feed"
//               style={{ display: isStreaming ? "block" : "none" }}
//             />
//             {!isStreaming && (
//               <div className="placeholder-text">
//                 <h2>Presiona "Iniciar Detección" para comenzar</h2>
//                 <p>El video en tiempo real aparecerá aquí</p>
//               </div>
//             )}
//           </div>

//           <div className="info-panel">
//             <div className="info-card">
//               <h3>Estado de Detección</h3>
//               <div className={`detection-status ${getDetectionStatusClass()}`}>
//                 {getDetectionDisplayText()}
//               </div>
//               <div className="status-item">
//                 <strong>Confianza:</strong>
//                 <span id="confidenceValue">
//                   {detectionInfo.detected
//                     ? `${(detectionInfo.confidence * 100).toFixed(1)}%`
//                     : "--"}
//                 </span>
//               </div>
//               <div className="status-item">
//                 <strong>Modelo:</strong>
//                 <span>{message}</span>
//               </div>
//             </div>

//             <div className="info-card">
//               <h3>Estadísticas</h3>
//               <div className="statistics">
//                 <div className="stat-item">
//                   <div>Sin Chaleco</div>
//                   <div className="stat-value">
//                     {detectionInfo.statistics.sin_chaleco}
//                   </div>
//                 </div>
//                 <div className="stat-item">
//                   <div>Con Chaleco</div>
//                   <div className="stat-value">
//                     {detectionInfo.statistics.con_chaleco}
//                   </div>
//                 </div>
//               </div>
//             </div>

//             <div className="info-card">
//               <h3>Información del Sistema</h3>
//               <div className="status-item">
//                 <strong>Conectado:</strong>
//                 <span>{isConnected ? "Sí" : "No"}</span>
//               </div>
//               <div className="status-item">
//                 <strong>Transmitiendo:</strong>
//                 <span>{isStreaming ? "Sí" : "No"}</span>
//               </div>
//               <div className="status-item">
//                 <strong>Última Actualización:</strong>
//                 <span>{lastUpdate}</span>
//               </div>
//             </div>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default App;

// App.js - Versión actualizada para cámara cliente
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

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const ws = useRef(null);
  const streamRef = useRef(null);
  const animationRef = useRef(null);

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
      stopCamera();
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
      case "detection_result":
        if (data.detection) {
          setDetectionInfo(data.detection);
          // Actualizar estadísticas globales si vienen en la respuesta
          if (data.detection.statistics) {
            setDetectionInfo((prev) => ({
              ...prev,
              statistics: data.detection.statistics,
            }));
          }
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

  // Iniciar cámara del usuario
  const startCamera = async () => {
    try {
      console.log("Solicitando acceso a cámara...");

      // Opciones para la cámara
      const constraints = {
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 30 },
        },
        audio: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        console.log("Cámara iniciada correctamente");
      }

      return true;
    } catch (error) {
      console.error("Error accediendo a la cámara:", error);
      alert(`No se pudo acceder a la cámara: ${error.message}`);
      return false;
    }
  };

  // Detener cámara
  const stopCamera = () => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  // Capturar y enviar frames
  const captureAndSendFrame = () => {
    if (
      !videoRef.current ||
      !ws.current ||
      ws.current.readyState !== WebSocket.OPEN
    ) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    // Configurar canvas con las dimensiones del video
    if (video.videoWidth > 0 && video.videoHeight > 0) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Dibujar frame actual en canvas
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convertir a JPEG (calidad reducida para mejor performance)
      const imageData = canvas.toDataURL("image/jpeg", 0.7);
      const base64Data = imageData.split(",")[1]; // Remover header data:image/jpeg;base64,

      // Enviar frame al servidor
      ws.current.send(
        JSON.stringify({
          action: "process_frame",
          frame_data: base64Data,
          timestamp: Date.now(),
        })
      );
    }

    // Continuar capturando frames
    if (isStreaming) {
      animationRef.current = requestAnimationFrame(captureAndSendFrame);
    }
  };

  const startStream = async () => {
    if (!isConnected) {
      alert("Primero debes conectar el WebSocket");
      return;
    }

    // Iniciar cámara
    const cameraStarted = await startCamera();
    if (!cameraStarted) {
      return;
    }

    // Esperar a que el video esté listo
    if (videoRef.current) {
      videoRef.current.onloadeddata = () => {
        setIsStreaming(true);
        setConnectionStatus("streaming");

        // Configurar canvas
        if (canvasRef.current) {
          canvasRef.current.width = videoRef.current.videoWidth;
          canvasRef.current.height = videoRef.current.videoHeight;
        }

        // Iniciar captura de frames
        captureAndSendFrame();
      };
    }
  };

  const stopStream = () => {
    setIsStreaming(false);
    setConnectionStatus("connected");
    stopCamera();

    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify({ action: "stop_stream" }));
    }
  };

  const disconnectWebSocket = () => {
    stopStream();
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
          <p>Usa tu cámara web para detección en tiempo real</p>
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
            <button className="btn btn-warning" onClick={resetStatistics}>
              🔄 Reiniciar Estadísticas
            </button>
          </div>
        </div>

        <div className="main-content">
          <div className="video-container">
            {/* Video en vivo de la cámara del usuario */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={{
                display: isStreaming ? "block" : "none",
                width: "100%",
                maxWidth: "640px",
                border: "2px solid #333",
                borderRadius: "8px",
              }}
            />

            {/* Canvas oculto para procesamiento */}
            <canvas ref={canvasRef} style={{ display: "none" }} />

            {!isStreaming && (
              <div className="placeholder-text">
                <h2>Presiona "Iniciar Detección" para comenzar</h2>
                <p>Se solicitará acceso a tu cámara web</p>
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
                <span>
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
