#!/usr/bin/env python3
"""
Script de prueba para la aplicación Ergo SaniTas SpA
Verifica que todos los componentes funcionen correctamente
"""

import sys
import os
import logging
from datetime import datetime

# Configurar logging para pruebas
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_imports():
    """Prueba que todos los módulos se importen correctamente"""
    print("🔍 Probando importación de módulos...")
    
    try:
        # Módulos principales de la aplicación
        from profile_manager import ProfileManager, UsuarioPerfil, validate_user_input
        from jump_analyzer import JumpAnalyzer, TipoSalto, EstadoSalto
        print("✅ Módulos principales importados correctamente")
        
        # Dependencias externas críticas
        import cv2
        print(f"✅ OpenCV versión: {cv2.__version__}")
        
        import mediapipe as mp
        print("✅ MediaPipe importado correctamente")
        
        import kivy
        print(f"✅ Kivy versión: {kivy.__version__}")
        
        import numpy as np
        print(f"✅ NumPy versión: {np.__version__}")
        
        import yaml
        print("✅ PyYAML importado correctamente")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_config_file():
    """Prueba que el archivo de configuración sea válido"""
    print("\n🔍 Probando archivo de configuración...")
    
    try:
        import yaml
        
        if not os.path.exists('config_Saltos.yaml'):
            print("❌ Archivo config_Saltos.yaml no encontrado")
            return False
        
        with open('config_Saltos.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Verificar secciones principales
        required_sections = ['proporciones', 'rom_optimo_salto', 'parametros_salto', 'nivel_usuario']
        for section in required_sections:
            if section not in config:
                print(f"❌ Sección '{section}' faltante en configuración")
                return False
        
        print("✅ Archivo de configuración válido")
        return True
        
    except Exception as e:
        print(f"❌ Error al leer configuración: {e}")
        return False

def test_profile_manager():
    """Prueba el gestor de perfiles"""
    print("\n🔍 Probando gestor de perfiles...")
    
    try:
        from profile_manager import ProfileManager, UsuarioPerfil
        
        # Crear gestor de perfiles
        pm = ProfileManager("test_profiles.json")
        
        # Crear perfil de prueba
        perfil = UsuarioPerfil(
            nombre="Usuario Test",
            sexo="M",
            edad=25,
            altura_cm=175,
            peso_kg=70,
            nivel_actividad="intermedio"
        )
        
        # Validar perfil
        errores = perfil.validar_datos()
        if errores:
            print(f"❌ Errores en validación de perfil: {errores}")
            return False
        
        # Guardar perfil
        success, errores = pm.save_profile(perfil)
        if not success:
            print(f"❌ Error al guardar perfil: {errores}")
            return False
        
        # Cargar perfil
        perfil_cargado, errores = pm.load_profile("Usuario Test")
        if not perfil_cargado:
            print(f"❌ Error al cargar perfil: {errores}")
            return False
        
        # Verificar datos
        if perfil_cargado.nombre != "Usuario Test":
            print("❌ Datos del perfil no coinciden")
            return False
        
        # Limpiar archivo de prueba
        if os.path.exists("test_profiles.json"):
            os.remove("test_profiles.json")
        
        print("✅ Gestor de perfiles funcional")
        return True
        
    except Exception as e:
        print(f"❌ Error en gestor de perfiles: {e}")
        return False

def test_jump_analyzer():
    """Prueba el analizador de saltos"""
    print("\n🔍 Probando analizador de saltos...")
    
    try:
        from profile_manager import UsuarioPerfil
        from jump_analyzer import JumpAnalyzer, TipoSalto
        
        # Crear perfil de prueba
        perfil = UsuarioPerfil(
            nombre="Test User",
            sexo="M",
            edad=25,
            altura_cm=175,
            peso_kg=70,
            nivel_actividad="intermedio"
        )
        
        # Crear analizador
        analyzer = JumpAnalyzer(perfil)
        
        # Verificar inicialización
        if analyzer.usuario.nombre != "Test User":
            print("❌ Error en inicialización del analizador")
            return False
        
        # Probar configuración de tipo de salto
        analyzer.set_tipo_salto(TipoSalto.CMJ)
        if analyzer.tipo_salto != TipoSalto.CMJ:
            print("❌ Error al configurar tipo de salto")
            return False
        
        # Probar reset de sesión
        analyzer.reset_session()
        if analyzer.contador != 0 or analyzer.correctas != 0:
            print("❌ Error en reset de sesión")
            return False
        
        print("✅ Analizador de saltos funcional")
        return True
        
    except Exception as e:
        print(f"❌ Error en analizador de saltos: {e}")
        return False

def test_kivy_app():
    """Prueba básica de la aplicación Kivy"""
    print("\n🔍 Probando aplicación Kivy...")
    
    try:
        # Importar sin ejecutar la aplicación
        import main
        
        # Verificar que la clase principal existe
        if not hasattr(main, 'ErgoSaniTasApp'):
            print("❌ Clase ErgoSaniTasApp no encontrada")
            return False
        
        print("✅ Aplicación Kivy lista para ejecutar")
        return True
        
    except Exception as e:
        print(f"❌ Error en aplicación Kivy: {e}")
        return False

def test_camera_availability():
    """Prueba disponibilidad de cámara"""
    print("\n🔍 Probando disponibilidad de cámara...")
    
    try:
        import cv2
        
        # Intentar abrir cámara
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("⚠️  Cámara no disponible (normal en entornos sin cámara)")
            return True  # No es un error crítico
        
        # Leer un frame
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            print("✅ Cámara disponible y funcional")
        else:
            print("⚠️  Cámara detectada pero no funcional")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Error al probar cámara: {e}")
        return True  # No es crítico para la prueba

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS DE ERGO SANITAS APP")
    print("=" * 50)
    
    tests = [
        ("Importación de módulos", test_imports),
        ("Archivo de configuración", test_config_file),
        ("Gestor de perfiles", test_profile_manager),
        ("Analizador de saltos", test_jump_analyzer),
        ("Aplicación Kivy", test_kivy_app),
        ("Disponibilidad de cámara", test_camera_availability),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ Falló: {test_name}")
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESUMEN DE PRUEBAS:")
    print(f"✅ Pasaron: {passed}/{total}")
    print(f"❌ Fallaron: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("La aplicación Ergo SaniTas está lista para usar.")
        return True
    else:
        print(f"\n⚠️  {total - passed} prueba(s) fallaron.")
        print("Revise los errores antes de usar la aplicación.")
        return False

def print_system_info():
    """Imprime información del sistema"""
    print("\n💻 INFORMACIÓN DEL SISTEMA:")
    print("-" * 30)
    print(f"Python: {sys.version}")
    print(f"Plataforma: {sys.platform}")
    print(f"Directorio actual: {os.getcwd()}")
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("🏥 ERGO SANITAS SPA - PRUEBAS DE APLICACIÓN")
    print("Análisis Biomecánico de Saltos")
    print("Medicina Deportiva • Chile")
    
    print_system_info()
    
    success = run_all_tests()
    
    if success:
        print("\n🚀 Para ejecutar la aplicación:")
        print("   python3 main.py")
        print("\n📱 Para compilar APK:")
        print("   ./build_android.sh")
        sys.exit(0)
    else:
        print("\n🔧 Corrija los errores antes de continuar.")
        sys.exit(1)
