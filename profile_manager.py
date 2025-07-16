import json
import os
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar configuración de proporciones
try:
    import yaml
    with open('config_Saltos.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    PROPORCIONES = config.get('proporciones', {})
    NIVEL_USUARIO = config.get('nivel_usuario', {})
except FileNotFoundError:
    logging.error("config_Saltos.yaml no encontrado. Usando parámetros por defecto.")
    PROPORCIONES = {
        'm': {'altura_femur': 0.23, 'altura_tibia': 0.22, 'distancia_rodillas': 0.18},
        'f': {'altura_femur': 0.22, 'altura_tibia': 0.21, 'distancia_rodillas': 0.17}
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

class UsuarioPerfil:
    def __init__(self, nombre="", sexo="", edad=0, altura_cm=0, peso_kg=0, nivel_actividad=""):
        self.nombre = nombre
        self.sexo = sexo.upper()
        self.edad = edad
        self.altura_cm = altura_cm
        self.peso_kg = peso_kg
        self.nivel_actividad = nivel_actividad if nivel_actividad in NIVEL_USUARIO else 'principiante'
        self.fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.altura_m = self.altura_cm / 100.0
        self.imc = self.peso_kg / (self.altura_m ** 2) if self.altura_m > 0 else 0

        # Inicializar longitudes como diccionario vacío
        self.longitudes = {}
        # Solo calcular si tenemos datos válidos
        if self.sexo in ['M', 'F'] and self.altura_cm > 0:
            self.calcular_longitudes()
        else:
            self.longitudes = {
                "femur": 0,
                "tibia": 0,
                "distancia_rodillas": 0
            }

    def calcular_longitudes(self):
        """Calcula las longitudes de los segmentos corporales"""
        # Factor de corrección por edad
        factor_correccion = 0.97 if self.edad > 50 else 1.0

        self.longitudes = {
            "femur": self.altura_m * PROPORCIONES[self.sexo.lower()]['altura_femur'] * factor_correccion,
            "tibia": self.altura_m * PROPORCIONES[self.sexo.lower()]['altura_tibia'] * factor_correccion,
            "distancia_rodillas": self.altura_m * PROPORCIONES[self.sexo.lower()]['distancia_rodillas'] * factor_correccion
        }
        self.umbrales_nivel = NIVEL_USUARIO[self.nivel_actividad]

    def validar_datos(self):
        """Valida que los datos del perfil sean correctos"""
        errores = []
        
        if not self.nombre or len(self.nombre.strip()) == 0:
            errores.append("El nombre es obligatorio")
            
        if self.sexo not in ['M', 'F']:
            errores.append("El sexo debe ser M o F")
            
        if self.edad <= 0 or self.edad > 120:
            errores.append("La edad debe estar entre 1 y 120 años")
            
        if self.altura_cm <= 0 or self.altura_cm > 250:
            errores.append("La altura debe estar entre 1 y 250 cm")
            
        if self.peso_kg <= 0 or self.peso_kg > 300:
            errores.append("El peso debe estar entre 1 y 300 kg")
            
        if self.nivel_actividad not in NIVEL_USUARIO:
            errores.append(f"El nivel de actividad debe ser uno de: {', '.join(NIVEL_USUARIO.keys())}")
            
        return errores

    def actualizar_datos(self, nombre=None, sexo=None, edad=None, altura_cm=None, peso_kg=None, nivel_actividad=None):
        """Actualiza los datos del perfil"""
        if nombre is not None:
            self.nombre = nombre
        if sexo is not None:
            self.sexo = sexo.upper()
        if edad is not None:
            self.edad = edad
        if altura_cm is not None:
            self.altura_cm = altura_cm
            self.altura_m = self.altura_cm / 100.0
        if peso_kg is not None:
            self.peso_kg = peso_kg
        if nivel_actividad is not None and nivel_actividad in NIVEL_USUARIO:
            self.nivel_actividad = nivel_actividad

        # Recalcular valores derivados
        self.imc = self.peso_kg / (self.altura_m ** 2) if self.altura_m > 0 else 0
        if self.sexo in ['M', 'F'] and self.altura_cm > 0:
            self.calcular_longitudes()

    def to_dict(self):
        """Convierte el perfil a diccionario para serialización"""
        return {
            'nombre': self.nombre,
            'sexo': self.sexo,
            'edad': self.edad,
            'altura_cm': self.altura_cm,
            'peso_kg': self.peso_kg,
            'nivel_actividad': self.nivel_actividad,
            'fecha_creacion': self.fecha_creacion,
            'altura_m': self.altura_m,
            'imc': self.imc,
            'longitudes': self.longitudes
        }

    @classmethod
    def from_dict(cls, data):
        """Crea un perfil desde un diccionario"""
        perfil = cls(
            nombre=data.get('nombre', ""),
            sexo=data.get('sexo', ""),
            edad=data.get('edad', 0),
            altura_cm=data.get('altura_cm', 0),
            peso_kg=data.get('peso_kg', 0),
            nivel_actividad=data.get('nivel_actividad', "")
        )
        perfil.fecha_creacion = data.get('fecha_creacion', perfil.fecha_creacion)
        return perfil

class ProfileManager:
    def __init__(self, profiles_file="perfiles_usuarios.json"):
        self.profiles_file = profiles_file
        self.current_profile = None

    def save_profile(self, perfil: UsuarioPerfil):
        """Guarda un perfil de usuario"""
        try:
            # Validar datos antes de guardar
            errores = perfil.validar_datos()
            if errores:
                return False, errores

            # Cargar perfiles existentes
            profiles = self.load_all_profiles()
            
            # Agregar o actualizar perfil
            profiles[perfil.nombre] = perfil.to_dict()
            
            # Guardar archivo
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=4, ensure_ascii=False)
            
            logging.info(f"Perfil de {perfil.nombre} guardado exitosamente")
            return True, []
            
        except Exception as e:
            error_msg = f"Error al guardar el perfil: {str(e)}"
            logging.error(error_msg)
            return False, [error_msg]

    def load_profile(self, nombre):
        """Carga un perfil específico por nombre"""
        try:
            profiles = self.load_all_profiles()
            
            if nombre in profiles:
                perfil = UsuarioPerfil.from_dict(profiles[nombre])
                self.current_profile = perfil
                logging.info(f"Perfil de {nombre} cargado exitosamente")
                return perfil, []
            else:
                error_msg = f"Perfil '{nombre}' no encontrado"
                logging.warning(error_msg)
                return None, [error_msg]
                
        except Exception as e:
            error_msg = f"Error al cargar el perfil: {str(e)}"
            logging.error(error_msg)
            return None, [error_msg]

    def load_all_profiles(self):
        """Carga todos los perfiles disponibles"""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logging.error(f"Error al cargar perfiles: {e}")
            return {}

    def get_profile_names(self):
        """Obtiene la lista de nombres de perfiles disponibles"""
        try:
            profiles = self.load_all_profiles()
            return list(profiles.keys())
        except Exception as e:
            logging.error(f"Error al obtener nombres de perfiles: {e}")
            return []

    def delete_profile(self, nombre):
        """Elimina un perfil"""
        try:
            profiles = self.load_all_profiles()
            
            if nombre in profiles:
                del profiles[nombre]
                
                with open(self.profiles_file, 'w', encoding='utf-8') as f:
                    json.dump(profiles, f, indent=4, ensure_ascii=False)
                
                logging.info(f"Perfil de {nombre} eliminado exitosamente")
                return True, []
            else:
                error_msg = f"Perfil '{nombre}' no encontrado"
                logging.warning(error_msg)
                return False, [error_msg]
                
        except Exception as e:
            error_msg = f"Error al eliminar el perfil: {str(e)}"
            logging.error(error_msg)
            return False, [error_msg]

    def create_default_profile(self, nombre="Usuario Demo"):
        """Crea un perfil por defecto para pruebas"""
        perfil = UsuarioPerfil(
            nombre=nombre,
            sexo="M",
            edad=25,
            altura_cm=175,
            peso_kg=70,
            nivel_actividad="intermedio"
        )
        
        success, errors = self.save_profile(perfil)
        if success:
            self.current_profile = perfil
            return perfil, []
        else:
            return None, errors

    def get_current_profile(self):
        """Obtiene el perfil actual"""
        return self.current_profile

    def set_current_profile(self, perfil: UsuarioPerfil):
        """Establece el perfil actual"""
        self.current_profile = perfil

# Funciones de utilidad para la aplicación móvil
def validate_user_input(nombre, sexo, edad, altura, peso, nivel):
    """Valida la entrada del usuario desde la interfaz móvil"""
    errores = []
    
    try:
        # Validar nombre
        if not nombre or len(nombre.strip()) == 0:
            errores.append("El nombre es obligatorio")
        
        # Validar sexo
        if sexo.upper() not in ['M', 'F', 'MASCULINO', 'FEMENINO', 'HOMBRE', 'MUJER']:
            errores.append("Seleccione un sexo válido")
        
        # Validar edad
        edad_int = int(edad)
        if edad_int <= 0 or edad_int > 120:
            errores.append("La edad debe estar entre 1 y 120 años")
            
        # Validar altura
        altura_float = float(altura)
        if altura_float <= 0 or altura_float > 250:
            errores.append("La altura debe estar entre 1 y 250 cm")
            
        # Validar peso
        peso_float = float(peso)
        if peso_float <= 0 or peso_float > 300:
            errores.append("El peso debe estar entre 1 y 300 kg")
            
        # Validar nivel
        if nivel not in NIVEL_USUARIO:
            errores.append(f"Seleccione un nivel válido: {', '.join(NIVEL_USUARIO.keys())}")
            
    except ValueError as e:
        errores.append("Verifique que los valores numéricos sean correctos")
    
    return errores

def normalize_gender(sexo_input):
    """Normaliza la entrada de género a M o F"""
    sexo_upper = sexo_input.upper().strip()
    
    if sexo_upper in ['M', 'MASCULINO', 'HOMBRE', 'MALE']:
        return 'M'
    elif sexo_upper in ['F', 'FEMENINO', 'MUJER', 'FEMALE']:
        return 'F'
    else:
        return sexo_upper

def get_imc_classification(imc):
    """Clasifica el IMC según estándares médicos"""
    if imc < 18.5:
        return "Bajo peso"
    elif imc < 25:
        return "Peso normal"
    elif imc < 30:
        return "Sobrepeso"
    else:
        return "Obesidad"

def save_session_results(perfil_nombre, resultados, filename=None):
    """Guarda los resultados de una sesión de análisis"""
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resultados_{perfil_nombre.replace(' ', '_')}_{timestamp}.json"
        
        # Agregar información del perfil y timestamp
        resultados_completos = {
            'perfil_usuario': perfil_nombre,
            'fecha_sesion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'resultados': resultados
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(resultados_completos, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Resultados guardados en {filename}")
        return True, filename
        
    except Exception as e:
        error_msg = f"Error al guardar resultados: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def load_session_history(perfil_nombre=None):
    """Carga el historial de sesiones"""
    try:
        import glob
        
        if perfil_nombre:
            pattern = f"resultados_{perfil_nombre.replace(' ', '_')}_*.json"
        else:
            pattern = "resultados_*.json"
        
        archivos = glob.glob(pattern)
        historial = []
        
        for archivo in sorted(archivos, reverse=True):  # Más recientes primero
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    historial.append({
                        'archivo': archivo,
                        'fecha': data.get('fecha_sesion', 'Desconocida'),
                        'perfil': data.get('perfil_usuario', 'Desconocido'),
                        'resultados': data.get('resultados', {})
                    })
            except Exception as e:
                logging.warning(f"Error cargando {archivo}: {e}")
                continue
        
        return historial, []
        
    except Exception as e:
        error_msg = f"Error cargando historial: {str(e)}"
        logging.error(error_msg)
        return [], [error_msg]
