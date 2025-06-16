import cv2
import numpy as np
from picamera2 import Picamera2
import time
import pickle
import tflite_runtime.interpreter as tflite
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import random
import threading
from collections import deque
import queue
import os
import math
from sklearn.preprocessing import LabelEncoder
import warnings
from typing import Dict, Optional, Callable
import serial
from flask import Flask, render_template_string, jsonify
import requests

# Suppress NumPy warnings about subnormal values
warnings.filterwarnings("ignore", category=UserWarning, module="numpy.core.getlimits")

# === Configuration ===
class Config:
    # Chemins
    MODEL_PATH = "/home/bingo/Desktop/poubelle/waste_classifier8.tflite"
    LABELS_PATH = "label_encoder(6).pkl"
    
    # Paramètres de détection optimisés
    INPUT_SHAPE = (224, 224)  # (hauteur, largeur)
    MIN_AREA = 1500   
    MAX_AREA = 150000 
    STABILIZATION_TIME = 3.0   # 3 secondes de stabilisation
    CONFIDENCE_THRESHOLD = 40  
    
    # Nouveaux paramètres pour la stabilisation
    MIN_DETECTION_FRAMES = 10  # Minimum de frames consécutives nécessaires
    STABLE_CONFIDENCE_THRESHOLD = 40  # Confiance minimum pour considérer stable
    
    # Paramètres de prétraitement avancés
    BLUR_KERNEL = (5, 5)  
    CANNY_LOW = 30  
    CANNY_HIGH = 100  
    MORPH_KERNEL_SIZE = 3  
    
    # Paramètres interface adaptés pour écran DSI Raspberry Pi
    RESULT_DISPLAY_TIME = 2  
    CAMERA_WIDTH = 480  # Réduit pour écran DSI
    CAMERA_HEIGHT = 320  # Réduit pour écran DSI
    
    # Dimensions interface adaptées pour écran DSI (800x480)
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 480
    FONT_SIZE_LARGE = 14  # Réduit
    FONT_SIZE_MEDIUM = 10  # Réduit
    FONT_SIZE_SMALL = 8   # Réduit
    EMOJI_SIZE = 24       # Réduit
    
    # Palette moderne avec dégradés
    COLORS = {
        "primary": "#6366F1",
        "primary_dark": "#4F46E5",
        "secondary": "#10B981",
        "secondary_dark": "#059669",
        "accent": "#F59E0B",
        "accent_dark": "#D97706",
        "background": "#F8FAFC",
        "surface": "#FFFFFF",
        "surface_dark": "#F1F5F9",
        "card": "#FFFFFF",
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "text_muted": "#94A3B8",
        "success": "#10B981",
        "error": "#EF4444",
        "warning": "#F59E0B",
        "info": "#3B82F6",
        "shadow": "#000000",
        "border": "#E2E8F0",
        "hover": "#F1F5F9",
        "warning_zone": "#ffcccb",
        "interactive_highlight": "#e0f0ff"
    }


class ArduinoController:
    def __init__(self, port="/dev/ttyUSB0", baud_rate=115200):
        self.serial_port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.connected = False
        self.current_data = {
            "niveau_bac1": 0, 
            "niveau_bac2": 0, 
            "niveau_bac3": 0, 
            "niveau_bac4": 0, 
            "niveau_bac5": 0
        }
        self.history_data = []
        
        # Configuration Ubidots
        self.UBIDOTS_TOKEN = "TON_TOKEN_ICI"
        self.DEVICE_NAME = "BinGo"
        
    def connect(self):
        """Établir la connexion série avec l'Arduino"""
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=2)
            time.sleep(3)  # Attendre que l'Arduino se réinitialise
            self.connected = True
            print(f"✅ Connexion Arduino établie sur {self.serial_port} à {self.baud_rate} bauds")
            return True
        except serial.SerialException as e:
            print(f"❌ Erreur connexion Arduino: {e}")
            self.connected = False
            return False
    
    def send_command(self, command):
        """Envoyer une commande à l'Arduino"""
        if not self.connected or not self.ser:
            print("❌ Arduino non connecté")
            return False
        
        try:
            command_with_newline = command + '\n'
            self.ser.write(command_with_newline.encode('utf-8'))
            print(f"📤 Commande envoyée: {command}")
            return True
        except Exception as e:
            print(f"❌ Erreur envoi commande: {e}")
            return False
    
    def read_arduino_data(self):
        """Lire les données de l'Arduino"""
        if not self.connected or not self.ser:
            return None
        
        try:
            if self.ser.in_waiting > 0:
                ligne = self.ser.readline().decode('utf-8').strip()
                print(f"📥 Arduino: {ligne}")
                
                # Parser les données des capteurs
                if ligne.startswith("forSite"):
                    return self.parse_sensor_data(ligne)
                
                return ligne
        except Exception as e:
            print(f"❌ Erreur lecture Arduino: {e}")
            return None
    
    def parse_sensor_data(self, ligne):
        """Parser les données des capteurs de distance"""
        try:
            # Enlève le préfixe "forSite" et parse les valeurs
            valeurs_str = ligne.replace("forSite", "").strip()
            valeurs = [float(val) for val in valeurs_str.split(",")]
            
            if len(valeurs) == 5:
                data = {
                    "niveau_bac1": round(valeurs[0], 0),
                    "niveau_bac2": round(valeurs[1], 0),
                    "niveau_bac3": round(valeurs[2], 0),
                    "niveau_bac4": round(valeurs[3], 0),
                    "niveau_bac5": round(valeurs[4], 0),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Mettre à jour les données actuelles
                self.current_data = data
                self.history_data.append(data)
                
                # Garder seulement les 50 dernières valeurs
                if len(self.history_data) > 50:
                    self.history_data.pop(0)
                
                # Envoyer à Ubidots
                self.send_to_ubidots(data)
                
                return data
        except ValueError as e:
            print(f"❌ Erreur parsing données capteurs: {e}")
        return None
    
    def send_to_ubidots(self, data):
        """Envoyer les données à Ubidots"""
        try:
            url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{self.DEVICE_NAME}/"
            headers = {
                "X-Auth-Token": self.UBIDOTS_TOKEN, 
                "Content-Type": "application/json"
            }
            response = requests.post(url, json=data, headers=headers)
            print(f"📊 Ubidots: {response.status_code} - {data}")
        except Exception as e:
            print(f"❌ Erreur Ubidots: {e}")
    
    def start_monitoring(self):
        """Démarrer la surveillance en arrière-plan"""
        def monitor_loop():
            while self.connected:
                self.read_arduino_data()
                time.sleep(0.1)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        print("🔄 Surveillance Arduino démarrée")
    
    def disconnect(self):
        """Fermer la connexion série"""
        if self.ser:
            self.ser.close()
            self.connected = False
            print("🔌 Arduino déconnecté")


# === Système de détection ===
class DetectionSystem:
    def __init__(self, comm_system):
        self.comm = comm_system
        self.interpreter = None
        self.label_encoder = None
        self.cap = None  # Caméra USB
        self.running = False
        self.thread = None
        self.camera_window = None
        self.camera_label = None
        self.detector = AdvancedObjectDetector()

    def initialize(self):
        try:
            # === NETTOYAGE COMPLET ===
            if hasattr(self, 'cap') and self.cap:
                try:
                    self.cap.release()
                except:
                    pass
                self.cap = None
            
            time.sleep(2)
            
            # === CAMÉRA USB AVEC DÉTECTION INTELLIGENTE ===
            os.environ['OPENCV_VIDEOIO_PRIORITY_V4L2'] = '1'
            
            print("🔍 Recherche intelligente de caméra USB...")
            
            camera_candidates = [2, 3, 0, 1]  # Commencer par /dev/video2
            for camera_id in camera_candidates:
                try:
                    print(f"   Test /dev/video{camera_id}...")
                    cap = cv2.VideoCapture(camera_id, cv2.CAP_V4L2)
                    if cap.isOpened():
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
                        cap.set(cv2.CAP_PROP_FPS, 15)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        success_count = 0
                        for _ in range(3):
                            ret, test_frame = cap.read()
                            if ret and test_frame is not None and test_frame.size > 0:
                                success_count += 1
                            time.sleep(0.1)
                        
                        if success_count >= 2:
                            self.cap = cap
                            print(f"✅ Caméra USB trouvée sur /dev/video{camera_id}")
                            print(f"   Format: {test_frame.shape}")
                            break
                        else:
                            cap.release()
                    else:
                        cap.release()
                except Exception as e:
                    print(f"   Erreur /dev/video{camera_id}: {e}")
                    continue
            
            if not hasattr(self, 'cap') or not self.cap:
                raise Exception("❌ Aucune caméra USB fonctionnelle trouvée")
            
            # === CHARGEMENT DU MODÈLE ===
            if os.path.exists(Config.MODEL_PATH):
                self.interpreter = tflite.Interpreter(model_path=Config.MODEL_PATH)
                self.interpreter.allocate_tensors()
                print("Input details:",self.interpreter.get_input_details())
            else:
                raise FileNotFoundError(f"Modèle non trouvé: {Config.MODEL_PATH}")
            
            # === CHARGEMENT DES LABELS ===
            if os.path.exists(Config.LABELS_PATH):
                with open(Config.LABELS_PATH, "rb") as f:
                    self.label_encoder = pickle.load(f)
                    print(f"✅ Label encoder chargé: {len(self.label_encoder.classes_)} classes")
                    print(f"Classes disponibles: {list(self.label_encoder.classes_)}")
            else:
                default_labels = ["cardboard_paper", "plastic", "metal", "glass", "trash"]
                self.label_encoder = LabelEncoder()
                self.label_encoder.fit(default_labels)
                print(f"Fichier labels non trouvé, utilisation des labels par défaut")
            
            return True
        except Exception as e:
            print(f"Erreur initialisation détection: {str(e)}")
            if hasattr(self, 'cap') and self.cap:
                self.cap.release()
                self.cap = None
            return False

    def create_camera_window(self, root):
        """Créer la fenêtre de la caméra"""
        try:
            self.camera_window = tk.Toplevel(root)
            self.camera_window.title("🎥 Vue Caméra - BinGo")
            self.camera_window.geometry(f"{Config.CAMERA_WIDTH + 20}x{Config.CAMERA_HEIGHT + 60}")
            self.camera_window.configure(bg=Config.COLORS["surface"])
            self.camera_label = tk.Label(self.camera_window, bg=Config.COLORS["surface"])
            self.camera_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            print("✅ Fenêtre caméra créée")
        except Exception as e:
            print(f"Erreur création fenêtre caméra: {e}")

    def close_camera_window(self):
        """Fermer la fenêtre de la caméra"""
        try:
            if hasattr(self, 'camera_window') and self.camera_window:
                self.camera_window.destroy()
                self.camera_window = None
                self.camera_label = None
                print("✅ Fenêtre caméra fermée")
        except Exception as e:
            print(f"Erreur fermeture fenêtre caméra: {e}")

    def update_camera_display(self, frame):
        """Mettre à jour l'affichage de la caméra"""
        try:
            if self.camera_window and self.camera_label:
                if not self.camera_window.winfo_exists():
                    self.camera_window = None
                    self.camera_label = None
                    return
                display_frame = cv2.resize(frame, (Config.CAMERA_WIDTH, Config.CAMERA_HEIGHT))
                img = Image.fromarray(display_frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.camera_label.configure(image=imgtk)
                self.camera_label.image = imgtk
                self.camera_window.update_idletasks()
        except tk.TclError:
            self.camera_window = None
            self.camera_label = None
        except Exception as e:
            print(f"Erreur mise à jour caméra: {e}")

    def draw_detection_box(self, frame, box, label, confidence):
        """Dessiner la boîte de détection sur le frame"""
        try:
            if box is not None:
                color = (0, 255, 0) if confidence >= 80 else (255, 255, 0) if confidence >= 60 else (255, 165, 0)
                cv2.polylines(frame, [box.astype(int)], True, color, 2)
                text = f"{label}: {confidence:.1f}%"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2
                text_x = int(box[0][0])
                text_y = int(box[0][1] - 10) if int(box[0][1] - 10) > 10 else int(box[2][1] + 25)
                (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
                cv2.rectangle(frame, (text_x - 3, text_y - text_h - 3), (text_x + text_w + 3, text_y + 3), (0, 0, 0), -1)
                cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness)
        except Exception as e:
            print(f"Erreur dessin boîte: {e}")

    def predict_roi(self, roi, input_details, output_details):
        """Prédire la classe de la ROI"""
        try:
            resized = cv2.resize(roi, Config.INPUT_SHAPE)
            input_data = resized.astype(np.float32)
            input_data = input_data / 127.5 - 1.0
            input_data = np.expand_dims(input_data, axis=0)
            self.interpreter.set_tensor(input_details[0]['index'], input_data)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(output_details[0]['index'])[0]
            pred_index = int(np.argmax(output_data))
            confidence = float(np.max(output_data)) * 100
            try:
                if hasattr(self, 'label_encoder') and 0 <= pred_index < len(self.label_encoder.classes_):
                    label = self.label_encoder.inverse_transform([pred_index])[0]
                else:
                    label = "trash"
            except (ValueError, IndexError, AttributeError):
                label = "trash"
            return confidence, label
        except Exception as e:
            print(f"Erreur prédiction: {e}")
            return 0, "trash"

    def start(self, root=None):
        """Démarrer le système de détection"""
        if self.initialize():
            if root:
                self.create_camera_window(root)
            self.running = True
            self.thread = threading.Thread(target=self.run_detection, daemon=True)
            self.thread.start()

    def run_detection(self):
        """Boucle principale de détection"""
        if not self.interpreter:
            print("Modèle non initialisé")
            return
        
        input_details = self.interpreter.get_input_details()
        output_details = self.interpreter.get_output_details()
        consecutive_errors = 0
        max_consecutive_errors = 5

        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    consecutive_errors += 1
                    print(f"⚠️ Erreur capture USB #{consecutive_errors}")
                    if consecutive_errors >= max_consecutive_errors:
                        print("❌ Trop d'erreurs de capture USB")
                        break
                    time.sleep(0.1)
                    continue
                consecutive_errors = 0
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                display_frame = frame_rgb.copy()
                
                if self.comm.is_blocked_for_display():
                    self.update_camera_display(display_frame)
                    time.sleep(0.1)
                    continue
                
                roi, box, x_offset, y_offset = self.detector.detect_objects_multi_method(frame_rgb)
                if box is not None:
                    confidence, label = self.predict_roi(roi, input_details, output_details)
                    if confidence >= Config.CONFIDENCE_THRESHOLD:
                        self.draw_detection_box(display_frame, box, label, confidence)
                        self.comm.add_detection(label, confidence, has_object=True)
                        print(f"Détecté: {label} ({confidence:.1f}%)")
                    else:
                        self.comm.add_detection("", confidence, has_object=True)
                else:
                    self.comm.add_detection("", 0, has_object=False)
                self.update_camera_display(display_frame)
                time.sleep(0.05)
        except Exception as e:
            print(f"Erreur dans la boucle de détection: {str(e)}")
            self.running = False
        finally:
            if hasattr(self, 'cap') and self.cap:
                self.cap.release()

    def stop(self):
        """Arrêter le système de détection"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
            self.cap = None
        self.close_camera_window()

# === Système de détection optimisé ===
class AdvancedObjectDetector:
    def __init__(self):
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (Config.MORPH_KERNEL_SIZE, Config.MORPH_KERNEL_SIZE))
        self.frame_count = 0
        self.stable_contours = []

    def detect_objects_multi_method(self, frame):
        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        blur = cv2.GaussianBlur(enhanced, (5, 5), 0)
        edges = cv2.Canny(blur, 30, 100)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        valid_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if Config.MIN_AREA <= area <= Config.MAX_AREA:
                x, y, w, h = cv2.boundingRect(cnt)
                if (x > 10 and y > 10 and x + w < width - 10 and y + h < height - 10):
                    valid_contours.append(cnt)
        
        if valid_contours:
            biggest_contour = max(valid_contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(biggest_contour)
            margin = 20
            x1 = max(0, x - margin)
            y1 = max(0, y - margin)
            x2 = min(width, x + w + margin)
            y2 = min(height, y + h + margin)
            roi = frame[y1:y2, x1:x2]
            box = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
            return roi, box, x1, y1
        return frame, None, 0, 0

# === Système de communication ===
class CommunicationSystem:
    def __init__(self):
        self.detection_queue = queue.Queue()
        self.interface_queue = queue.Queue()
        self.detection_history = deque(maxlen=20)
        self.stable_detection = None
        self.stable_since = None
        self.last_object_time = None
        self.no_object_timeout = 2.5
        self.confidence_history = deque(maxlen=10)
        self.current_stable_label = None
        self.stability_start_time = None
        self.consecutive_detections = 0
        self.is_analyzing = False
        self.is_displaying_result = False
        self.display_start_time = None
        self.display_duration = 2.0

    def add_detection(self, label, confidence, has_object=True, image_data=None):
        timestamp = time.time()
        if self.is_displaying_result:
            elapsed_display = timestamp - self.display_start_time
            if elapsed_display < self.display_duration:
                return
            else:
                self.stop_displaying_result()
        
        if has_object and confidence >= Config.STABLE_CONFIDENCE_THRESHOLD:
            self.last_object_time = timestamp
            if (self.current_stable_label == label and self.stability_start_time is not None):
                elapsed_time = timestamp - self.stability_start_time
                self.consecutive_detections += 1
                self.detection_history.append((label, confidence, timestamp))
                self.confidence_history.append(confidence)
                print(f"🔄 Stabilisation en cours: {label} ({elapsed_time:.1f}s/3.0s)")
                if elapsed_time >= Config.STABILIZATION_TIME and not self.is_analyzing:
                    avg_confidence = sum(self.confidence_history) / len(self.confidence_history)
                    if avg_confidence >= Config.CONFIDENCE_THRESHOLD:
                        self.is_analyzing = True
                        print(f"✅ Objet stable détecté après 3s: {label} ({avg_confidence:.1f}%)")
                        self.start_displaying_result()
                        self.detection_queue.put(("validation", label, avg_confidence, image_data))
                        self.reset_stability_tracking()
            elif (self.current_stable_label != label or self.stability_start_time is None):
                print(f"🔍 Nouveau/Changement d'objet détecté: {label}")
                self.start_stability_tracking(label, timestamp)
        else:
            if has_object:
                print(f"⚠️ Confiance trop faible: {confidence:.1f}%")
            if (not self.is_displaying_result and self.last_object_time and 
                (timestamp - self.last_object_time > self.no_object_timeout)):
                if not self.detection_queue.empty():
                    return
                print("📭 Aucun objet stable détecté")
                self.detection_queue.put(("NO_OBJECT", 0))
                self.reset_stability_tracking()
                self.last_object_time = None

    def start_displaying_result(self):
        """Démarre l'affichage bloquant du résultat"""
        self.is_displaying_result = True
        self.display_start_time = time.time()
        print("🚫 BLOCAGE : Affichage du résultat pendant 2 secondes")

    def stop_displaying_result(self):
        """Arrête l'affichage bloquant"""
        self.is_displaying_result = False
        self.display_start_time = None
        print("✅ DÉBLOCAGE : Prêt pour nouvelle détection")

    def is_blocked_for_display(self):
        """Vérifie si le système est bloqué pour affichage"""
        if not self.is_displaying_result:
            return False
        elapsed = time.time() - self.display_start_time
        if elapsed >= self.display_duration:
            self.stop_displaying_result()
            return False
        return True

    def start_stability_tracking(self, label, timestamp):
        """Démarre le suivi de stabilité pour un nouvel objet"""
        self.current_stable_label = label
        self.stability_start_time = timestamp
        self.consecutive_detections = 1
        self.is_analyzing = False
        self.detection_history.clear()
        self.confidence_history.clear()
        print(f"🎯 Début de stabilisation pour: {label}")

    def reset_stability_tracking(self):
        """Reset tous les paramètres de stabilité"""
        self.current_stable_label = None
        self.stability_start_time = None
        self.consecutive_detections = 0
        self.is_analyzing = False
        self.detection_history.clear()
        self.confidence_history.clear()

    def get_stability_progress(self):
        if self.stability_start_time is None:
            return 0.0, None
        elapsed = time.time() - self.stability_start_time
        progress = min(elapsed / Config.STABILIZATION_TIME, 1.0)
        return progress, self.current_stable_label

# === Interface utilisateur ===
class ModernUI:
    @staticmethod
    def create_card(parent, title="", content_frame_config=None):
        if content_frame_config is None:
            content_frame_config = {}
        shadow_frame = tk.Frame(parent, bg=Config.COLORS["shadow"], padx=1, pady=1)
        card_frame = tk.Frame(shadow_frame, bg=Config.COLORS["card"], padx=10, pady=8, relief="flat")
        card_frame.pack(fill="both", expand=True)
        if title:
            title_label = tk.Label(card_frame, text=title, font=("Segoe UI", Config.FONT_SIZE_MEDIUM, "bold"),
                                   bg=Config.COLORS["card"], fg=Config.COLORS["primary"])
            title_label.pack(anchor="w", pady=(0, 5))
        content_frame = tk.Frame(card_frame, bg=Config.COLORS["card"], **content_frame_config)
        content_frame.pack(fill="both", expand=True)
        return shadow_frame, content_frame

    @staticmethod
    def create_modern_button(parent, text, command, style="primary"):
        colors = {
            "primary": (Config.COLORS["primary"], Config.COLORS["primary_dark"]),
            "secondary": (Config.COLORS["secondary"], Config.COLORS["secondary_dark"]),
            "accent": (Config.COLORS["accent"], Config.COLORS["accent_dark"])
        }
        bg_color, hover_color = colors.get(style, colors["primary"])
        btn = tk.Button(parent, text=text, command=command, font=("Segoe UI", Config.FONT_SIZE_SMALL, "bold"),
                        bg=bg_color, fg="white", relief="flat", padx=10, pady=4, cursor="hand2")
        
        def on_enter(e):
            btn.config(bg=hover_color)
        def on_leave(e):
            btn.config(bg=bg_color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

# === Application principale ===
class MainApplication(tk.Tk):
    def __init__(self, comm_system, detection_system):
        super().__init__()
        self.comm = comm_system
        self.detection = detection_system
        self.title("🗂️ BinGo - Poubelle Intelligente")
        self.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        self.configure(bg=Config.COLORS["background"])
        self.resizable(False, False)
        self.attributes('-fullscreen', True)
        self.current_result = None
        self.result_timer = None
        self.stats = {"total": 0, "papier": 0, "plastique": 0, "metal": 0, "verre": 0, "non_recyclable": 0}
        self.create_interface()
        self.start_systems()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_interface(self):
        main_container = tk.Frame(self, bg=Config.COLORS["background"], padx=15, pady=10)
        main_container.pack(fill="both", expand=True)
        self.create_header(main_container)
        content_frame = tk.Frame(main_container, bg=Config.COLORS["background"])
        content_frame.pack(fill="both", expand=True, pady=(10, 0))
        content_frame.grid_columnconfigure(0, weight=3)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=0)
        self.create_detection_panel(content_frame)
        self.create_stats_panel(content_frame)
        self.create_forbidden_objects_panel(content_frame)
        self.create_status_bar(main_container)

    def create_forbidden_objects_panel(self, parent):
        forbidden_container = tk.Frame(parent, bg=Config.COLORS["background"])
        forbidden_container.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        
        # CRÉER LA CARTE AVEC TITRE PERSONNALISÉ
        shadow_frame = tk.Frame(forbidden_container, bg=Config.COLORS["shadow"], padx=1, pady=1)
        shadow_frame.pack(fill="x")
        
        card_frame = tk.Frame(shadow_frame, bg=Config.COLORS["card"], padx=10, pady=8, relief="flat")
        card_frame.pack(fill="both", expand=True)
        
        # TITRE AVEC ICÔNE PERSONNALISÉE
        title_frame = tk.Frame(card_frame, bg=Config.COLORS["card"])
        title_frame.pack(anchor="w", pady=(0, 5))
        
        try:
            # Charger l'icône interdit
            interdit_icon_path = "/home/bingo/Desktop/poubelle/icons/interdit.png"
            interdit_image = Image.open(interdit_icon_path).resize((18, 18), Image.Resampling.LANCZOS)
            interdit_tk = ImageTk.PhotoImage(interdit_image)
            
            # Stocker la référence pour éviter le garbage collection
            if not hasattr(self, 'interdit_icon_ref'):
                self.interdit_icon_ref = interdit_tk
            
            tk.Label(title_frame, image=interdit_tk, bg=Config.COLORS["card"]).pack(side="left", padx=(0, 8))
            
        except Exception as e:
            print(f"Erreur chargement icône interdit: {e}")
            # Fallback emoji
            tk.Label(title_frame, text="🚫", font=("Segoe UI Emoji", 16), bg=Config.COLORS["card"]).pack(side="left", padx=(0, 8))
        
        tk.Label(title_frame, text="Objets Interdits", 
                 font=("Segoe UI", Config.FONT_SIZE_MEDIUM, "bold"),
                 bg=Config.COLORS["card"], fg=Config.COLORS["primary"]).pack(side="left")
        
        # CONTENU DE LA CARTE
        forbidden_content = tk.Frame(card_frame, bg=Config.COLORS["card"])
        forbidden_content.pack(fill="both", expand=True)
        
        content_frame = tk.Frame(forbidden_content, bg=Config.COLORS["card"])
        content_frame.pack(fill="x", padx=5, pady=5)
        
        # OBJETS INTERDITS AVEC IMAGES PERSONNALISÉES
        forbidden_items = [
            ("/home/bingo/Desktop/poubelle/icons/medoc.jpg", "Médicaments"),
            ("/home/bingo/Desktop/poubelle/icons/pile.png", "Piles"),
            ("/home/bingo/Desktop/poubelle/icons/ampoule.png", "Ampoules"),
            ("/home/bingo/Desktop/poubelle/icons/fiole.jpg", "Produits chimiques")
        ]
        
        items_frame = tk.Frame(content_frame, bg=Config.COLORS["card"])
        items_frame.pack(fill="x", pady=(0, 5))
        
        # Stocker les références d'images pour éviter le garbage collection
        if not hasattr(self, 'forbidden_icon_refs'):
            self.forbidden_icon_refs = []
        
        for icon_path, item_name in forbidden_items:
            item_frame = tk.Frame(items_frame, bg=Config.COLORS["card"])
            item_frame.pack(side="left", padx=(0, 15))
            
            # Charger et afficher l'image
            try:
                # Ouvrir et redimensionner l'image
                icon_image = Image.open(icon_path).resize((32, 32), Image.Resampling.LANCZOS)
                icon_tk = ImageTk.PhotoImage(icon_image)
                
                # Garder une référence pour éviter le garbage collection
                self.forbidden_icon_refs.append(icon_tk)
                
                # Créer le label avec l'image
                icon_label = tk.Label(item_frame, image=icon_tk, bg=Config.COLORS["card"])
                icon_label.pack(pady=(0, 5))
                
            except Exception as e:
                print(f"Erreur chargement image {icon_path}: {e}")
                # Fallback avec emoji si image non trouvée
                fallback_emojis = {
                    "Médicaments": "💊", 
                    "Piles": "🔋", 
                    "Ampoules": "💡", 
                    "Produits chimiques": "⚗️"
                }
                fallback_emoji = fallback_emojis.get(item_name, "❓")
                tk.Label(item_frame, text=fallback_emoji, 
                        font=("Segoe UI Emoji", 24), 
                        bg=Config.COLORS["card"]).pack(pady=(0, 5))
            
            # Texte sous l'image
            tk.Label(item_frame, text=item_name, 
                     font=("Segoe UI", Config.FONT_SIZE_SMALL),
                     bg=Config.COLORS["card"], 
                     fg=Config.COLORS["text_secondary"]).pack()
        
        # MESSAGE D'AVERTISSEMENT
        message_frame = tk.Frame(content_frame, bg=Config.COLORS["warning_zone"], padx=8, pady=5)
        message_frame.pack(fill="x")
        
        warning_text = "⚠️ Ces objets nécessitent un traitement spécialisé\nMerci de les déposer dans un lieu prévu à cet effet"
        tk.Label(message_frame, text=warning_text, 
                 font=("Segoe UI", Config.FONT_SIZE_SMALL, "bold"),
                 bg=Config.COLORS["warning_zone"], 
                 fg=Config.COLORS["error"]).pack()

    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg=Config.COLORS["background"])
        header_frame.pack(fill="x", pady=(0, 10))
        title_container = tk.Frame(header_frame, bg=Config.COLORS["background"])
        title_container.pack(side="left")
        tk.Label(title_container, text="🗂️", font=("Segoe UI Emoji", Config.EMOJI_SIZE),
                 bg=Config.COLORS["background"]).pack(side="left", padx=(0, 10))
        title_text_frame = tk.Frame(title_container, bg=Config.COLORS["background"])
        title_text_frame.pack(side="left")
        tk.Label(title_text_frame, text="BinGo", font=("Segoe UI", Config.FONT_SIZE_LARGE, "bold"),
                 bg=Config.COLORS["background"], fg=Config.COLORS["primary"]).pack(anchor="w")
        tk.Label(title_text_frame, text="Nous sommes heureux de vous accueillir", font=("Segoe UI", Config.FONT_SIZE_SMALL),
                 bg=Config.COLORS["background"], fg=Config.COLORS["text_secondary"]).pack(anchor="w")
        controls_frame = tk.Frame(header_frame, bg=Config.COLORS["background"])
        controls_frame.pack(side="right")
        self.camera_btn = ModernUI.create_modern_button(controls_frame, "📹 Caméra", self.toggle_camera, "secondary")
        self.camera_btn.pack(side="right", padx=(5, 0))
        self.reset_btn = ModernUI.create_modern_button(controls_frame, "🔄 Reset", self.reset_stats, "accent")
        self.reset_btn.pack(side="right", padx=(5, 0))
        self.exit_btn = ModernUI.create_modern_button(controls_frame, "✕ Quitter", self.on_closing, "primary")
        self.exit_btn.pack(side="right", padx=(5, 0))

    def create_detection_panel(self, parent):
        detection_container = tk.Frame(parent, bg=Config.COLORS["background"])
        detection_container.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        detection_card, detection_content = ModernUI.create_card(detection_container, "🔍 Détection en Temps Réel")
        detection_card.pack(fill="both", expand=True)
        self.result_frame = tk.Frame(detection_content, bg=Config.COLORS["card"])
        self.result_frame.pack(fill="both", expand=True, pady=10)
        self.create_waiting_state()

    def create_stats_panel(self, parent):
        stats_container = tk.Frame(parent, bg=Config.COLORS["background"])
        stats_container.grid(row=0, column=1, sticky="nsew")
        stats_card, stats_content = ModernUI.create_card(stats_container, "📈 Statistiques")
        stats_card.pack(fill="both", expand=True)
        self.stats_content = stats_content
        self.update_stats_display()

    def create_status_bar(self, parent):
        status_frame = tk.Frame(parent, bg=Config.COLORS["surface_dark"], relief="flat", padx=10, pady=5)
        status_frame.pack(fill="x", pady=(8, 0))
        self.status_label = tk.Label(status_frame, text="🟢 Système prêt", font=("Segoe UI", Config.FONT_SIZE_SMALL),
                                     bg=Config.COLORS["surface_dark"], fg=Config.COLORS["text_secondary"])
        self.status_label.pack(side="left")

    def create_waiting_state(self):
        for widget in self.result_frame.winfo_children():
            widget.destroy()
    
        waiting_container = tk.Frame(self.result_frame, bg=Config.COLORS["card"])
        waiting_container.place(relx=0.5, rely=0.5, anchor="center")
    
        # ICÔNE LOUPE AVEC IMAGE
        try:
            search_icon_path = "/home/bingo/Desktop/poubelle/icons/loupe.jpg"  # ou search.png
            search_image = Image.open(search_icon_path).resize((48, 48), Image.Resampling.LANCZOS)
            search_tk = ImageTk.PhotoImage(search_image)
        
            self.search_icon = tk.Label(waiting_container, image=search_tk, bg=Config.COLORS["card"])
            self.search_icon.image = search_tk  # Garder une référence
            self.search_icon.pack(pady=(0, 15))
            
        except Exception as e:
            print(f"Erreur chargement icône loupe: {e}")
            # Fallback emoji si image non trouvée
            self.search_icon = tk.Label(waiting_container, text="🔍", 
                                        font=("Segoe UI Emoji", 32),
                                        bg=Config.COLORS["card"])
            self.search_icon.pack(pady=(0, 15))
    
        # Texte principal
        tk.Label(waiting_container, text="En attente d'un objet...", 
                 font=("Segoe UI", Config.FONT_SIZE_MEDIUM, "bold"),
                 bg=Config.COLORS["card"], fg=Config.COLORS["text_secondary"]).pack()
    
        # Sous-texte
        tk.Label(waiting_container, text="Placez un déchet devant la caméra", 
                 font=("Segoe UI", Config.FONT_SIZE_SMALL),
                 bg=Config.COLORS["card"], fg=Config.COLORS["text_muted"]).pack(pady=(5, 0))
    
        self.animate_search_icon()
    
    def animate_search_icon(self):
        if hasattr(self, 'search_icon') and self.search_icon.winfo_exists():
            current = self.search_icon.cget("text")
            icons = ["🔍", "🔎", "🔍", "⌚"]
            try:
                next_index = (icons.index(current) + 1) % len(icons)
                self.search_icon.config(text=icons[next_index])
            except ValueError:
                self.search_icon.config(text="🔍")
            self.after(800, self.animate_search_icon)

    def create_stabilization_display(self, label, progress):
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        result_container = tk.Frame(self.result_frame, bg=Config.COLORS["card"])
        result_container.place(relx=0.5, rely=0.5, anchor="center")
        label_mapping = {
            "cardboard_paper": ("📄", "Papier / Carton"), "plastic": ("🧴", "Plastique"),
            "metal": ("🥫", "Métal"), "glass": ("🍾", "Verre"), "trash": ("🗑️", "Non recyclable")
        }
        icon, french_label = label_mapping.get(label, ("❓", label))
        tk.Label(result_container, text=icon, font=("Segoe UI Emoji", 28), bg=Config.COLORS["card"]).pack(pady=(0, 8))
        tk.Label(result_container, text=f"Analyse: {french_label}", font=("Segoe UI", Config.FONT_SIZE_MEDIUM, "bold"),
                 bg=Config.COLORS["card"], fg=Config.COLORS["primary"]).pack()
        progress_frame = tk.Frame(result_container, bg=Config.COLORS["card"])
        progress_frame.pack(pady=(10, 8))
        progress_bg = tk.Frame(progress_frame, bg=Config.COLORS["border"], width=200, height=8)
        progress_bg.pack()
        progress_bg.pack_propagate(False)
        fill_width = int(200 * progress)
        if fill_width > 0:
            progress_fill = tk.Frame(progress_bg, bg=Config.COLORS["primary"], height=8)
            progress_fill.place(x=0, y=0, width=fill_width)
        remaining_time = max(0, 3.0 - (progress * 3.0))
        tk.Label(result_container, text=f"Stabilisation: {remaining_time:.1f}s restantes",
                 font=("Segoe UI", Config.FONT_SIZE_SMALL), bg=Config.COLORS["card"],
                 fg=Config.COLORS["text_secondary"]).pack(pady=(3, 0))
        tk.Label(result_container, text="Maintenez l'objet stable...", font=("Segoe UI", Config.FONT_SIZE_SMALL),
                 bg=Config.COLORS["card"], fg=Config.COLORS["text_muted"]).pack(pady=(3, 0))

    def create_result_display(self, label, confidence):
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        result_container = tk.Frame(self.result_frame, bg=Config.COLORS["card"])
        result_container.place(relx=0.5, rely=0.4, anchor="center")
        label_mapping = {
            "cardboard_paper": ("📄", "Papier / Carton", Config.COLORS["info"]),
            "plastic": ("🧴", "Plastique", Config.COLORS["warning"]),
            "metal": ("🥫", "Métal", Config.COLORS["text_secondary"]),
            "glass": ("🍾", "Verre", Config.COLORS["success"]),
            "trash": ("🗑️", "Non recyclable", Config.COLORS["error"])
        }
        icon, french_label, color = label_mapping.get(label, ("❓", label, Config.COLORS["text_primary"]))
        tk.Label(result_container, text=icon, font=("Segoe UI Emoji", 32), bg=Config.COLORS["card"]).pack(pady=(0, 10))
        tk.Label(result_container, text=french_label, font=("Segoe UI", Config.FONT_SIZE_MEDIUM, "bold"),
                 bg=Config.COLORS["card"], fg=color).pack()
        confidence_text = f"Confiance: {confidence:.1f}%"
        confidence_color = Config.COLORS["success"] if confidence >= 80 else Config.COLORS["warning"]
        tk.Label(result_container, text=confidence_text, font=("Segoe UI", Config.FONT_SIZE_SMALL),
                 bg=Config.COLORS["card"], fg=confidence_color).pack(pady=(5, 10))
        tk.Label(result_container, text="OBJET CLASSIFIÉ", font=("Segoe UI", Config.FONT_SIZE_SMALL, "bold"),
                 bg=Config.COLORS["card"], fg=Config.COLORS["success"]).pack(pady=(3, 0))
        tk.Label(result_container, text="Bras en mouvement...", font=("Segoe UI", Config.FONT_SIZE_SMALL),
                 bg=Config.COLORS["card"], fg=Config.COLORS["text_muted"]).pack(pady=(3, 0))

    def update_stats_display(self):
        for widget in self.stats_content.winfo_children():
            widget.destroy()
        total_frame = tk.Frame(self.stats_content, bg=Config.COLORS["card"])
        total_frame.pack(fill="x", pady=(0, 10))
        tk.Label(total_frame, text="Total d'objets analysés", font=("Segoe UI", Config.FONT_SIZE_SMALL, "bold"),
                 bg=Config.COLORS["card"], fg=Config.COLORS["text_primary"]).pack(anchor="w")
        tk.Label(total_frame, text=str(self.stats["total"]), font=("Segoe UI", 18, "bold"),
                 bg=Config.COLORS["card"], fg=Config.COLORS["primary"]).pack(anchor="w")
        categories = {
            "papier": ("icons/carton.jpg", "Papier/Carton", Config.COLORS["info"]),
            "plastique": ("icons/sac.jpg", "Plastique", Config.COLORS["warning"]),
            "metal": ("icons/canette.png", "Métal", Config.COLORS["text_secondary"]),
            "verre": ("icons/verre.jpg", "Verre", Config.COLORS["success"]),
            "non_recyclable": ("icons/trash.png", "Non recyclable", Config.COLORS["error"])
        }
        self.icon_refs = []  # Pour éviter le garbage collection
        for key, (icon_path, name, color) in categories.items():
            count = self.stats[key]
            percentage = (count / max(self.stats["total"], 1)) * 100
            cat_frame = tk.Frame(self.stats_content, bg=Config.COLORS["card"])
            cat_frame.pack(fill="x", pady=2)
            info_frame = tk.Frame(cat_frame, bg=Config.COLORS["card"])
            info_frame.pack(fill="x")
            # Charger l'image
            icon_image = Image.open(icon_path).resize((20, 20), Image.Resampling.LANCZOS)
            icon_tk = ImageTk.PhotoImage(icon_image)
            self.icon_refs.append(icon_tk)  # Garder une référence
            tk.Label(info_frame, image=icon_tk, bg=Config.COLORS["card"]).pack(side="left", padx=(0, 5))
            tk.Label(info_frame, text=name, font=("Segoe UI", Config.FONT_SIZE_SMALL),
                     bg=Config.COLORS["card"], fg=Config.COLORS["text_primary"]).pack(side="left")
            tk.Label(info_frame, text=f"{count} ({percentage:.1f}%)", font=("Segoe UI", Config.FONT_SIZE_SMALL, "bold"),
                     bg=Config.COLORS["card"], fg=color).pack(side="right")
            #if self.stats["total"] > 0:
                #progress_bg = tk.Frame(cat_frame, bg=Config.COLORS["border"], height=3)
                #progress_bg.pack(fill="x", pady=(2, 0))
                #if count > 0:
                    #progress_fill = tk.Frame(progress_bg, bg=color, height=3)
                    #progress_fill.place(x=0, y=0, relwidth=percentage/100, height=3)

    def start_systems(self):
        self.detection.start(self)
        self.update_status("Détection active")
        self.check_detections()

    def check_detections(self):
        try:
            progress, current_label = self.comm.get_stability_progress()
            if current_label and progress < 1.0:
                self.create_stabilization_display(current_label, progress)
                self.update_status(f"Analyse en cours: {current_label} ({progress*100:.0f}%)")
            while not self.comm.detection_queue.empty():
                detection_data = self.comm.detection_queue.get_nowait()
                if detection_data[0] == "NO_OBJECT":
                    self.handle_no_object()
                elif detection_data[0] == "validation":
                    _, label, confidence, image_data = detection_data
                    self.handle_detection(label, confidence)
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Erreur détections: {e}")
        self.after(100, self.check_detections)

    def handle_detection(self, label, confidence):
        print(f"DÉTECTION CONFIRMÉE après 3s: {label} ({confidence:.1f}%)")
        self.update_stats(label)
        self.create_result_display(label, confidence)
        self.current_result = (label, confidence)
        if self.result_timer:
            self.after_cancel(self.result_timer)
        self.result_timer = self.after(2000, self.return_to_waiting)
        print("Objet classifié")
        self.update_status(f"CONFIRMÉ: {label} - Retour dans 2s")
        self.start_countdown_status(label)

    def start_countdown_status(self, label):
        def countdown(seconds_left):
            if seconds_left > 0:
                self.update_status(f"✅ CONFIRMÉ: {label} - Retour dans {seconds_left}s")
                self.after(1000, lambda: countdown(seconds_left - 1))
            else:
                self.update_status("🟢 Système prêt")
        countdown(2)

    def handle_no_object(self):
        self.return_to_waiting()
        self.update_status("🔍 En attente d'un objet")

    def return_to_waiting(self):
        if self.result_timer:
            self.after_cancel(self.result_timer)
        self.result_timer = None
        self.current_result = None
        self.create_waiting_state()
        self.comm.reset_stability_tracking()
        self.update_status("Système prêt - En attente d'un objet")
        print("Retour à l'écran d'attente")

    def update_stats(self, label):
        self.stats["total"] += 1
        label_to_stats = {
            "cardboard_paper": "papier", "plastic": "plastique", "metal": "metal",
            "glass": "verre", "trash": "non_recyclable"
        }
        key = label_to_stats.get(label, "non_recyclable")
        self.stats[key] += 1
        self.update_stats_display()

    def reset_stats(self):
        for key in self.stats:
            self.stats[key] = 0
        self.update_stats_display()
        self.update_status("📊 Statistiques remises à zéro")

    def toggle_camera(self):
        if self.detection.camera_window is None:
            self.detection.create_camera_window(self)
            self.camera_btn.config(text="Masquer")
        else:
            self.detection.close_camera_window()
            self.camera_btn.config(text="Caméra")

    def update_status(self, message):
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)

    def on_closing(self):
        print("Fermeture de l'application...")
        self.detection.stop()
        self.destroy()
class EnhancedCommunicationSystem(CommunicationSystem):
    def __init__(self):
        super().__init__()
        self.arduino = ArduinoController()
        
    def initialize_arduino(self):
        """Initialiser la connexion Arduino"""
        if self.arduino.connect():
            self.arduino.start_monitoring()
            return True
        return False
    
    def send_classification_to_arduino(self, label):
        """Envoyer la classification à l'Arduino pour actionner les servos"""
        # Mapper les labels de votre système vers les commandes Arduino
        label_mapping = {
            "plastic": "plastique",
            "cardboard_paper": "carton", 
            "glass": "verre",
            "metal": "metal",
            "trash": "non recyclable"
        }
        
        arduino_command = label_mapping.get(label, "non recyclable")
        return self.arduino.send_command(arduino_command)
    
    def get_bin_levels(self):
        """Obtenir les niveaux actuels des bacs"""
        return self.arduino.current_data

# Modification de votre classe MainApplication
class EnhancedMainApplication(MainApplication):
    def __init__(self, comm_system, detection_system):
        super().__init__(comm_system, detection_system)
        
        # Initialiser l'Arduino
        if self.comm.initialize_arduino():
            print("✅ Arduino connecté et prêt")
        else:
            print("⚠️ Arduino non disponible - Mode simulation")
    
    def handle_detection(self, label, confidence):
        """Gestion améliorée des détections avec contrôle Arduino"""
        print(f"DÉTECTION CONFIRMÉE: {label} ({confidence:.1f}%)")
        
        # Envoyer la commande à l'Arduino
        if hasattr(self.comm, 'send_classification_to_arduino'):
            success = self.comm.send_classification_to_arduino(label)
            if success:
                print(f"🤖 Commande Arduino envoyée: {label}")
            else:
                print("⚠️ Échec envoi commande Arduino")
        
        # Continuer avec le traitement normal
        self.update_stats(label)
        self.create_result_display(label, confidence)
        self.current_result = (label, confidence)
        
        if self.result_timer:
            self.after_cancel(self.result_timer)
        self.result_timer = self.after(2000, self.return_to_waiting)
        
        self.update_status(f"✅ CONFIRMÉ: {label} - Arduino activé")
        self.start_countdown_status(label)
# === Point d'entrée principal ===
def main():
    print("🚀 Démarrage de BinGo avec contrôle Arduino")
    print("=" * 60)
    
    try:
        # Utiliser les classes améliorées
        comm_system = EnhancedCommunicationSystem()
        detection_system = DetectionSystem(comm_system)
        app = EnhancedMainApplication(comm_system, detection_system)
        
        print("✅ Interface utilisateur créée")
        print("🎯 Système de détection initialisé") 
        print("🤖 Contrôleur Arduino intégré")
        print("=" * 60)
        print("BinGo est prêt à fonctionner!")
        
        app.mainloop()
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur critique: {str(e)}")
    finally:
        print("🔚 Arrêt de BinGo")

if __name__ == "__main__":
    main()
