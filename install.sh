#!/bin/bash

# Script de instalación para Ergo SaniTas SpA
# Aplicación de Análisis Biomecánico de Saltos

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con colores
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Header principal
clear
print_header "ERGO SANITAS SPA - INSTALADOR"
echo -e "${BLUE}Aplicación de Análisis Biomecánico de Saltos${NC}"
echo -e "${BLUE}Medicina Deportiva • Chile${NC}"
echo ""

# Verificar sistema operativo
print_message "Detectando sistema operativo..."
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac
print_message "Sistema detectado: ${MACHINE}"

# Verificar Python
print_message "Verificando instalación de Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_message "Python encontrado: ${PYTHON_VERSION}"
    
    # Verificar versión mínima (3.8)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        print_message "Versión de Python compatible ✓"
    else
        print_error "Se requiere Python 3.8 o superior"
        exit 1
    fi
else
    print_error "Python 3 no encontrado. Por favor instale Python 3.8 o superior"
    exit 1
fi

# Verificar pip
print_message "Verificando pip..."
if command -v pip3 &> /dev/null; then
    print_message "pip3 encontrado ✓"
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    print_message "pip encontrado ✓"
    PIP_CMD="pip"
else
    print_error "pip no encontrado. Por favor instale pip"
    exit 1
fi

# Crear entorno virtual
print_message "Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_message "Entorno virtual creado ✓"
else
    print_warning "Entorno virtual ya existe"
fi

# Activar entorno virtual
print_message "Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
print_message "Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias del sistema (Linux)
if [ "$MACHINE" = "Linux" ]; then
    print_message "Instalando dependencias del sistema para Linux..."
    
    # Detectar distribución
    if command -v apt-get &> /dev/null; then
        print_message "Detectado sistema basado en Debian/Ubuntu"
        sudo apt-get update
        sudo apt-get install -y \
            python3-dev \
            python3-pip \
            build-essential \
            libgl1-mesa-glx \
            libglib2.0-0 \
            libsm6 \
            libxext6 \
            libxrender-dev \
            libgomp1 \
            libgtk-3-dev \
            libsdl2-dev \
            libsdl2-image-dev \
            libsdl2-mixer-dev \
            libsdl2-ttf-dev \
            libportmidi-dev \
            libswscale-dev \
            libavformat-dev \
            libavcodec-dev \
            zlib1g-dev
    elif command -v yum &> /dev/null; then
        print_message "Detectado sistema basado en RedHat/CentOS"
        sudo yum install -y \
            python3-devel \
            gcc \
            gcc-c++ \
            make \
            mesa-libGL \
            gtk3-devel \
            SDL2-devel \
            SDL2_image-devel \
            SDL2_mixer-devel \
            SDL2_ttf-devel
    fi
fi

# Instalar dependencias de Python
print_message "Instalando dependencias de Python..."
pip install -r requirements.txt

# Verificar instalación de OpenCV
print_message "Verificando instalación de OpenCV..."
python3 -c "import cv2; print(f'OpenCV versión: {cv2.__version__}')" || {
    print_error "Error al importar OpenCV"
    exit 1
}

# Verificar instalación de MediaPipe
print_message "Verificando instalación de MediaPipe..."
python3 -c "import mediapipe; print('MediaPipe instalado correctamente')" || {
    print_error "Error al importar MediaPipe"
    exit 1
}

# Verificar instalación de Kivy
print_message "Verificando instalación de Kivy..."
python3 -c "import kivy; print(f'Kivy versión: {kivy.__version__}')" || {
    print_error "Error al importar Kivy"
    exit 1
}

# Crear directorios necesarios
print_message "Creando directorios necesarios..."
mkdir -p logs
mkdir -p data/profiles
mkdir -p data/results
mkdir -p data/sessions

# Verificar archivos de configuración
print_message "Verificando archivos de configuración..."
if [ ! -f "config_Saltos.yaml" ]; then
    print_error "Archivo config_Saltos.yaml no encontrado"
    exit 1
else
    print_message "Configuración biomecánica encontrada ✓"
fi

# Crear script de ejecución
print_message "Creando script de ejecución..."
cat > run_app.sh << 'EOF'
#!/bin/bash
# Script para ejecutar Ergo SaniTas App

# Activar entorno virtual
source venv/bin/activate

# Ejecutar aplicación
python3 main.py

# Desactivar entorno virtual al salir
deactivate
EOF

chmod +x run_app.sh
print_message "Script de ejecución creado ✓"

# Crear script para desarrollo móvil
print_message "Creando herramientas de desarrollo móvil..."
cat > build_android.sh << 'EOF'
#!/bin/bash
# Script para compilar APK de Android

echo "Compilando aplicación para Android..."

# Activar entorno virtual
source venv/bin/activate

# Verificar buildozer
if ! command -v buildozer &> /dev/null; then
    echo "Instalando buildozer..."
    pip install buildozer
fi

# Compilar APK debug
buildozer android debug

echo "APK generado en bin/"
EOF

chmod +x build_android.sh

# Prueba rápida de la aplicación
print_message "Ejecutando prueba rápida..."
python3 -c "
import sys
sys.path.append('.')
from profile_manager import ProfileManager
from jump_analyzer import JumpAnalyzer, TipoSalto

print('✓ Módulos importados correctamente')

# Crear perfil de prueba
pm = ProfileManager()
perfil, errores = pm.create_default_profile('Test User')
if perfil:
    print('✓ Gestión de perfiles funcional')
else:
    print('✗ Error en gestión de perfiles')

print('✓ Prueba básica completada')
"

# Mensaje final
print_header "INSTALACIÓN COMPLETADA"
echo ""
print_message "La aplicación Ergo SaniTas ha sido instalada correctamente"
echo ""
echo -e "${BLUE}Para ejecutar la aplicación:${NC}"
echo -e "  ${GREEN}./run_app.sh${NC}"
echo ""
echo -e "${BLUE}Para compilar APK de Android:${NC}"
echo -e "  ${GREEN}./build_android.sh${NC}"
echo ""
echo -e "${BLUE}Para desarrollo:${NC}"
echo -e "  ${GREEN}source venv/bin/activate${NC}"
echo -e "  ${GREEN}python3 main.py${NC}"
echo ""
echo -e "${BLUE}Archivos importantes:${NC}"
echo -e "  • ${YELLOW}config_Saltos.yaml${NC} - Parámetros biomecánicos"
echo -e "  • ${YELLOW}main.py${NC} - Aplicación principal"
echo -e "  • ${YELLOW}README.md${NC} - Documentación completa"
echo ""
print_message "¡Listo para usar!"
echo -e "${BLUE}© 2024 Ergo SaniTas SpA - Medicina Deportiva${NC}"
