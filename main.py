import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.widget import Widget
from kivy.core.window import Window
import cv2
import numpy as np
import logging
from datetime import datetime
import threading
import time

# Importar nuestros módulos
from profile_manager import ProfileManager, UsuarioPerfil, validate_user_input, normalize_gender, get_imc_classification
from jump_analyzer import JumpAnalyzer, TipoSalto

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de ventana para desarrollo
Window.size = (400, 700)  # Simular pantalla móvil

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profile_manager = ProfileManager()
        self.build_ui()

    def build_ui(self):
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Header con logo de la empresa
        header_layout = BoxLayout(orientation='vertical', size_hint_y=0.3, spacing=10)
        
        # Logo/Título de la empresa
        title_label = Label(
            text='Ergo SaniTas SpA',
            font_size='28sp',
            bold=True,
            color=(0.2, 0.4, 0.8, 1),  # Azul corporativo
            size_hint_y=0.4
        )
        
        subtitle_label = Label(
            text='Análisis Biomecánico de Saltos',
            font_size='16sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=0.3
        )
        
        company_info = Label(
            text='Medicina Deportiva • Chile',
            font_size='14sp',
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=0.3
        )
        
        header_layout.add_widget(title_label)
        header_layout.add_widget(subtitle_label)
        header_layout.add_widget(company_info)
        
        # Formulario de login/selección de perfil
        form_layout = BoxLayout(orientation='vertical', size_hint_y=0.5, spacing=10)
        
        form_title = Label(
            text='Seleccionar Perfil de Usuario',
            font_size='18sp',
            bold=True,
            size_hint_y=0.2
        )
        
        # Spinner para seleccionar perfil existente
        self.profile_spinner = Spinner(
            text='Seleccionar perfil existente',
            values=self.profile_manager.get_profile_names(),
            size_hint_y=0.3
        )
        
        # Botones
        button_layout = BoxLayout(orientation='vertical', size_hint_y=0.5, spacing=10)
        
        login_button = Button(
            text='Usar Perfil Seleccionado',
            size_hint_y=0.33,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        login_button.bind(on_press=self.login_with_existing_profile)
        
        new_profile_button = Button(
            text='Crear Nuevo Perfil',
            size_hint_y=0.33,
            background_color=(0.2, 0.4, 0.8, 1)
        )
        new_profile_button.bind(on_press=self.create_new_profile)
        
        demo_button = Button(
            text='Usar Perfil Demo',
            size_hint_y=0.33,
            background_color=(0.8, 0.6, 0.2, 1)
        )
        demo_button.bind(on_press=self.use_demo_profile)
        
        button_layout.add_widget(login_button)
        button_layout.add_widget(new_profile_button)
        button_layout.add_widget(demo_button)
        
        form_layout.add_widget(form_title)
        form_layout.add_widget(self.profile_spinner)
        form_layout.add_widget(button_layout)
        
        # Footer
        footer_layout = BoxLayout(orientation='vertical', size_hint_y=0.2)
        footer_label = Label(
            text='© 2024 Ergo SaniTas SpA\nTecnología para la Salud Deportiva',
            font_size='12sp',
            color=(0.7, 0.7, 0.7, 1),
            halign='center'
        )
        footer_layout.add_widget(footer_label)
        
        main_layout.add_widget(header_layout)
        main_layout.add_widget(form_layout)
        main_layout.add_widget(footer_layout)
        
        self.add_widget(main_layout)

    def refresh_profiles(self):
        """Actualiza la lista de perfiles disponibles"""
        self.profile_spinner.values = self.profile_manager.get_profile_names()

    def login_with_existing_profile(self, instance):
        """Inicia sesión con un perfil existente"""
        if self.profile_spinner.text == 'Seleccionar perfil existente':
            self.show_error_popup("Por favor seleccione un perfil")
            return
        
        perfil, errores = self.profile_manager.load_profile(self.profile_spinner.text)
        if perfil:
            # Pasar el perfil a la aplicación principal
            app = App.get_running_app()
            app.set_current_profile(perfil)
            self.manager.current = 'home'
        else:
            self.show_error_popup("Error al cargar el perfil: " + ", ".join(errores))

    def create_new_profile(self, instance):
        """Abre el popup para crear un nuevo perfil"""
        self.show_profile_creation_popup()

    def use_demo_profile(self, instance):
        """Usa un perfil de demostración"""
        perfil, errores = self.profile_manager.create_default_profile("Usuario Demo")
        if perfil:
            app = App.get_running_app()
            app.set_current_profile(perfil)
            self.manager.current = 'home'
        else:
            self.show_error_popup("Error al crear perfil demo: " + ", ".join(errores))

    def show_profile_creation_popup(self):
        """Muestra el popup para crear un nuevo perfil"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Campos del formulario
        fields = {}
        
        # Nombre
        content.add_widget(Label(text='Nombre completo:', size_hint_y=0.1))
        fields['nombre'] = TextInput(multiline=False, size_hint_y=0.1)
        content.add_widget(fields['nombre'])
        
        # Sexo
        content.add_widget(Label(text='Sexo:', size_hint_y=0.1))
        fields['sexo'] = Spinner(text='Seleccionar', values=['Masculino', 'Femenino'], size_hint_y=0.1)
        content.add_widget(fields['sexo'])
        
        # Edad
        content.add_widget(Label(text='Edad (años):', size_hint_y=0.1))
        fields['edad'] = TextInput(multiline=False, input_filter='int', size_hint_y=0.1)
        content.add_widget(fields['edad'])
        
        # Altura
        content.add_widget(Label(text='Altura (cm):', size_hint_y=0.1))
        fields['altura'] = TextInput(multiline=False, input_filter='float', size_hint_y=0.1)
        content.add_widget(fields['altura'])
        
        # Peso
        content.add_widget(Label(text='Peso (kg):', size_hint_y=0.1))
        fields['peso'] = TextInput(multiline=False, input_filter='float', size_hint_y=0.1)
        content.add_widget(fields['peso'])
        
        # Nivel de actividad
        content.add_widget(Label(text='Nivel de actividad:', size_hint_y=0.1))
        fields['nivel'] = Spinner(
            text='Seleccionar', 
            values=['principiante', 'intermedio', 'avanzado'], 
            size_hint_y=0.1
        )
        content.add_widget(fields['nivel'])
        
        # Botones
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
        
        create_button = Button(text='Crear Perfil', background_color=(0.2, 0.6, 0.2, 1))
        cancel_button = Button(text='Cancelar', background_color=(0.8, 0.2, 0.2, 1))
        
        button_layout.add_widget(create_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='Crear Nuevo Perfil',
            content=content,
            size_hint=(0.9, 0.8)
        )
        
        def create_profile(instance):
            # Validar y crear perfil
            errores = validate_user_input(
                fields['nombre'].text,
                fields['sexo'].text,
                fields['edad'].text or "0",
                fields['altura'].text or "0",
                fields['peso'].text or "0",
                fields['nivel'].text
            )
            
            if errores:
                self.show_error_popup("Errores en el formulario:\n" + "\n".join(errores))
                return
            
            # Crear perfil
            perfil = UsuarioPerfil(
                nombre=fields['nombre'].text,
                sexo=normalize_gender(fields['sexo'].text),
                edad=int(fields['edad'].text),
                altura_cm=float(fields['altura'].text),
                peso_kg=float(fields['peso'].text),
                nivel_actividad=fields['nivel'].text
            )
            
            success, errores = self.profile_manager.save_profile(perfil)
            if success:
                popup.dismiss()
                self.refresh_profiles()
                app = App.get_running_app()
                app.set_current_profile(perfil)
                self.manager.current = 'home'
            else:
                self.show_error_popup("Error al crear perfil:\n" + "\n".join(errores))
        
        create_button.bind(on_press=create_profile)
        cancel_button.bind(on_press=popup.dismiss)
        
        popup.open()

    def show_error_popup(self, message):
        """Muestra un popup de error"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, text_size=(300, None), halign='center'))
        
        close_button = Button(text='Cerrar', size_hint_y=0.3)
        content.add_widget(close_button)
        
        popup = Popup(
            title='Error',
            content=content,
            size_hint=(0.8, 0.4)
        )
        
        close_button.bind(on_press=popup.dismiss)
        popup.open()

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Header
        header_layout = BoxLayout(orientation='vertical', size_hint_y=0.3, spacing=10)
        
        welcome_label = Label(
            text='Bienvenido a Ergo SaniTas',
            font_size='24sp',
            bold=True,
            color=(0.2, 0.4, 0.8, 1)
        )
        
        self.user_info_label = Label(
            text='Usuario: No seleccionado',
            font_size='16sp',
            color=(0.5, 0.5, 0.5, 1)
        )
        
        header_layout.add_widget(welcome_label)
        header_layout.add_widget(self.user_info_label)
        
        # Menú principal
        menu_layout = BoxLayout(orientation='vertical', size_hint_y=0.6, spacing=15)
        
        start_analysis_button = Button(
            text='Iniciar Análisis de Salto',
            font_size='18sp',
            size_hint_y=0.25,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        start_analysis_button.bind(on_press=self.start_jump_analysis)
        
        history_button = Button(
            text='Historial de Resultados',
            font_size='18sp',
            size_hint_y=0.25,
            background_color=(0.2, 0.4, 0.8, 1)
        )
        history_button.bind(on_press=self.show_history)
        
        profile_button = Button(
            text='Configurar Perfil',
            font_size='18sp',
            size_hint_y=0.25,
            background_color=(0.8, 0.6, 0.2, 1)
        )
        profile_button.bind(on_press=self.configure_profile)
        
        logout_button = Button(
            text='Cambiar Usuario',
            font_size='16sp',
            size_hint_y=0.25,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        logout_button.bind(on_press=self.logout)
        
        menu_layout.add_widget(start_analysis_button)
        menu_layout.add_widget(history_button)
        menu_layout.add_widget(profile_button)
        menu_layout.add_widget(logout_button)
        
        # Footer
        footer_layout = BoxLayout(orientation='vertical', size_hint_y=0.1)
        footer_label = Label(
            text='Tecnología avanzada para análisis biomecánico',
            font_size='12sp',
            color=(0.7, 0.7, 0.7, 1)
        )
        footer_layout.add_widget(footer_label)
        
        main_layout.add_widget(header_layout)
        main_layout.add_widget(menu_layout)
        main_layout.add_widget(footer_layout)
        
        self.add_widget(main_layout)

    def update_user_info(self, perfil):
        """Actualiza la información del usuario en pantalla"""
        if perfil:
            imc_class = get_imc_classification(perfil.imc)
            self.user_info_label.text = f'Usuario: {perfil.nombre}\nEdad: {perfil.edad} años | IMC: {perfil.imc:.1f} ({imc_class})'

    def start_jump_analysis(self, instance):
        """Inicia el análisis de salto"""
        app = App.get_running_app()
        if app.current_profile:
            self.manager.current = 'jump_analysis'
        else:
            self.show_error_popup("No hay perfil de usuario seleccionado")

    def show_history(self, instance):
        """Muestra el historial de resultados"""
        self.manager.current = 'results'

    def configure_profile(self, instance):
        """Configura el perfil del usuario"""
        # Por ahora, redirige al login para cambiar perfil
        self.manager.current = 'login'

    def logout(self, instance):
        """Cierra sesión y vuelve al login"""
        app = App.get_running_app()
        app.set_current_profile(None)
        self.manager.current = 'login'

    def show_error_popup(self, message):
        """Muestra un popup de error"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, text_size=(300, None), halign='center'))
        
        close_button = Button(text='Cerrar', size_hint_y=0.3)
        content.add_widget(close_button)
        
        popup = Popup(
            title='Error',
            content=content,
            size_hint=(0.8, 0.4)
        )
        
        close_button.bind(on_press=popup.dismiss)
        popup.open()

class JumpAnalysisScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.jump_analyzer = None
        self.camera_active = False
        self.analysis_active = False
        self.build_ui()

    def build_ui(self):
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Header con información del análisis
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        
        self.status_label = Label(
            text='Estado: Preparando...',
            font_size='16sp',
            bold=True
        )
        
        self.jump_counter_label = Label(
            text='Saltos: 0/0',
            font_size='16sp'
        )
        
        header_layout.add_widget(self.status_label)
        header_layout.add_widget(self.jump_counter_label)
        
        # Área de la cámara (simulada con un widget)
        self.camera_widget = Widget(size_hint_y=0.5)
        with self.camera_widget.canvas:
            Color(0.1, 0.1, 0.1, 1)
            self.camera_rect = Rectangle(size=self.camera_widget.size, pos=self.camera_widget.pos)
        
        self.camera_widget.bind(size=self.update_camera_rect, pos=self.update_camera_rect)
        
        # Información de análisis en tiempo real
        info_layout = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=5)
        
        self.height_label = Label(text='Altura de salto: 0.00m', font_size='14sp')
        self.power_label = Label(text='Potencia: 0%', font_size='14sp')
        self.feedback_label = Label(
            text='Feedback: Posiciónese frente a la cámara',
            font_size='12sp',
            text_size=(None, None),
            halign='center'
        )
        
        info_layout.add_widget(self.height_label)
        info_layout.add_widget(self.power_label)
        info_layout.add_widget(self.feedback_label)
        
        # Controles
        control_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        
        self.start_button = Button(
            text='Iniciar Análisis',
            background_color=(0.2, 0.6, 0.2, 1)
        )
        self.start_button.bind(on_press=self.toggle_analysis)
        
        self.calibrate_button = Button(
            text='Recalibrar',
            background_color=(0.8, 0.6, 0.2, 1)
        )
        self.calibrate_button.bind(on_press=self.recalibrate)
        
        back_button = Button(
            text='Volver',
            background_color=(0.8, 0.2, 0.2, 1)
        )
        back_button.bind(on_press=self.go_back)
        
        control_layout.add_widget(self.start_button)
        control_layout.add_widget(self.calibrate_button)
        control_layout.add_widget(back_button)
        
        main_layout.add_widget(header_layout)
        main_layout.add_widget(self.camera_widget)
        main_layout.add_widget(info_layout)
        main_layout.add_widget(control_layout)
        
        self.add_widget(main_layout)

    def update_camera_rect(self, instance, value):
        """Actualiza el rectángulo de la cámara"""
        self.camera_rect.size = instance.size
        self.camera_rect.pos = instance.pos

    def on_enter(self):
        """Se ejecuta cuando se entra a la pantalla"""
        app = App.get_running_app()
        if app.current_profile:
            self.jump_analyzer = JumpAnalyzer(app.current_profile)
            self.status_label.text = f'Estado: Listo - {app.current_profile.nombre}'

    def toggle_analysis(self, instance):
        """Inicia o detiene el análisis"""
        if not self.analysis_active:
            self.start_analysis()
        else:
            self.stop_analysis()

    def start_analysis(self):
        """Inicia el análisis de salto"""
        if not self.jump_analyzer:
            self.show_error_popup("Error: No hay analizador inicializado")
            return
        
        self.analysis_active = True
        self.start_button.text = 'Detener Análisis'
        self.start_button.background_color = (0.8, 0.2, 0.2, 1)
        self.status_label.text = 'Estado: Analizando...'
        
        # Simular análisis (en una implementación real, aquí se procesarían frames de cámara)
        self.analysis_event = Clock.schedule_interval(self.simulate_analysis, 1.0/30.0)  # 30 FPS

    def stop_analysis(self):
        """Detiene el análisis"""
        self.analysis_active = False
        self.start_button.text = 'Iniciar Análisis'
        self.start_button.background_color = (0.2, 0.6, 0.2, 1)
        self.status_label.text = 'Estado: Detenido'
        
        if hasattr(self, 'analysis_event'):
            self.analysis_event.cancel()
        
        # Mostrar resultados si hay saltos completados
        if self.jump_analyzer and self.jump_analyzer.contador > 0:
            self.show_results()

    def simulate_analysis(self, dt):
        """Simula el análisis de salto (para demostración)"""
        if not self.jump_analyzer:
            return False
        
        # Simular datos de análisis
        import random
        
        # Actualizar contadores
        self.jump_counter_label.text = f'Saltos: {self.jump_analyzer.correctas}/{self.jump_analyzer.contador}'
        
        # Simular altura de salto
        if random.random() < 0.1:  # 10% de probabilidad de "salto"
            altura_simulada = random.uniform(0.15, 0.45)
            self.jump_analyzer.jump_height_m = altura_simulada
            self.jump_analyzer.contador += 1
            if random.random() < 0.8:  # 80% de saltos "correctos"
                self.jump_analyzer.correctas += 1
        
        self.height_label.text = f'Altura de salto: {self.jump_analyzer.jump_height_m:.2f}m'
        
        # Simular potencia
        potencia_simulada = random.uniform(40, 90)
        self.power_label.text = f'Potencia: {potencia_simulada:.0f}%'
        
        # Simular feedback
        feedbacks = [
            'Mantenga posición estable',
            'Flexione más las rodillas',
            '¡Buen salto!',
            'Aterrizaje suave',
            'Preparado para el siguiente'
        ]
        self.feedback_label.text = f'Feedback: {random.choice(feedbacks)}'
        
        return True

    def recalibrate(self, instance):
        """Recalibra el sistema"""
        if self.jump_analyzer:
            self.jump_analyzer.reset_session()
            self.status_label.text = 'Estado: Recalibrado'
            self.jump_counter_label.text = 'Saltos: 0/0'
            self.height_label.text = 'Altura de salto: 0.00m'
            self.power_label.text = 'Potencia: 0%'

    def show_results(self):
        """Muestra los resultados del análisis"""
        if self.jump_analyzer:
            resultados = self.jump_analyzer.get_results()
            
            # Cambiar a pantalla de resultados
            results_screen = self.manager.get_screen('results')
            results_screen.display_results(resultados)
            self.manager.current = 'results'

    def go_back(self):
        """Vuelve a la pantalla principal"""
        if self.analysis_active:
            self.stop_analysis()
        self.manager.current = 'home'

    def show_error_popup(self, message):
        """Muestra un popup de error"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, text_size=(300, None), halign='center'))
        
        close_button = Button(text='Cerrar', size_hint_y=0.3)
        content.add_widget(close_button)
        
        popup = Popup(
            title='Error',
            content=content,
            size_hint=(0.8, 0.4)
        )
        
        close_button.bind(on_press=popup.dismiss)
        popup.open()

class ResultsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Header
        header_label = Label(
            text='Resultados del Análisis',
            font_size='22sp',
            bold=True,
            size_hint_y=0.1,
            color=(0.2, 0.4, 0.8, 1)
        )
        
        # Área de resultados (scroll)
        scroll = ScrollView(size_hint_y=0.75)
        self.results_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        
        scroll.add_widget(self.results_layout)
        
        # Botones de control
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        
        new_analysis_button = Button(
            text='Nuevo Análisis',
            background_color=(0.2, 0.6, 0.2, 1)
        )
        new_analysis_button.bind(on_press=self.new_analysis)
        
        home_button = Button(
            text='Menú Principal',
            background_color=(0.2, 0.4, 0.8, 1)
        )
        home_button.bind(on_press=self.go_home)
        
        button_layout.add_widget(new_analysis_button)
        button_layout.add_widget(home_button)
        
        main_layout.add_widget(header_label)
        main_layout.add_widget(scroll)
        main_layout.add_widget(button_layout)
        
        self.add_widget(main_layout)

    def display_results(self, resultados):
        """Muestra los resultados del análisis"""
        # Limpiar resultados anteriores
        self.results_layout.clear_widgets()
        
        # Información general
        general_info = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=200)
        
        general_info.add_widget(Label(
            text=f'Total de saltos: {resultados.get("total", 0)}',
            font_size='16sp',
            size_hint_y=None,
            height=30
        ))
        
        general_info.add_widget(Label(
            text=f'Saltos correctos: {resultados.get("correctas", 0)}',
            font_size='16sp',
            size_hint_y=None,
            height=30
        ))
        
        general_info.add_widget(Label(
            text=f'Precisión: {resultados.get("precision", 0):.1f}%',
            font_size='16sp',
            size_hint_y=None,
            height=30
        ))
        
        general_info.add_widget(Label(
            text=f'Altura promedio: {resultados.get("altura_salto_promedio", 0)*100:.1f} cm',
            font_size='16sp',
            size_hint_y=None,
            height=30
        ))
        
        general_info.add_widget(Label(
            text=f'Clasificación: {resultados.get("clasificacion", "N/A")}',
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=30
        ))
        
        general_info.add_widget(Label(
            text=f'Evaluación: {resultados.get("evaluacion_rendimiento", "N/A")}',
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=30
        ))
        
        self.results_layout.add_widget(general_info)
        
        # Recomendaciones
        if resultados.get("recomendaciones"):
            rec_title = Label(
                text='Recomendaciones:',
                font_size='18sp',
                bold=True,
                size_hint_y=None,
                height=40
            )
            self.results_layout.add_widget(rec_title)
            
            for i, rec in enumerate(resultados["recomendaciones"][:5], 1):  # Máximo 5 recomendaciones
                rec_label = Label(
                    text=f'{i}. {rec}',
                    font_size='14sp',
                    text_size=(350, None),
                    halign='left',
                    size_hint_y=None,
                    height=50
                )
                self.results_layout.add_widget(rec_label)

    def new_analysis(self, instance):
        """Inicia un nuevo análisis"""
        self.manager.current = 'jump_analysis'

    def go_home(self, instance):
        """Vuelve al menú principal"""
        self.manager.current = 'home'

class ErgoSaniTasApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_profile = None

    def build(self):
        # Crear el gestor de pantallas
        sm = ScreenManager()
        
        # Agregar pantallas
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(JumpAnalysisScreen(name='jump_analysis'))
        sm.add_widget(ResultsScreen(name='results'))
        
        return sm

    def set_current_profile(self, perfil):
        """Establece el perfil actual"""
        self.current_profile = perfil
        
        # Actualizar información en la pantalla de inicio
        if perfil:
            home_screen = self.root.get_screen('home')
            home_screen.update_user_info(perfil)

    def get_current_profile(self):
        """Obtiene el perfil actual"""
        return self.current_profile

    def on_start(self):
        """Se ejecuta cuando la aplicación inicia"""
        logging.info("Aplicación Ergo SaniTas iniciada")

    def on_stop(self):
        """Se ejecuta cuando la aplicación se cierra"""
        logging.info("Aplicación Ergo SaniTas cerrada")

if __name__ == '__main__':
    ErgoSaniTasApp().run()
