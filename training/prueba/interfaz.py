#!/usr/bin/env python3
"""
Interfaz gráfica para probar el modelo de detección de chalecos de seguridad
Permite usar la cámara en tiempo real para detectar si una persona lleva chaleco o no
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import os
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar YOLO
sys.path.append(str(Path(__file__).parent.parent))

try:
    from ultralytics import YOLO
except ImportError:
    messagebox.showerror("Error", "No se pudo importar ultralytics. Instala con: pip install ultralytics")
    sys.exit(1)

class ChalecoDetectionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Detección de Chalecos de Seguridad")
        self.root.geometry("900x700")
        self.root.configure(bg='#2c3e50')
        
        # Variables
        self.cap = None
        self.model = None
        self.is_running = False
        self.current_frame = None
        
        # Configurar la interfaz
        self.setup_ui()
        
        # Intentar cargar el modelo
        self.load_model()
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="🔍 Detección de Chalecos de Seguridad", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Frame de controles
        controls_frame = ttk.LabelFrame(main_frame, text="Controles", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Botones de control
        self.start_btn = ttk.Button(controls_frame, text="▶️ Iniciar Cámara", 
                                   command=self.start_camera, style='Accent.TButton')
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(controls_frame, text="⏹️ Detener Cámara", 
                                  command=self.stop_camera, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.capture_btn = ttk.Button(controls_frame, text="📸 Capturar Foto", 
                                     command=self.capture_photo, state='disabled')
        self.capture_btn.grid(row=0, column=2, padx=(0, 10))
        
        self.model_btn = ttk.Button(controls_frame, text="📁 Cargar Modelo", 
                                   command=self.load_model_dialog)
        self.model_btn.grid(row=0, column=3)
        
        # Frame de video
        video_frame = ttk.LabelFrame(main_frame, text="Vista de Cámara", padding="5")
        video_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        video_frame.columnconfigure(0, weight=1)
        video_frame.rowconfigure(0, weight=1)
        
        # Label para mostrar video
        self.video_label = ttk.Label(video_frame, text="Presiona 'Iniciar Cámara' para comenzar", 
                                    font=('Arial', 12), anchor='center')
        self.video_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame de información
        info_frame = ttk.LabelFrame(main_frame, text="Información de Detección", padding="10")
        info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Labels de información
        self.status_label = ttk.Label(info_frame, text="Estado: Modelo no cargado", 
                                     font=('Arial', 10, 'bold'))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.detection_label = ttk.Label(info_frame, text="Detección: Esperando...", 
                                        font=('Arial', 12, 'bold'), foreground='blue')
        self.detection_label.grid(row=1, column=0, sticky=tk.W)
        
        self.confidence_label = ttk.Label(info_frame, text="Confianza: --", 
                                         font=('Arial', 10))
        self.confidence_label.grid(row=2, column=0, sticky=tk.W)
        
        # Frame de estadísticas
        stats_frame = ttk.LabelFrame(main_frame, text="Estadísticas", padding="10")
        stats_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0), padx=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="Sin detecciones aún", 
                                    font=('Arial', 10))
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # Variables para estadísticas
        self.detection_count = {'sin_chaleco': 0, 'con_chaleco': 0}
        
    def load_model(self):
        """Carga el modelo entrenado"""
        try:
            # Buscar el modelo en diferentes ubicaciones posibles
            model_paths = [
                "modelo_entrenado/chaleco_detection/weights/best.pt",
                "../modelo_entrenado/chaleco_detection/weights/best.pt",
                "chaleco_detection/weights/best.pt"
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if model_path:
                self.model = YOLO(model_path)
                self.status_label.config(text=f"Estado: Modelo cargado ({os.path.basename(model_path)})", 
                                       foreground='green')
                messagebox.showinfo("Éxito", f"Modelo cargado correctamente desde:\n{model_path}")
            else:
                # Si no se encuentra, usar modelo pre-entrenado como fallback
                self.model = YOLO('yolov8n.pt')
                self.status_label.config(text="Estado: Usando modelo pre-entrenado (no específico para chalecos)", 
                                       foreground='orange')
                messagebox.showwarning("Advertencia", 
                                     "No se encontró el modelo entrenado para chalecos.\n"
                                     "Usando modelo pre-entrenado genérico.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el modelo:\n{str(e)}")
            self.status_label.config(text="Estado: Error al cargar modelo", foreground='red')
    
    def load_model_dialog(self):
        """Abre un diálogo para cargar un modelo personalizado"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar modelo YOLO",
            filetypes=[("PyTorch models", "*.pt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.model = YOLO(file_path)
                self.status_label.config(text=f"Estado: Modelo cargado ({os.path.basename(file_path)})", 
                                       foreground='green')
                messagebox.showinfo("Éxito", f"Modelo cargado correctamente desde:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar el modelo:\n{str(e)}")
    
    def start_camera(self):
        """Inicia la cámara y el proceso de detección"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Error", "No se pudo abrir la cámara")
                return
            
            self.is_running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.capture_btn.config(state='normal')
            
            # Iniciar hilo de detección
            self.detection_thread = threading.Thread(target=self.detection_loop)
            self.detection_thread.daemon = True
            self.detection_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar la cámara:\n{str(e)}")
    
    def stop_camera(self):
        """Detiene la cámara y el proceso de detección"""
        self.is_running = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.capture_btn.config(state='disabled')
        
        self.video_label.config(image='', text="Cámara detenida")
        self.detection_label.config(text="Detección: Detenida", foreground='gray')
        self.confidence_label.config(text="Confianza: --")
    
    def detection_loop(self):
        """Loop principal de detección"""
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Procesar frame si hay modelo cargado
            if self.model:
                try:
                    # Realizar detección
                    results = self.model(frame, verbose=False)
                    
                    # Dibujar resultados
                    annotated_frame = results[0].plot()
                    
                    # Obtener información de detección
                    if len(results[0].boxes) > 0:
                        box = results[0].boxes[0]
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        
                        # Obtener nombre de la clase
                        class_names = ['sin_chaleco', 'con_chaleco']
                        if hasattr(results[0], 'names'):
                            class_names = list(results[0].names.values())
                        
                        class_name = class_names[class_id] if class_id < len(class_names) else f"Clase {class_id}"
                        
                        # Actualizar estadísticas
                        if class_name in self.detection_count:
                            self.detection_count[class_name] += 1
                        
                        # Actualizar UI
                        self.root.after(0, lambda: self.update_detection_info(class_name, confidence))
                    else:
                        self.root.after(0, lambda: self.update_detection_info("Sin detección", 0.0))
                    
                    self.current_frame = annotated_frame
                    
                except Exception as e:
                    print(f"Error en detección: {e}")
                    self.current_frame = frame
            else:
                self.current_frame = frame
            
            # Actualizar imagen en la interfaz
            self.root.after(0, self.update_video_display)
    
    def update_detection_info(self, class_name, confidence):
        """Actualiza la información de detección en la UI"""
        self.detection_label.config(text=f"Detección: {class_name}")
        
        if confidence > 0:
            self.confidence_label.config(text=f"Confianza: {confidence:.2f}")
            
            # Cambiar color según la detección
            if "chaleco" in class_name.lower():
                color = 'green'
            elif "sin" in class_name.lower():
                color = 'red'
            else:
                color = 'blue'
            self.detection_label.config(foreground=color)
        else:
            self.confidence_label.config(text="Confianza: --")
            self.detection_label.config(foreground='gray')
        
        # Actualizar estadísticas
        stats_text = f"Sin chaleco: {self.detection_count['sin_chaleco']} | Con chaleco: {self.detection_count['con_chaleco']}"
        self.stats_label.config(text=stats_text)
    
    def update_video_display(self):
        """Actualiza la visualización del video"""
        if self.current_frame is not None:
            # Redimensionar frame para la interfaz
            height, width = self.current_frame.shape[:2]
            max_width = 800
            max_height = 600
            
            if width > max_width or height > max_height:
                scale = min(max_width/width, max_height/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                self.current_frame = cv2.resize(self.current_frame, (new_width, new_height))
            
            # Convertir BGR a RGB
            rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            
            # Convertir a PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            # Convertir a PhotoImage para tkinter
            photo = ImageTk.PhotoImage(pil_image)
            
            # Actualizar label
            self.video_label.config(image=photo, text='')
            self.video_label.image = photo  # Mantener referencia
    
    def capture_photo(self):
        """Captura una foto del frame actual"""
        if self.current_frame is not None:
            try:
                # Crear directorio de capturas si no existe
                captures_dir = "capturas"
                os.makedirs(captures_dir, exist_ok=True)
                
                # Generar nombre de archivo único
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{captures_dir}/captura_{timestamp}.jpg"
                
                # Guardar imagen
                cv2.imwrite(filename, self.current_frame)
                
                messagebox.showinfo("Éxito", f"Foto guardada en:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar la foto:\n{str(e)}")
        else:
            messagebox.showwarning("Advertencia", "No hay frame disponible para capturar")

def main():
    """Función principal"""
    root = tk.Tk()
    
    # Configurar estilo
    style = ttk.Style()
    style.theme_use('clam')
    
    # Crear la aplicación
    app = ChalecoDetectionGUI(root)
    
    # Configurar cierre de ventana
    def on_closing():
        if app.is_running:
            app.stop_camera()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Centrar ventana
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Iniciar la aplicación
    root.mainloop()

if __name__ == "__main__":
    main()
