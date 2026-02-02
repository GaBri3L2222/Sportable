#!/usr/bin/env -P /usr/bin:/usr/local/bin python3 -B
# coding: utf-8

#
#  Interface_graphique.py
#  Interface_graphique
#  Created by Sportable & Co on 2026/01/09
#
# "no description"
#
import ingescape as igs
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QSpinBox, QLineEdit, QListWidget, 
                             QListWidgetItem, QStackedWidget, QFormLayout, QDialog,
                             QComboBox, QFrame, QScrollArea, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QPointF
from PyQt5.QtGui import QFont, QPixmap, QColor, QIcon, QPainter, QPen, QBrush
from PyQt5.QtWidgets import QApplication
import json
import threading


class SkeletonWidget(QWidget):
    """Widget to draw the skeleton from MediaPipe landmarks"""
    
    # MediaPipe Pose connections
    POSE_CONNECTIONS = [
        # Face
        (0, 1), (1, 2), (2, 3), (3, 7),  # Left eye to left ear
        (0, 4), (4, 5), (5, 6), (6, 8),  # Right eye to right ear
        (9, 10),  # Mouth
        
        # Torso
        (11, 12),  # Shoulders
        (11, 23), (12, 24),  # Shoulders to hips
        (23, 24),  # Hips
        
        # Left arm
        (11, 13), (13, 15),  # Shoulder to elbow to wrist
        (15, 17), (15, 19), (15, 21),  # Wrist to fingers
        (17, 19),  # Pinky to index
        
        # Right arm
        (12, 14), (14, 16),  # Shoulder to elbow to wrist
        (16, 18), (16, 20), (16, 22),  # Wrist to fingers
        (18, 20),  # Pinky to index
        
        # Left leg
        (23, 25), (25, 27),  # Hip to knee to ankle
        (27, 29), (27, 31),  # Ankle to heel and foot index
        (29, 31),  # Heel to foot index
        
        # Right leg
        (24, 26), (26, 28),  # Hip to knee to ankle
        (28, 30), (28, 32),  # Ankle to heel and foot index
        (30, 32),  # Heel to foot index
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.landmarks = []
        self.feedback = ""
        self.stage = ""
        self.setMinimumSize(400, 500)
        
    def set_skeleton_data(self, skeleton_json):
        """Parse and set skeleton data from JSON"""
        try:
            data = json.loads(skeleton_json)
            self.landmarks = data.get("landmarks", [])
            self.feedback = data.get("feedback", "")
            self.stage = data.get("stage", "")
            self.update()  # Trigger repaint
        except json.JSONDecodeError:
            self.landmarks = []
            self.feedback = "Erreur de décodage JSON"
            self.update()
    
    def paintEvent(self, event):
        """Draw the skeleton"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        if not self.landmarks:
            # Draw "waiting" message
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(self.rect(), Qt.AlignCenter, "En attente du squelette...")
            return
        
        # Calculate scaling to fit the skeleton in the widget
        width = self.width()
        height = self.height()
        padding = 40
        
        # Find bounds of landmarks (using x and y only, ignoring z)
        x_coords = [lm['x'] for lm in self.landmarks if lm.get('visibility', 0) > 0.5]
        y_coords = [lm['y'] for lm in self.landmarks if lm.get('visibility', 0) > 0.5]
        
        if not x_coords or not y_coords:
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(self.rect(), Qt.AlignCenter, "Aucun point visible")
            return
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # Calculate scale and offset
        data_width = max_x - min_x
        data_height = max_y - min_y
        
        if data_width == 0 or data_height == 0:
            return
        
        scale_x = (width - 2 * padding) / data_width
        scale_y = (height - 2 * padding) / data_height
        scale = min(scale_x, scale_y)
        
        offset_x = padding - min_x * scale + (width - 2 * padding - data_width * scale) / 2
        offset_y = padding - min_y * scale + (height - 2 * padding - data_height * scale) / 2
        
        def transform_point(landmark):
            """Transform landmark coordinates to widget coordinates"""
            x = landmark['x'] * scale + offset_x
            y = landmark['y'] * scale + offset_y
            return QPointF(x, y)
        
        # Draw connections
        pen = QPen(QColor(70, 130, 180), 3)  # Steel blue
        painter.setPen(pen)
        
        for connection in self.POSE_CONNECTIONS:
            start_idx, end_idx = connection
            if start_idx < len(self.landmarks) and end_idx < len(self.landmarks):
                start_lm = self.landmarks[start_idx]
                end_lm = self.landmarks[end_idx]
                
                # Only draw if both points are visible
                if start_lm.get('visibility', 0) > 0.5 and end_lm.get('visibility', 0) > 0.5:
                    start_point = transform_point(start_lm)
                    end_point = transform_point(end_lm)
                    painter.drawLine(start_point, end_point)
        
        # Draw landmarks
        for i, landmark in enumerate(self.landmarks):
            visibility = landmark.get('visibility', 0)
            if visibility > 0.5:
                point = transform_point(landmark)
                
                # Color code by body part
                if i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:  # Face
                    color = QColor(255, 100, 100)  # Red
                elif i in [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]:  # Arms
                    color = QColor(100, 255, 100)  # Green
                elif i in [23, 24]:  # Hips
                    color = QColor(255, 255, 100)  # Yellow
                else:  # Legs
                    color = QColor(100, 100, 255)  # Blue
                
                # Adjust opacity based on visibility
                color.setAlpha(int(255 * visibility))
                
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor(50, 50, 50), 1))
                painter.drawEllipse(point, 5, 5)
        
        # Draw stage and feedback info at the bottom
        painter.setPen(QColor(50, 50, 50))
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        
        info_text = f"Stage: {self.stage}"
        if self.feedback:
            info_text += f" | {self.feedback}"
        
        painter.drawText(10, height - 10, info_text)


class SignalBridge(QObject):
    """Bridge to emit signals from callbacks"""
    update_ui = pyqtSignal()
    update_squelette = pyqtSignal(str)
    update_vision_state = pyqtSignal(bool)
    update_feedback = pyqtSignal(str)
    update_rep_remaining = pyqtSignal(int)
    update_set_remaining = pyqtSignal(int)
    update_rest_time = pyqtSignal(int)
    update_current_exercice = pyqtSignal(str)


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Interface_graphique(metaclass=Singleton):
    def __init__(self):
        # inputs
        self.SqueletteI = None
        self.Vision_StateI = None
        self.Current_ExerciceI = None
        self.Rep_RemainingI = None
        self.Set_RemainingI = None
        self.Rest_Time_RemainingI = None
        self.Session_StateI = None
        self.FeedbackI = None
        
        # GUI
        self.window = None
        self.signal_bridge = SignalBridge()
        self.exercises = []  # List of exercises: {"name": str, "reps": int, "sets": int}
        self.current_exercise_index = 0
        
    def initialize_gui(self):
        """Initialize and show the GUI"""
        with open("style.qss", "r") as f:
            style = f.read()
    
        app = QApplication.instance()
        if app:
            app.setStyleSheet(style)
    
        self.window = WorkoutWindow(self)
        self.window.show()
        self.signal_bridge.update_ui.connect(self.window.update_display)
        self.signal_bridge.update_squelette.connect(self.window.update_squelette_display)
        self.signal_bridge.update_vision_state.connect(self.window.update_vision_state_display)
        # Connect feedback signal if it exists
        if hasattr(self.signal_bridge, 'update_feedback'):
            self.signal_bridge.update_feedback.connect(self.window.update_feedback_display)
        # Connect progress signals
        if hasattr(self.signal_bridge, 'update_rep_remaining'):
            self.signal_bridge.update_rep_remaining.connect(self.window.update_reps)
        if hasattr(self.signal_bridge, 'update_set_remaining'):
            self.signal_bridge.update_set_remaining.connect(self.window.update_sets)
        if hasattr(self.signal_bridge, 'update_rest_time'):
            self.signal_bridge.update_rest_time.connect(self.window.update_rest_time)
        if hasattr(self.signal_bridge, 'update_current_exercice'):
            self.signal_bridge.update_current_exercice.connect(self.window.update_current_exercice_display)
            
    def on_exercice_added(self, sender_agent_name, sender_agent_uuid, exercise_id):
        """Service callback when an exercise is added in Moteur"""
        print(f"Received exercice added with ID: {exercise_id}")
        self.exercises[-1]["id"] = exercise_id
    
    
    def add_exercise(self, exercise_name, reps, sets):
        result = igs.service_call("Moteur", "addExercice", (), "")
        print(f"Exercise ID: {id}")
        """Add exercise to the list"""
        self.exercises.append({
            "type": "exercice",
            "nom": exercise_name,
            "series": sets,
            "repetitions": reps,
            "id": result,
            "done": "false"
        })
        if self.window:
            self.window.update_exercise_list()
            

    
    def remove_exercise(self, index):
            """Supprime un élément (exercice ou pause)"""
            if 0 <= index < len(self.exercises):
                item = self.exercises.pop(index)
                try:
                    elem_id = item.get("id")
                    print(f"Removing element with ID: {elem_id}")
                    if item.get("type") == "pause":
                        igs.service_call("Moteur", "removeRecuperation", elem_id,"")
                    else:
                        igs.service_call("Moteur", "removeExercice", elem_id,"")
                except:
                    pass
                if self.window:
                    self.window.update_exercise_list()

    def start_workout(self):
        """Start the workout session"""
        if len(self.exercises) > 0:
            self.current_exercise_index = 0
            js = {'nom':'Séance', 'elements': self.exercises }
            try:
                igs.service_call("Moteur", "startWorkout",json.dumps(js),"")
            except:
                pass  # Service might not be available yet
            if self.window:
                self.window.show_execution_view()
                

    def stop_workout(self):
        """Stop the workout session"""
        try:
            js = igs.service_call("Moteur", "stopWorkout",None,"")
            self.exercises = js.elements # TODO
        except:
            pass  # Service might not be available yet
        if self.window:
            self.window.show_config_view()

    def next_exercise(self):
        """Move to next exercise"""
        if self.current_exercise_index < len(self.exercises) - 1:
            self.current_exercise_index += 1
            if self.window:
                self.window.update_display()

    def previous_exercise(self):
        """Move to previous exercise"""
        if self.current_exercise_index > 0:
            self.current_exercise_index -= 1
            if self.window:
                self.window.update_display()
                
    def add_rest(self, duration_seconds: int):
            try:
                result = igs.service_call("Moteur", "addRecuperation", None, "")
            except:
                rest_id = None
            self.exercises.append({
                "type": "pause",
                "duree_secondes": int(duration_seconds),
                "id": result,
                "done": "false"
            })
            if self.window:
                self.window.update_exercise_list()
                
    # outputs
    def set_Fin_TimerO(self):
        igs.output_set_impulsion("fin_timer")
        
    # services
    def Settotaldisplay(self, sender_agent_name, sender_agent_uuid, Displayjson):
        """Service to receive and display JSON data"""
        try:
            data = json.loads(Displayjson)
            if "exercises" in data:
                self.exercises = data["exercises"]
            if "current_index" in data:
                self.current_exercise_index = data["current_index"]
            self.signal_bridge.update_ui.emit()
        except:
            pass


class WorkoutWindow(QMainWindow):
    def __init__(self, interface_graphique):
        super().__init__()
        self.interface = interface_graphique
        self.setWindowTitle("Sportable - Workout Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Update timer for execution view - create FIRST before calling show_config_view()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        
        # Create stacked widget for two views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create configuration view
        self.config_view = self.create_config_view()
        self.stacked_widget.addWidget(self.config_view)
        
        # Create execution view
        self.execution_view = self.create_execution_view()
        self.stacked_widget.addWidget(self.execution_view)
        
        # Show config view by default
        self.show_config_view()
        
        
        # Local rest timer
        self.local_rest_seconds = None
        self.local_rest_timer = QTimer(self)
        self.local_rest_timer.setInterval(1000)
        self.local_rest_timer.timeout.connect(self._tick_local_rest)
        
        # Dans WorkoutWindow.__init__ après la config des timers
        self._last_rest_item_key = None

    def create_config_view(self):
            """Create the configuration/setup view"""
            widget = QWidget()
            layout = QVBoxLayout()
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            # Title
            title = QLabel("Création de séance de sport")
            title.setObjectName("title")
            layout.addWidget(title)

            # === Deux formulaires côte à côte ===
            forms_row = QHBoxLayout()
            forms_row.setSpacing(20)

            # ----- FORMULAIRE EXERCICE -----
            ex_group = QGroupBox("Exercice")
            ex_form = QFormLayout()
            ex_form.setSpacing(10)

            self.ex_name_input = QComboBox()
            listeExos = ["Pompes", "Squats", "Jumping Jacks", "Levée de jambes", "Montée de genou"]
            self.ex_name_input.addItems(listeExos)
            ex_form.addRow("Exercice :", self.ex_name_input)

            self.ex_reps_spin = QSpinBox()
            self.ex_reps_spin.setRange(1, 100)
            self.ex_reps_spin.setValue(10)
            ex_form.addRow("Répétitions :", self.ex_reps_spin)

            self.ex_sets_spin = QSpinBox()
            self.ex_sets_spin.setRange(1, 20)
            self.ex_sets_spin.setValue(3)
            ex_form.addRow("Séries :", self.ex_sets_spin)

            add_ex_btn = QPushButton("Ajouter l'exercice")
            add_ex_btn.setObjectName("btnGreen")
            add_ex_btn.clicked.connect(self.add_exercise_to_list)
            ex_form.addRow(add_ex_btn)

            ex_group.setLayout(ex_form)
            forms_row.addWidget(ex_group, 1)

            # ----- FORMULAIRE PAUSE (à droite) -----
            rest_group = QGroupBox("Pause")
            rest_form = QFormLayout()
            rest_form.setSpacing(10)

            self.rest_duration_spin = QSpinBox()
            self.rest_duration_spin.setRange(5, 600)  # 5s à 10min
            self.rest_duration_spin.setValue(30)
            rest_form.addRow("Durée (secondes) :", self.rest_duration_spin)

            add_rest_btn = QPushButton("Ajouter la pause")
            add_rest_btn.setObjectName("btnGreen")
            add_rest_btn.clicked.connect(self.add_rest_to_list)
            rest_form.addRow(add_rest_btn)

            rest_group.setLayout(rest_form)
            forms_row.addWidget(rest_group, 1)

            layout.addLayout(forms_row)

            # Separator
            sep = QFrame()
            sep.setObjectName("separator")
            sep.setFixedHeight(1)
            layout.addWidget(sep)

            # Exercise list
            list_label = QLabel("Séquence configurée :")
            list_label.setObjectName("title")
            layout.addWidget(list_label)

            self.exercise_list = QListWidget()
            layout.addWidget(self.exercise_list)

            # Delete button for selected item
            delete_btn = QPushButton("Supprimer l'élément sélectionné")
            delete_btn.setObjectName("btnGreen")
            delete_btn.clicked.connect(self.delete_selected_exercise)
            layout.addWidget(delete_btn)

            # Start workout button
            start_btn = QPushButton("Démarrer l'entraînement")
            start_btn.setObjectName("btnRed")
            start_btn.clicked.connect(self.start_workout_clicked)
            layout.addWidget(start_btn)

            layout.addStretch()
            widget.setLayout(layout)
            return widget

    
    def create_execution_view(self):
        """Create the execution/workout view"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Execution de la séance")
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Current exercise name
        self.current_exercise_label = QLabel()
        self.current_exercise_label.setObjectName("exerciseName")
        self.current_exercise_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_exercise_label)
        
        # Separator
        sep1 = QFrame()
        sep1.setObjectName("separator")
        sep1.setFixedHeight(1)
        layout.addWidget(sep1)
        
        # Main content layout (side by side)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left side: Progress info and controls
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)
        
        # Progress info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        reps_row = QHBoxLayout()
        reps_row.addWidget(QLabel("Répétitions restantes:"))
        self.reps_remaining_label = QLabel("0")
        self.reps_remaining_label.setObjectName("displayValue")
        reps_row.addWidget(self.reps_remaining_label)
        reps_row.addStretch()
        info_layout.addLayout(reps_row)
        
        sets_row = QHBoxLayout()
        sets_row.addWidget(QLabel("Séries restantes:"))
        self.sets_remaining_label = QLabel("0")
        self.sets_remaining_label.setObjectName("displayValue")
        sets_row.addWidget(self.sets_remaining_label)
        sets_row.addStretch()
        info_layout.addLayout(sets_row)
        
        left_layout.addLayout(info_layout)
        
        # Vision state indicator
        vision_label = QLabel("Vision:")
        vision_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(vision_label)
        
        self.vision_state_indicator = QLabel()
        self.vision_state_indicator.setObjectName("visionIndicator")
        self.vision_state_indicator.setAlignment(Qt.AlignCenter)
        self.vision_state_indicator.setMinimumHeight(40)
        left_layout.addWidget(self.vision_state_indicator)
        
        # Feedback display
        # feedback_label = QLabel("Feedback:")
        # feedback_label.setStyleSheet("font-weight: bold;")
        # left_layout.addWidget(feedback_label)
        
        # self.feedback_display = QLabel()
        # self.feedback_display.setObjectName("feedbackDisplay")
        # self.feedback_display.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        # self.feedback_display.setWordWrap(True)
        # self.feedback_display.setMinimumHeight(80)
        # left_layout.addWidget(self.feedback_display)
        
        # Rest time display
        rest_separator = QFrame()
        rest_separator.setObjectName("separator")
        rest_separator.setFixedHeight(1)
        left_layout.addWidget(rest_separator)
        
        rest_layout = QHBoxLayout()
        rest_layout.addStretch()
        self.temps_pause_label = QLabel(" Temps de repos : ")
        rest_layout.addWidget(self.temps_pause_label)
        self.rest_time_label = QLabel(" 0s ")
        self.rest_time_label.setObjectName("displayValue")
        rest_layout.addWidget(self.rest_time_label)
        rest_layout.addStretch()
        left_layout.addLayout(rest_layout)
        
        left_layout.addStretch()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(400)
        
        content_layout.addWidget(left_widget)
        
        # Right side: Skeleton display
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        skeleton_label = QLabel("Visualisation du squelette:")
        skeleton_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        right_layout.addWidget(skeleton_label)
        
        # Use the custom SkeletonWidget instead of QLabel
        self.skeleton_display = SkeletonWidget()
        self.skeleton_display.setObjectName("skeletonDisplay")
        right_layout.addWidget(self.skeleton_display)
        
        right_widget.setLayout(right_layout)
        content_layout.addWidget(right_widget, 1)
        
        layout.addLayout(content_layout)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        
        self.exercise_counter_label = QLabel()
        self.exercise_counter_label.setAlignment(Qt.AlignCenter)
        self.exercise_counter_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        nav_layout.addWidget(self.exercise_counter_label)
        
        layout.addLayout(nav_layout)
        
        # Stop button
        stop_btn = QPushButton("Quitter")
        stop_btn.setObjectName("btnRed")
        stop_btn.clicked.connect(self.stop_workout_clicked)
        layout.addWidget(stop_btn)
        
        widget.setLayout(layout)
        return widget
    
    
    def add_rest_to_list(self):
            """Add a rest (pause) from input fields"""
            duration = self.rest_duration_spin.value()
            self.interface.add_rest(duration)
            self.update_exercise_list()

    
    def add_exercise_to_list(self):
        """Add exercise from input fields"""
        name_bf = self.ex_name_input.currentText().strip()
        name = self._get_logical_name(name_bf)
        reps = self.ex_reps_spin.value()
        sets = self.ex_sets_spin.value()

        if name:
            self.interface.add_exercise(name, reps, sets)
            self.update_exercise_list()
        else:
            # Show error message
            pass
    
    def delete_selected_exercise(self):
        """Delete selected exercise from list"""
        current_row = self.exercise_list.currentRow()
        if current_row >= 0:
            self.interface.remove_exercise(current_row)
    
    
    def update_exercise_list(self):
            """Update the list display (exercices + pauses)"""
            self.exercise_list.clear()
            for item in self.interface.exercises:
                t = item.get("type")
                if t == "exercice":
                    nom = item.get("nom", "Exercice")
                    reps = item.get("repetitions", 0)
                    sets = item.get("series", 0)
                    text = f"{self._get_corrected_name(nom)} — {reps} reps x {sets} séries"
                elif t == "pause":
                    duree_secondes = item.get("duree_secondes", 0)
                    text = f"Repos — {duree_secondes} s"
                else:
                    text = str(item)
                self.exercise_list.addItem(text)

    
    def start_workout_clicked(self):
        """Start the workout"""
        self.interface.start_workout()
        self.update_timer.start(500)  # Update every 500ms
        self._stop_local_rest()
    
    def stop_workout_clicked(self):
        """Stop the workout"""
        self.update_timer.stop()
        self.interface.stop_workout()
        self._stop_local_rest()
    
    def show_config_view(self):
        """Show configuration view"""
        self.stacked_widget.setCurrentWidget(self.config_view)
        self.update_timer.stop()
    
    def show_execution_view(self):
        """Show execution view"""
        self.stacked_widget.setCurrentWidget(self.execution_view)
        self.update_display()
    
    
    def update_display(self):
        """Met à jour la vue d'exécution : nom, reps/séries, temps de repos, compteur.
        Gère aussi le timer local de repos si le moteur ne fournit pas Rest_Time_RemainingI.
        """
        # 1) Vérifications de base
        if self.interface.Session_StateI != "execution" or len(self.interface.exercises) == 0:
            # Par sécurité, on coupe le timer local si on n’est pas en exécution
            self._stop_local_rest()
            return

        current_index = self.interface.current_exercise_index
        if not (0 <= current_index < len(self.interface.exercises)):
            self._stop_local_rest()
            return

        exercise = self.interface.exercises[current_index]
        t = exercise.get("type")

        # 2) Titre et affichage reps/séries selon le type
        if t == "pause":
            duree_secondes = exercise.get("duree_secondes", 0)
            self.current_exercise_label.setText(f"Pause : {duree_secondes} s")
            self.current_exercise_label.setStyleSheet("background-color: #2d8211;")
            self.reps_remaining_label.setText("—")
            self.sets_remaining_label.setText("—")
        else:
            nom = exercise.get("nom", "Exercice")
            nameAfter = self._get_corrected_name(nom)
            self.current_exercise_label.setText(f"Exercice actuel : {nameAfter}")
            self.current_exercise_label.setStyleSheet("background-color: #751323;")
            self.reps_remaining_label.setText(str(self.interface.Rep_RemainingI or 0))
            self.sets_remaining_label.setText(str(self.interface.Set_RemainingI or 0))

        # 3) Gestion du temps de repos : priorité au moteur
        if self.interface.Rest_Time_RemainingI is not None:
            # Valeur poussée par le moteur => on affiche telle quelle
            try:
                # au cas où c’est une chaîne
                rest_val = int(self.interface.Rest_Time_RemainingI)
            except:
                rest_val = 0
            self.rest_time_label.setText(f" {rest_val}s ")

            # IMPORTANT : si le moteur pousse la valeur, on coupe notre timer local
            self._stop_local_rest()

            # Et on reset la clé de cache pour permettre un relancement futur si besoin
            self._last_rest_item_key = None

        else:
            # Pas de valeur moteur
            if t == "pause":
                # On fabrique une clé unique pour cette pause (index + durée)
                # Cela évite de relancer le timer à chaque update (500 ms)
                current_key = (current_index, exercise.get("duree_secondes", 0))

                # Si on change de pause ou de durée, on relance
                if self._last_rest_item_key != current_key:
                    self._last_rest_item_key = current_key
                    self._start_local_rest(exercise.get("duree_secondes", 0))
                else:
                    pass
            else:
                # On est sur un exercice sans valeur moteur => pas de timer local
                self._stop_local_rest()
                self._last_rest_item_key = None

        # 4) Compteur d’élément
        self.exercise_counter_label.setText(
            f"Élément {current_index + 1} / {len(self.interface.exercises)}"
        )

    
    def update_squelette_display(self, squelette_data):
        """Update skeleton/squelette display"""
        if squelette_data:
            self.skeleton_display.set_skeleton_data(squelette_data)
        else:
            self.skeleton_display.landmarks = []
            self.skeleton_display.update()
    
    def update_vision_state_display(self, vision_state):
        """Update vision state indicator"""
        if vision_state:
            self.vision_state_indicator.setText("✓ Vision Active")
            self.vision_state_indicator.setStyleSheet(
                "border: 2px solid green; padding: 10px; background-color: #e8f5e9; color: green; font-weight: bold;"
            )
        else:
            self.vision_state_indicator.setText("✗ Vision Inactive")
            self.vision_state_indicator.setStyleSheet(
                "border: 2px solid red; padding: 10px; background-color: #ffebee; color: red; font-weight: bold;"
            )
    
    def update_feedback_display(self, feedback_data):
        """Update feedback display from vision"""
        self.feedback_display.setText(feedback_data or "En attente de feedback...")
    
    def update_reps(self, value):
        """Update reps remaining display"""
        self.reps_remaining_label.setText(str(value or 0))
    
    def update_sets(self, value):
        """Update sets remaining display"""
        self.sets_remaining_label.setText(str(value or 0))
    
    def update_rest_time(self, value):
        """Slot appelé par le SignalBridge: le moteur pousse une valeur de repos restante."""
        # On synchronise l'état côté interface pour que update_display() détecte la priorité moteur
        try:
            self.interface.Rest_Time_RemainingI = int(value) if value is not None else None
        except:
            self.interface.Rest_Time_RemainingI = None

        # Démarre un timer local à chaque update
        if self.interface.Rest_Time_RemainingI is not None and self.interface.Rest_Time_RemainingI > 0:
            self._start_rest_countdown(self.interface.Rest_Time_RemainingI)
        else:
            self._stop_rest_countdown()

        self.update_display()
    
    def _start_rest_countdown(self, seconds):
        self._stop_rest_countdown()
        self._rest_seconds_left = int(seconds)
        self.rest_time_label.setText(f" {self._rest_seconds_left}s ")
        self.temps_pause_label.setStyleSheet("background-color: red; color: white; font-weight: bold; border-radius: 5px;")
        self.rest_time_label.setStyleSheet("background-color: red; color: white; font-weight: bold; border-radius: 5px;")
        self._rest_timer = QTimer(self)
        self._rest_timer.timeout.connect(self._tick_rest_countdown)
        self._rest_timer.start(1000)

    def _stop_rest_countdown(self):
        if hasattr(self, '_rest_timer') and self._rest_timer.isActive():
            self._rest_timer.stop()
        self._rest_seconds_left = None
        self.temps_pause_label.setStyleSheet("background-color: white; color: black; font-weight: normal;")
        self.rest_time_label.setStyleSheet("background-color: white; color: black; font-weight: normal;")

    def _tick_rest_countdown(self):
        if self._rest_seconds_left is None:
            self._stop_rest_countdown()
            return
        self._rest_seconds_left -= 1
        self.rest_time_label.setText(f" {self._rest_seconds_left}s ")
        if self._rest_seconds_left <= 0:
            self._stop_rest_countdown()
            # Envoie l'impulsion fin_timer
            self.interface.set_Fin_TimerO()
            
    
    def update_current_exercice_display(self, exercice_name):
        """Update current exercise display from Moteur input"""
        self.current_exercise_label.setText(f"Exercice actuel : {self._get_corrected_name(exercice_name)}")
        self.current_exercise_label.setStyleSheet("background-color: #751323;")
        
    def _start_local_rest(self, seconds: int):
        self._stop_local_rest()
        self.local_rest_seconds = max(0, int(seconds))
        self._render_local_rest()
        if self.local_rest_seconds > 0:
            self.local_rest_timer.start()

    def _stop_local_rest(self):
        if self.local_rest_timer.isActive():
            self.local_rest_timer.stop()
        self.local_rest_seconds = None

    def _tick_local_rest(self):
        if self.local_rest_seconds is None:
            self._stop_local_rest()
            return
        self.local_rest_seconds -= 1
        self._render_local_rest()
        if self.local_rest_seconds <= 0:
            self._stop_local_rest()

    def _render_local_rest(self):
        val = self.local_rest_seconds if self.local_rest_seconds is not None else 0
        self.rest_time_label.setText(f" {val}s ")
        
    def _get_corrected_name(self, nom):
        nameAfter = ""
        match nom:
            case "pompes":
                nameAfter = "Pompes"
            case "squats":
                nameAfter = "Squats"
            case "jumping_jacks":
                nameAfter = "Jumping Jacks"
            case "lever_jambes":
                nameAfter = "Levée de jambes"
            case "montee_genou":
                nameAfter = "Montée de genou"
            case _:
                nameAfter = nom
        return nameAfter
    
    def _get_logical_name(self, nom):
        nameBefore = ""
        match nom:
            case "Pompes":
                nameBefore = "pompes"
            case "Squats":
                nameBefore = "squats"
            case "Jumping Jacks":
                nameBefore = "jumping_jacks"
            case "Levée de jambes":
                nameBefore = "lever_jambes"
            case "Montée de genou":
                nameBefore = "montee_genou"
            case _:
                nameBefore = nom
        return nameBefore
