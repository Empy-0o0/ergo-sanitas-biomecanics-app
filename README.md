# Ergo SaniTas SpA - Aplicación Móvil de Análisis Biomecánico

## Descripción

Aplicación móvil profesional desarrollada para **Ergo SaniTas SpA**, empresa chilena especializada en medicina deportiva. La aplicación proporciona análisis biomecánico en tiempo real de saltos verticales, ofreciendo retroalimentación técnica y métricas de rendimiento para atletas y profesionales de la salud.

## Características Principales

### 🏥 **Análisis Biomecánico Profesional**
- Detección de pose en tiempo real usando MediaPipe
- Análisis de ángulos articulares (rodilla, cadera, tobillo)
- Evaluación de técnica de salto con retroalimentación inmediata
- Cálculo de métricas de rendimiento (altura, potencia, tiempo de vuelo)

### 📊 **Tipos de Salto Soportados**
- **CMJ (Counter Movement Jump)**: Salto con contramovimiento
- **SQJ (Squat Jump)**: Salto desde posición estática
- **Abalakov**: Salto con uso de brazos

### 👤 **Gestión de Perfiles**
- Perfiles personalizados por usuario
- Cálculo de proporciones corporales
- Niveles de experiencia (principiante, intermedio, avanzado)
- Historial de sesiones y progreso

### 📱 **Interfaz Móvil Moderna**
- Diseño limpio y profesional
- Navegación intuitiva entre pantallas
- Retroalimentación visual en tiempo real
- Resultados detallados con recomendaciones

## Estructura del Proyecto

```
ergo-sanitas-app/
├── main.py                 # Aplicación principal Kivy
├── app.kv                  # Interfaz de usuario (Kivy Language)
├── jump_analyzer.py        # Motor de análisis biomecánico
├── profile_manager.py      # Gestión de perfiles de usuario
├── config_Saltos.yaml      # Parámetros biomecánicos
├── requirements.txt        # Dependencias del proyecto
├── README.md              # Documentación
└── TestSalto.py           # Código original de referencia
```

## Instalación y Configuración

### Requisitos del Sistema
- Python 3.8 o superior
- Cámara web o cámara de dispositivo móvil
- Sistema operativo: Windows, macOS, Linux, Android, iOS

### Instalación de Dependencias

```bash
# Clonar el repositorio
git clone <repository-url>
cd ergo-sanitas-app

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecución en Desarrollo

```bash
# Ejecutar la aplicación
python main.py
```

## Uso de la Aplicación

### 1. **Pantalla de Login**
- Seleccionar perfil existente o crear uno nuevo
- Opción de perfil demo para pruebas rápidas
- Validación de datos de usuario

### 2. **Pantalla Principal**
- Información del usuario actual
- Acceso a análisis de salto
- Historial de resultados
- Configuración de perfil

### 3. **Análisis de Salto**
- Calibración automática del sistema
- Retroalimentación en tiempo real
- Detección automática de fases del salto
- Métricas instantáneas

### 4. **Resultados**
- Resumen de la sesión
- Métricas de rendimiento
- Clasificación por nivel
- Recomendaciones personalizadas

## Parámetros Biomecánicos

La aplicación utiliza parámetros científicamente validados para el análisis:

### Rangos Óptimos de Movimiento (ROM)
- **Rodilla**: Flexión 70-90°, Extensión 160-170°
- **Cadera**: Flexión 90-100°, Extensión 170°
- **Tobillo**: Dorsiflexión 70-80°, Plantiflexión 160°

### Clasificación de Rendimiento
- **Hombres CMJ**: Bajo (<30cm), Medio (30-40cm), Avanzado (40-50cm), Elite (>50cm)
- **Mujeres CMJ**: Bajo (<22cm), Medio (22-30cm), Avanzado (30-38cm), Elite (>38cm)

## Arquitectura Técnica

### Componentes Principales

1. **JumpAnalyzer**: Motor de análisis biomecánico
   - Detección de pose con MediaPipe
   - Máquina de estados para fases del salto
   - Cálculo de métricas en tiempo real

2. **ProfileManager**: Gestión de usuarios
   - Almacenamiento local en JSON
   - Validación de datos
   - Cálculo de proporciones corporales

3. **Interfaz Kivy**: Aplicación móvil
   - Navegación entre pantallas
   - Widgets personalizados
   - Diseño responsivo

### Flujo de Datos

```
Usuario → Perfil → Calibración → Análisis → Resultados → Recomendaciones
```

## Características de Seguridad

- ✅ Validación de datos de entrada
- ✅ Manejo de errores robusto
- ✅ Logging de eventos y errores
- ✅ Almacenamiento local seguro
- ✅ Advertencias de seguridad para ejercicios

## Empaquetado para Móviles

### Android (usando Buildozer)

```bash
# Instalar buildozer
pip install buildozer

# Inicializar configuración
buildozer init

# Compilar APK
buildozer android debug
```

### iOS (usando kivy-ios)

```bash
# Instalar kivy-ios
pip install kivy-ios

# Compilar para iOS
toolchain build python3 kivy
```

## Personalización

### Modificar Parámetros Biomecánicos
Editar `config_Saltos.yaml` para ajustar:
- Rangos de movimiento óptimos
- Tolerancias por nivel de usuario
- Parámetros de detección de salto

### Personalizar Interfaz
Modificar `app.kv` para cambiar:
- Colores corporativos
- Tamaños de fuente
- Espaciado y diseño

## Soporte Técnico

### Logs y Depuración
Los logs se guardan automáticamente para diagnóstico:
- Eventos de calibración
- Errores de detección
- Métricas de rendimiento

### Problemas Comunes

1. **Cámara no detectada**
   - Verificar permisos de cámara
   - Comprobar conexión de hardware

2. **Calibración fallida**
   - Asegurar buena iluminación
   - Mantener posición estable
   - Verificar visibilidad completa del cuerpo

3. **Detección de pose inexacta**
   - Usar ropa ajustada
   - Fondo contrastante
   - Distancia adecuada de la cámara

## Contribución y Desarrollo

### Estructura de Código
- Código modular y bien documentado
- Separación clara de responsabilidades
- Manejo de errores consistente
- Logging detallado

### Testing
```bash
# Ejecutar tests
pytest tests/

# Con cobertura
pytest --cov=. tests/
```

## Licencia y Derechos

© 2024 **Ergo SaniTas SpA**  
Todos los derechos reservados.

Esta aplicación ha sido desarrollada específicamente para Ergo SaniTas SpA, empresa chilena especializada en medicina deportiva y análisis biomecánico.

## Contacto

**Ergo SaniTas SpA**  
Medicina Deportiva • Chile  
Tecnología para la Salud Deportiva

---

*Desarrollado con tecnología de vanguardia para el análisis biomecánico profesional*
