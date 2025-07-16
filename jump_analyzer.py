import cv2
import mediapipe as mp
import numpy as np
import json
import time
from datetime import datetime
import logging
import yaml
from collections import deque
from enum import Enum
import os
import math

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PoseDetectionError(Exception):
    """Excepción para errores en la detección de pose."""
    pass

class CalibrationError(Exception):
    """Excepción para errores durante la calibración."""
    pass

# Cargar configuración
try:
    with open('config_Saltos.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    PROPORCIONES = config.get('proporciones', {})
    ROM_OPTIMO_SALTO = config.get('rom_optimo_salto', {})
    PARAMETROS_SALTO = config.get('parametros_salto', {})
    NIVEL_USUARIO = config.get('nivel_usuario', {})
except FileNotFoundError:
    logging.error("config_Saltos.yaml no encontrado. Usando parámetros por defecto.")
    # Parámetros por defecto
    PROPORCIONES = {
        'm': {'altura_femur': 0.23, 'altura_tibia': 0.22, 'distancia_rodillas': 0.18},
        'f': {'altura_femur': 0.22, 'altura_tibia': 0.21, 'distancia_rodillas': 0.17}
    }
    ROM_OPTIMO_SALTO = {
        "rodilla": {
            "flexion_min_cm": 90,
            "flexion_objetivo_cm": 70,
            "extension_takeoff": 170,
            "flexion_landing_max": 90,
            "extension_landing_min": 160
        },
        "cadera": {
            "flexion_min_cm": 100,
            "extension_takeoff": 170,
            "flexion_landing_max": 90
        },
        "tobillo": {
            "dorsiflexion_cm": 70,
            "plantarflexion_takeoff": 160,
            "dorsiflexion_landing": 80
        },
        "columna": {
            "alineacion_general": 170,
            "inclinacion_tronco_max": 30
        }
    }
    PARAMETROS_SALTO = {
        "min_flight_time": 0.15,
        "min_vertical_displacement_m": 0.10,
        "max_landing_time": 0.5,
        "rodillas_valgo_tolerancia_x": 0.04,
        "stiff_landing_tolerance": 10,
        "max_landing_impact_angle_vel": 1.5
    }
    NIVEL_USUARIO = {
        'principiante': {
            'tolerancia_angulo': 20,
            'velocidad_cm_min': 0.10,
            'velocidad_takeoff_min': 0.4,
            'rango_minimo_cm': 70
        },
        'intermedio': {
            'tolerancia_angulo': 10,
            'velocidad_cm_min': 0.20,
            'velocidad_takeoff_min': 0.8,
            'rango_minimo_cm': 80
        },
        'avanzado': {
            'tolerancia_angulo': 5,
            'velocidad_cm_min': 0.30,
            'velocidad_takeoff_min': 1.2,
            'rango_minimo_cm': 90
        }
    }

class EstadoSalto(Enum):
    INICIAL = "INICIAL"
    CONTRAMOVIMIENTO = "CONTRAMOVIMIENTO"
    DESPEGUE = "DESPEGUE"
    VUELO = "VUELO"
    ATERRIZAJE = "ATERRIZAJE"
    ESTABLE_POST_ATERRIZAJE = "ESTABLE_POST_ATERRIZAJE"

class TipoSalto(Enum):
    CMJ = "Counter Movement Jump (CMJ)"
    SQJ = "Squat Jump (SQJ)"
    ABALAKOV = "Abalakov"

RANGOS_CLASIFICACION = {
    'hombres': {
        'CMJ': {'bajo': (0, 30), 'medio': (30, 40), 'avanzado': (40, 50), 'elite': (50, 100)},
        'SQJ': {'bajo': (0, 25), 'medio': (25, 35), 'avanzado': (35, 45), 'elite': (45, 100)},
        'ABALAKOV': {'bajo': (0, 35), 'medio': (35, 45), 'avanzado': (45, 55), 'elite': (55, 100)}
    },
    'mujeres': {
        'CMJ': {'bajo': (0, 22), 'medio': (22, 30), 'avanzado': (30, 38), 'elite': (38, 100)},
        'SQJ': {'bajo': (0, 18), 'medio': (18, 25), 'avanzado': (25, 33), 'elite': (33, 100)},
        'ABALAKOV': {'bajo': (0, 25), 'medio': (25, 35), 'avanzado': (35, 43), 'elite': (43, 100)}
    }
}

class JumpAnalyzer:
    def __init__(self, usuario_perfil):
        self.usuario = usuario_perfil
        self.contador = 0
        self.correctas = 0
        self.estado = EstadoSalto.INICIAL
        self.errores = {
            "insufficient_cm_depth": 0,
            "prematura_extension": 0,
            "rodillas_valgo_takeoff": 0,
            "insufficient_plantarflexion": 0,
            "stiff_landing": 0,
            "landing_imbalance": 0,
            "excessive_landing_impact": 0,
            "trunk_lean_takeoff_landing": 0
        }
        self.gravedad_errores = {
            "insufficient_cm_depth": 1,
            "prematura_extension": 2,
            "rodillas_valgo_takeoff": 2,
            "insufficient_plantarflexion": 1,
            "stiff_landing": 2,
            "landing_imbalance": 1.5,
            "excessive_landing_impact": 1.5,
            "trunk_lean_takeoff_landing": 1
        }
        self.potencia = 0.0
        self.potencia_target = 0.0
        self.calibrado = False
        self.ultimo_tiempo = time.time()

        self.initial_hip_y = 0
        self.initial_knee_x_diff = 0
        self.max_hip_y_cm = 0
        self.min_hip_y_flight = float('inf')
        self.takeoff_time = 0
        self.landing_time = 0
        self.jump_height_m = 0
        self.tipo_salto = TipoSalto.CMJ

        self.historial_angulos_rodilla = []
        self.historial_angulos_cadera = []
        self.historial_pos_y_cadera = []
        self.historial_tiempos = []
        self.mensajes_feedback = []

        self.alturas_saltos = []
        self.tiempos_vuelo = []
        self.potencias = []
        self.indice_elasticidad = 0.0
        self.indice_coordinacion = 0.0

        self.smoothed_knee_angles = deque(maxlen=5)
        self.smoothed_hip_angles = deque(maxlen=5)
        self.smoothed_ankle_angles = deque(maxlen=5)
        self.smoothed_trunk_angles = deque(maxlen=5)

        self.umbrales = {
            "rodilla_flexion_min_cm": ROM_OPTIMO_SALTO["rodilla"]["flexion_min_cm"],
            "rodilla_flexion_objetivo_cm": ROM_OPTIMO_SALTO["rodilla"]["flexion_objetivo_cm"],
            "rodilla_extension_takeoff": ROM_OPTIMO_SALTO["rodilla"]["extension_takeoff"],
            "rodilla_flexion_landing_max": ROM_OPTIMO_SALTO["rodilla"]["flexion_landing_max"],
            "rodilla_extension_landing_min": ROM_OPTIMO_SALTO["rodilla"]["extension_landing_min"],
            "cadera_flexion_min_cm": ROM_OPTIMO_SALTO["cadera"]["flexion_min_cm"],
            "cadera_extension_takeoff": ROM_OPTIMO_SALTO["cadera"]["extension_takeoff"],
            "cadera_flexion_landing_max": ROM_OPTIMO_SALTO["cadera"]["flexion_landing_max"],
            "tobillo_dorsiflexion_cm": ROM_OPTIMO_SALTO["tobillo"]["dorsiflexion_cm"],
            "tobillo_plantarflexion_takeoff": ROM_OPTIMO_SALTO["tobillo"]["plantarflexion_takeoff"],
            "tobillo_dorsiflexion_landing": ROM_OPTIMO_SALTO["tobillo"]["dorsiflexion_landing"],
            "columna_alineacion_general": ROM_OPTIMO_SALTO["columna"]["alineacion_general"],
            "inclinacion_tronco_max": ROM_OPTIMO_SALTO["columna"]["inclinacion_tronco_max"],
            "min_flight_time": PARAMETROS_SALTO["min_flight_time"],
            "min_vertical_displacement_m": PARAMETROS_SALTO["min_vertical_displacement_m"],
            "max_landing_time": PARAMETROS_SALTO["max_landing_time"],
            "rodillas_valgo_tolerancia_x": PARAMETROS_SALTO["rodillas_valgo_tolerancia_x"],
            "stiff_landing_tolerance": PARAMETROS_SALTO["stiff_landing_tolerance"],
            "max_landing_impact_angle_vel": PARAMETROS_SALTO["max_landing_impact_angle_vel"]
        }
        self.px_to_m = 0

        # Inicializar MediaPipe
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def set_tipo_salto(self, tipo_salto: TipoSalto):
        """Establece el tipo de salto a analizar"""
        self.tipo_salto = tipo_salto
        logging.info(f"Tipo de salto configurado: {tipo_salto.value}")
        
        if tipo_salto == TipoSalto.CMJ:
            self.mensajes_feedback.append("SALTO CMJ: Inicie de pie, flexión rápida y salto")
        elif tipo_salto == TipoSalto.SQJ:
            self.mensajes_feedback.append("SALTO SQJ: Mantenga posición flexionada 3s antes de saltar")
        elif tipo_salto == TipoSalto.ABALAKOV:
            self.mensajes_feedback.append("SALTO ABALAKOV: Use brazos para impulsarse activamente")

    def calibrar(self, lm):
        """Calibra el sistema usando los landmarks detectados"""
        try:
            required_landmarks = [
                self.mp_pose.PoseLandmark.LEFT_HIP,
                self.mp_pose.PoseLandmark.RIGHT_HIP,
                self.mp_pose.PoseLandmark.LEFT_KNEE,
                self.mp_pose.PoseLandmark.RIGHT_KNEE,
                self.mp_pose.PoseLandmark.LEFT_ANKLE,
                self.mp_pose.PoseLandmark.RIGHT_ANKLE,
                self.mp_pose.PoseLandmark.LEFT_SHOULDER,
                self.mp_pose.PoseLandmark.RIGHT_SHOULDER
            ]

            for landmark in required_landmarks:
                if landmark.value >= len(lm) or not lm[landmark.value].visibility > 0.7:
                    logging.warning(f"Calibración fallida: Landmark {landmark.name} no visible o ausente.")
                    raise CalibrationError(f"Landmark {landmark.name} no detectado o visibilidad baja.")

            lhip_3d = np.array([lm[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
                                lm[self.mp_pose.PoseLandmark.LEFT_HIP.value].y,
                                lm[self.mp_pose.PoseLandmark.LEFT_HIP.value].z])
            rhip_3d = np.array([lm[self.mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                                lm[self.mp_pose.PoseLandmark.RIGHT_HIP.value].y,
                                lm[self.mp_pose.PoseLandmark.RIGHT_HIP.value].z])
            lknee_3d = np.array([lm[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                                 lm[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y,
                                 lm[self.mp_pose.PoseLandmark.LEFT_KNEE.value].z])
            rknee_3d = np.array([lm[self.mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                                 lm[self.mp_pose.PoseLandmark.RIGHT_KNEE.value].y,
                                 lm[self.mp_pose.PoseLandmark.RIGHT_KNEE.value].z])

            mid_hip_initial_y_px = (lhip_3d[1] + rhip_3d[1]) / 2
            dist_rodillas_px = np.hypot(lknee_3d[0] - rknee_3d[0], lknee_3d[1] - rknee_3d[1])
            
            if dist_rodillas_px > 0:
                self.px_to_m = self.usuario.longitudes["distancia_rodillas"] / dist_rodillas_px
            else:
                logging.error("Distancia entre rodillas cero durante calibración.")
                raise CalibrationError("Distancia entre rodillas cero. Posición incorrecta.")

            self.initial_hip_y = mid_hip_initial_y_px
            self.initial_knee_x_diff = abs(lknee_3d[0] - rknee_3d[0])

            if self.px_to_m < 0.001 or self.initial_hip_y <= 0:
                logging.error("Valores de calibración inválidos. Reiniciando calibración.")
                self.calibrado = False
                return False

            self.calibrado = True
            logging.info(f"Calibrado exitoso: factor_px_m={self.px_to_m:.5f}, initial_hip_y={self.initial_hip_y:.5f}")
            return True
            
        except CalibrationError as e:
            logging.error(f"Error específico en calibración: {e}")
            self.calibrado = False
            return False
        except Exception as e:
            logging.error(f"Error inesperado en calibración: {e}")
            self.calibrado = False
            return False

    def process_frame(self, frame):
        """Procesa un frame de la cámara y retorna datos de análisis"""
        try:
            if frame is None:
                return {
                    'error': 'Frame vacío',
                    'estado': self.estado.value,
                    'feedback': ['Error: Frame vacío']
                }

            # Convertir frame a RGB para MediaPipe
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image_rgb)

            if not results.pose_landmarks:
                return {
                    'error': 'No se detectó pose',
                    'estado': self.estado.value,
                    'feedback': ['Ajuste su posición para ser visible completamente']
                }

            lm = results.pose_landmarks.landmark

            if not self.calibrado:
                calibration_success = self.calibrar(lm)
                return {
                    'calibrando': True,
                    'calibration_success': calibration_success,
                    'estado': 'CALIBRANDO',
                    'feedback': ['Mantenga posición estable para calibrar'] if not calibration_success else ['Calibración exitosa']
                }

            # Procesar análisis de salto
            angle_rodilla, postura_ok, detalles_salto = self.verificar(lm)
            
            return {
                'calibrando': False,
                'angulo_rodilla': angle_rodilla,
                'postura_correcta': postura_ok,
                'estado': self.estado.value,
                'jump_height': self.jump_height_m,
                'potencia': self.potencia,
                'contador': self.contador,
                'correctas': self.correctas,
                'feedback': self.mensajes_feedback[-3:] if self.mensajes_feedback else [],
                'detalles': detalles_salto,
                'tipo_salto': self.tipo_salto.value
            }

        except Exception as e:
            logging.error(f"Error procesando frame: {e}")
            return {
                'error': f'Error procesando frame: {str(e)}',
                'estado': self.estado.value,
                'feedback': [f'Error: {str(e)}']
            }

    def verificar(self, lm):
        """Lógica principal de verificación de salto"""
        if not self.calibrado:
            logging.warning("Verificación llamada sin calibrar.")
            return 0, False, {"error": "Sin calibrar", "feedback": "Sin calibrar"}

        self.mensajes_feedback = []
        current_time = time.time()
        delta_time = current_time - self.ultimo_tiempo
        self.ultimo_tiempo = current_time

        try:
            visible_lm = {}
            for i, p in enumerate(lm):
                if p.visibility > 0.5:
                    visible_lm[i] = np.array([p.x, p.y, p.z])

            def pt(p_enum):
                idx = p_enum.value
                if idx in visible_lm:
                    return visible_lm[idx]
                logging.warning(f"Landmark {p_enum.name} no visible o ausente. Visibilidad: {lm[idx].visibility:.2f}")
                raise PoseDetectionError(f"Punto {p_enum.name} no detectado o visibilidad baja.")

            # Puntos clave
            lhip = pt(self.mp_pose.PoseLandmark.LEFT_HIP)
            lknee = pt(self.mp_pose.PoseLandmark.LEFT_KNEE)
            lankle = pt(self.mp_pose.PoseLandmark.LEFT_ANKLE)
            rhip = pt(self.mp_pose.PoseLandmark.RIGHT_HIP)
            rknee = pt(self.mp_pose.PoseLandmark.RIGHT_KNEE)
            rankle = pt(self.mp_pose.PoseLandmark.RIGHT_ANKLE)
            lshoulder = pt(self.mp_pose.PoseLandmark.LEFT_SHOULDER)
            rshoulder = pt(self.mp_pose.PoseLandmark.RIGHT_SHOULDER)
            lheel = pt(self.mp_pose.PoseLandmark.LEFT_HEEL)
            rheel = pt(self.mp_pose.PoseLandmark.RIGHT_HEEL)

            mid_hip_y_px = (lhip[1] + rhip[1]) / 2

            # Cálculo de ángulos
            ang_rodilla_l = self._angle_3d(lhip, lknee, lankle)
            ang_rodilla_r = self._angle_3d(rhip, rknee, rankle)
            prom_rodilla_raw = (ang_rodilla_l + ang_rodilla_r) / 2

            ang_cadera_l = self._angle_3d(lshoulder, lhip, lknee)
            ang_cadera_r = self._angle_3d(rshoulder, rhip, rknee)
            prom_cadera_raw = (ang_cadera_l + ang_cadera_r) / 2

            ang_tobillo_l = self._angle_3d(lknee, lankle, lheel)
            ang_tobillo_r = self._angle_3d(rknee, rankle, rheel)
            prom_tobillo_raw = (ang_tobillo_l + ang_tobillo_r) / 2

            # Aplicar suavizado
            self.smoothed_knee_angles.append(prom_rodilla_raw)
            self.smoothed_hip_angles.append(prom_cadera_raw)
            self.smoothed_ankle_angles.append(prom_tobillo_raw)

            prom_rodilla = np.mean(self.smoothed_knee_angles)
            prom_cadera = np.mean(self.smoothed_hip_angles)
            prom_tobillo = np.mean(self.smoothed_ankle_angles)

            # Detección de vuelo
            avg_heel_y = np.mean([lheel[1], rheel[1]])
            is_in_air = (avg_heel_y < (self.initial_hip_y - (self.usuario.altura_m * 0.15 * self.px_to_m)))

            # Velocidades angulares
            velocidad_rodilla = 0
            if self.historial_angulos_rodilla and delta_time > 0:
                velocidad_rodilla = abs(prom_rodilla - self.historial_angulos_rodilla[-1]) / delta_time

            self.historial_angulos_rodilla.append(prom_rodilla)
            self.historial_angulos_cadera.append(prom_cadera)
            self.historial_pos_y_cadera.append(mid_hip_y_px)
            self.historial_tiempos.append(current_time)

            # Máquina de estados
            postura_correcta_frame = True
            error_keys = []

            if self.estado == EstadoSalto.INICIAL:
                if mid_hip_y_px > (self.initial_hip_y + (0.02 * self.px_to_m)) and prom_rodilla < (self.umbrales["rodilla_extension_takeoff"] - self.usuario.umbrales_nivel['tolerancia_angulo']):
                    self.estado = EstadoSalto.CONTRAMOVIMIENTO
                    self.max_hip_y_cm = mid_hip_y_px
                    logging.info("Estado: CONTRAMOVIMIENTO")
                    self.mensajes_feedback.append("¡Iniciando contramovimiento!")

            elif self.estado == EstadoSalto.CONTRAMOVIMIENTO:
                if mid_hip_y_px > self.max_hip_y_cm:
                    self.max_hip_y_cm = mid_hip_y_px

                if prom_rodilla > (self.umbrales["rodilla_flexion_objetivo_cm"] + self.usuario.umbrales_nivel['tolerancia_angulo']):
                    self.errores["insufficient_cm_depth"] += 1
                    error_keys.append("insufficient_cm_depth")
                    self.mensajes_feedback.append("¡Profundidad insuficiente! Flexione más rodillas")
                    postura_correcta_frame = False

                if mid_hip_y_px < (self.max_hip_y_cm - (0.01 * self.px_to_m)) and prom_rodilla > (self.umbrales["rodilla_flexion_objetivo_cm"] + self.usuario.umbrales_nivel['tolerancia_angulo']):
                    self.estado = EstadoSalto.DESPEGUE
                    logging.info("Estado: DESPEGUE")
                    self.mensajes_feedback.append("¡Despegando!")
                    self.takeoff_time = current_time
                    self.min_hip_y_flight = mid_hip_y_px

            elif self.estado == EstadoSalto.DESPEGUE:
                if mid_hip_y_px < self.min_hip_y_flight:
                    self.min_hip_y_flight = mid_hip_y_px

                if is_in_air:
                    self.estado = EstadoSalto.VUELO
                    logging.info("Estado: VUELO")
                    self.mensajes_feedback.append("¡En el aire!")

            elif self.estado == EstadoSalto.VUELO:
                if not is_in_air:
                    self.estado = EstadoSalto.ATERRIZAJE
                    logging.info("Estado: ATERRIZAJE")
                    self.mensajes_feedback.append("¡Aterrizando!")
                    self.landing_time = current_time
                    
                    jump_peak_y_px = self.min_hip_y_flight
                    cm_lowest_y_px = self.max_hip_y_cm
                    self.jump_height_m = ((cm_lowest_y_px - jump_peak_y_px) * self.px_to_m)
                    
                    flight_duration = self.landing_time - self.takeoff_time
                    self.tiempos_vuelo.append(flight_duration)
                    
                    potencia = self.calcular_potencia(self.jump_height_m)
                    self.potencias.append(potencia)
                    
                    self.alturas_saltos.append(self.jump_height_m)

            elif self.estado == EstadoSalto.ATERRIZAJE:
                if prom_rodilla > self.umbrales["rodilla_flexion_landing_max"] + self.usuario.umbrales_nivel['tolerancia_angulo']:
                    self.errores["stiff_landing"] += 1
                    error_keys.append("stiff_landing")
                    self.mensajes_feedback.append("¡Aterrizaje rígido! Flexiona más rodillas al caer")
                    postura_correcta_frame = False

                if current_time - self.landing_time > self.umbrales["max_landing_time"]:
                    self.estado = EstadoSalto.ESTABLE_POST_ATERRIZAJE
                    logging.info("Estado: ESTABLE_POST_ATERRIZAJE")
                    
                    if postura_correcta_frame:
                        self.correctas += 1
                        self.mensajes_feedback.append(f"¡BUEN SALTO! Altura: {self.jump_height_m*100:.1f}cm")
                    else:
                        self.mensajes_feedback.append("¡Salto con errores!")
                    
                    self.contador += 1

            elif self.estado == EstadoSalto.ESTABLE_POST_ATERRIZAJE:
                if abs(mid_hip_y_px - self.initial_hip_y) < (0.05 * self.px_to_m):
                    self.estado = EstadoSalto.INICIAL
                    logging.info("Estado: INICIAL (listo para el próximo salto)")

            self._actualizar_potencia(postura_correcta_frame, prom_rodilla, velocidad_rodilla)

            return prom_rodilla, postura_correcta_frame, {
                "angulo_rodilla": prom_rodilla,
                "angulo_cadera": prom_cadera,
                "angulo_tobillo": prom_tobillo,
                "velocidad_rodilla": velocidad_rodilla,
                "mid_hip_y_px": mid_hip_y_px,
                "is_in_air": is_in_air,
                "jump_height_m": self.jump_height_m,
                "estado_salto_str": self.estado.value,
                "tipo_salto": self.tipo_salto.value
            }

        except PoseDetectionError as e:
            logging.warning(f"Error de detección en verificar: {e}")
            return 0, False, {"error": str(e), "feedback": str(e), "estado_salto_str": self.estado.value}
        except Exception as e:
            logging.error(f"Error inesperado en verificar: {e}")
            return 0, False, {"error": f"Error: {e}", "feedback": f"Error: {e}", "estado_salto_str": self.estado.value}

    def calcular_potencia(self, altura_salto):
        """Calcula la potencia mecánica en watts"""
        tiempo_impulso = math.sqrt(2 * altura_salto / 9.81)
        potencia = (self.usuario.peso_kg * 9.81 * altura_salto) / tiempo_impulso
        return potencia

    def _actualizar_potencia(self, postura_ok, angulo_rodilla, velocidad):
        """Sistema de potencia para saltos."""
        factor_tecnica = 0.7 if postura_ok else 0.4
        
        factor_velocidad = 0
        vel_takeoff_min = self.usuario.umbrales_nivel['velocidad_takeoff_min']
        if velocidad > vel_takeoff_min * 1.5:
            factor_velocidad = 0.3
        elif velocidad > vel_takeoff_min:
            factor_velocidad = 0.15

        factor_altura = 0
        if self.estado == EstadoSalto.VUELO and self.jump_height_m > 0:
            target_height = self.usuario.altura_m * 0.25
            factor_altura = min(1, self.jump_height_m / target_height) * 0.2

        incremento = (factor_tecnica + factor_velocidad + factor_altura) * 5
        self.potencia_target = min(100, self.potencia_target + incremento)

        if not postura_ok:
            self.potencia_target = max(0, self.potencia_target - 5)

        self.potencia += (self.potencia_target - self.potencia) * 0.2

    @staticmethod
    def _angle_3d(a, b, c):
        """Calcula el ángulo entre tres puntos en 3D."""
        ba = a - b
        bc = c - b
        dot_product = np.dot(ba, bc)
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        
        denominator = norm_ba * norm_bc
        if denominator < 1e-6:
            return 180.0
            
        cos_angle = dot_product / denominator
        return np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))

    def get_results(self):
        """Retorna los resultados finales del análisis"""
        precision = (self.correctas / max(self.contador, 1)) * 100 if self.contador > 0 else 0
        altura_promedio = np.mean(self.alturas_saltos) if self.alturas_saltos else 0
        potencia_promedio = np.mean(self.potencias) if self.potencias else 0
        tiempo_vuelo_promedio = np.mean(self.tiempos_vuelo) if self.tiempos_vuelo else 0
        
        clasificacion = self.clasificar_nivel(altura_promedio)
        
        if altura_promedio > 0.4:
            evaluacion = "EXCELENTE"
        elif altura_promedio > 0.3:
            evaluacion = "BUENO"
        elif altura_promedio > 0.2:
            evaluacion = "PROMEDIO"
        else:
            evaluacion = "POR DEBAJO DEL PROMEDIO"
            
        recomendaciones = self.generar_recomendaciones()
        
        return {
            "total": self.contador,
            "correctas": self.correctas,
            "errores": self.errores,
            "precision": precision,
            "altura_salto_promedio": altura_promedio,
            "potencia_promedio": potencia_promedio,
            "tiempo_vuelo_promedio": tiempo_vuelo_promedio,
            "clasificacion": clasificacion,
            "tipo_salto": self.tipo_salto.value,
            "evaluacion_rendimiento": evaluacion,
            "recomendaciones": recomendaciones
        }

    def clasificar_nivel(self, altura_promedio):
        """Clasifica al deportista según su rendimiento"""
        if altura_promedio == 0:
            return "Sin datos suficientes"
        
        altura_cm = altura_promedio * 100
        genero = "hombres" if self.usuario.sexo == "M" else "mujeres"
        tipo = self.tipo_salto.name
        
        rangos = RANGOS_CLASIFICACION[genero][tipo]
        
        if altura_cm < rangos['bajo'][1]:
            return "Bajo"
        elif altura_cm < rangos['medio'][1]:
            return "Medio"
        elif altura_cm < rangos['avanzado'][1]:
            return "Avanzado"
        else:
            return "Alto rendimiento"

    def generar_recomendaciones(self):
        """Genera recomendaciones basadas en el análisis"""
        recs = []
        
        if self.errores["rodillas_valgo_takeoff"] > 0:
            recs.append("Fortalezca glúteos medios para control de rodillas")
            recs.append("Practique sentadillas con banda elástica alrededor de rodillas")
            
        if self.errores["stiff_landing"] > 0:
            recs.append("Practique aterrizajes con mayor flexión de rodillas")
            recs.append("Entrene saltos a cajón con recepción suave")
            
        if self.errores["insufficient_cm_depth"] > 0:
            recs.append("Mejore la profundidad del contramovimiento")
            recs.append("Trabaje movilidad de cadera y tobillos")
            
        if self.alturas_saltos and max(self.alturas_saltos) < 0.25:
            recs.append("Trabaje ejercicios pliométricos para mejorar potencia")
            recs.append("Incorpore saltos con contramovimiento profundo")
            
        if self.errores["trunk_lean_takeoff_landing"] > 0:
            recs.append("Fortalezca core para mantener tronco erguido")
            recs.append("Practique planchas y ejercicios de estabilidad")
            
        if not recs:
            recs.append("¡Buen trabajo! Continúe con su rutina actual")
            
        return recs

    def reset_session(self):
        """Reinicia la sesión de análisis"""
        self.contador = 0
        self.correctas = 0
        self.estado = EstadoSalto.INICIAL
        self.errores = {k: 0 for k in self.errores}
        self.potencia = 0.0
        self.potencia_target = 0.0
        self.calibrado = False
        
        self.initial_hip_y = 0
        self.initial_knee_x_diff = 0
        self.max_hip_y_cm = 0
        self.min_hip_y_flight = float('inf')
        self.takeoff_time = 0
        self.landing_time = 0
        self.jump_height_m = 0
        
        self.historial_angulos_rodilla = []
        self.historial_angulos_cadera = []
        self.historial_pos_y_cadera = []
        self.historial_tiempos = []
        self.mensajes_feedback = []
        
        self.alturas_saltos = []
        self.tiempos_vuelo = []
        self.potencias = []
        
        self.smoothed_knee_angles.clear()
        self.smoothed_hip_angles.clear()
        self.smoothed_ankle_angles.clear()
        self.smoothed_trunk_angles.clear()
        
        self.px_to_m = 0
        
        logging.info("Sesión de análisis reiniciada")
