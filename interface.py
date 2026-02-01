import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class SportApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Appli Sport Fonctionnelle")
        self.resize(350, 600)
        self.setStyleSheet("""
            QWidget { background-color: #f4f4f4; font-family: 'Segoe UI'; }
            .Card { background-color: white; border: 2px solid #2c3e50; border-radius: 15px; }
            QPushButton { border-radius: 5px; font-weight: bold; padding: 8px; }
            .BtnGreen { background-color: #3e7d23; color: white; }
            .BtnRed { background-color: #c92a42; color: white; text-transform: uppercase; }
            .BtnNext { background-color: #2c3e50; color: white; }
            QLineEdit, QSpinBox { padding: 5px; border: 1px solid #8c8c8c; }
        """)

        # Pile d'écrans (Equivalent du système .hidden)
        self.stack = QStackedWidget()
        
        self.setup_creation_screen()
        self.setup_active_screen()
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)

    # --- ÉCRAN 1 : CRÉATION ---
    def setup_creation_screen(self):
        page = QFrame()
        layout = QVBoxLayout(page)
        
        title = QLabel("Création d'une séance")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # Zone scrollable pour la liste d'exercices
        self.scroll = QScrollArea()
        self.scroll_content = QWidget()
        self.workout_layout = QVBoxLayout(self.scroll_content)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

        # Boutons d'ajout
        btn_layout = QHBoxLayout()
        add_ex_btn = QPushButton("Ajouter exercice +")
        add_ex_btn.setObjectName("BtnGreen") # Utilisation de styles via sélecteurs
        add_ex_btn.clicked.connect(self.add_exercise_row)
        
        add_rest_btn = QPushButton("Ajouter récup +")
        add_rest_btn.clicked.connect(self.add_rest_row)
        
        btn_layout.addWidget(add_ex_btn)
        btn_layout.addWidget(add_rest_btn)
        layout.addLayout(btn_layout)

        # Bouton START
        start_btn = QPushButton("START")
        start_btn.setMinimumHeight(50)
        start_btn.setStyleSheet("background-color: #c92a42; color: white; font-size: 16px;")
        start_btn.clicked.connect(self.start_workout)
        layout.addWidget(start_btn)

        self.stack.addWidget(page)

    def add_exercise_row(self):
        row = QFrame()
        row.setObjectName("ExoRow")
        row.setStyleSheet("#ExoRow { background: #e0e0e0; border: 1px solid #ccc; border-radius: 8px; }")
        
        # Layout principal de la ligne (Horizontal pour mettre la croix à droite)
        main_layout = QHBoxLayout(row)
        
        # Layout du formulaire (Nom, Reps, Séries)
        form_layout = QFormLayout()
        name_input = QComboBox()
        reps_input = QSpinBox()
        sets_input = QSpinBox()
        
        
        
        listeExos=["pompes", "squats","jumping_jacks","lever_jambes","montee_genou"]
        name_input.addItems(listeExos)
        form_layout.addRow("Exo :", name_input)
        form_layout.addRow("Reps :", reps_input)
        form_layout.addRow("Séries :", sets_input)
        
        
        
        name_input.setStyleSheet("border-radius: 12px;")
        reps_input.setStyleSheet("border-radius: 12px;")
        sets_input.setStyleSheet("border-radius: 12px;")
        
        row.setStyleSheet("background-color: rgba(64, 207, 93, 0.8); color: white;")
        
        main_layout.addLayout(form_layout)

        # Bouton Haut
        up_btn = QPushButton("▲")
        up_btn.setFixedSize(25, 25)
        up_btn.setStyleSheet("background: #bdc3c7; border-radius: 4px;")
        up_btn.clicked.connect(self.move_up)
        
        # Bouton Bas
        down_btn = QPushButton("▼")
        down_btn.setFixedSize(25, 25)
        down_btn.setStyleSheet("background: #bdc3c7; border-radius: 4px;")
        down_btn.clicked.connect(self.move_down)
        
        # Croix de suppression (votre bouton précédent)
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(25, 25)
        del_btn.setStyleSheet("background-color: #c92a42; color: white; border-radius: 4px;")
        del_btn.clicked.connect(self.remove_row)

        # Assemblage
        main_layout.addWidget(up_btn)
        main_layout.addWidget(down_btn)
        main_layout.addWidget(del_btn)
        
        main_layout.addWidget(del_btn, alignment=Qt.AlignTop)
        
        row.setProperty("type", "exercise")
        self.workout_layout.addWidget(row)
    
    def add_rest_row(self):
        row = QFrame()
        row.setStyleSheet("background: #6495ed; border-radius: 8px; color: white;")
        row_layout = QHBoxLayout(row)
        
        time_input = QSpinBox()
        time_input.setSuffix(" min")
        
        row_layout.addWidget(QLabel("⏳ Récupération :"))
        row_layout.addWidget(time_input)
        
        # Croix de suppression
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(25, 25)
        del_btn.setStyleSheet("background-color: rgba(255,255,255,0.3); color: white; border-radius: 12px;")
        del_btn.clicked.connect(self.remove_row)
        
        row_layout.addWidget(del_btn)
        
        row.setProperty("type", "rest")
        self.workout_layout.addWidget(row)        
        
    def remove_row(self):
        # Récupère le bouton qui a été cliqué
        button = self.sender()
        if button:
            # Récupère la ligne (le QFrame) et la détruit
            row = button.parent()
            row.deleteLater()

    def move_row(self, direction):
        button = self.sender()
        if button:
            row = button.parent()
            # On trouve l'index actuel de la ligne dans le layout
            current_index = self.workout_layout.indexOf(row)
            new_index = current_index + direction
            
            # On vérifie qu'on ne sort pas des limites
            if 0 <= new_index < self.workout_layout.count():
                # On retire et on réinsère
                self.workout_layout.removeWidget(row)
                self.workout_layout.insertWidget(new_index, row)

    def move_up(self):
        self.move_row(-1)

    def move_down(self):
        self.move_row(1)
        
        
    # --- ÉCRAN 2 : SÉANCE ACTIVE ---
    def setup_active_screen(self):
        self.active_page = QFrame()
        layout = QVBoxLayout(self.active_page)

        self.status_label = QLabel("Exercice en cours")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.current_ex_name = QLabel("NOM EXERCICE")
        self.current_ex_name.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        self.current_ex_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_ex_name)

        # Illustration (Placeholder)
        img_placeholder = QLabel("IMAGE / GIF")
        img_placeholder.setStyleSheet("background: #ddd; min-height: 150px; border-radius: 10px;")
        img_placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(img_placeholder)

        # Footer info
        self.next_label = QLabel("À venir : Fin de séance")
        layout.addWidget(self.next_label)

        next_btn = QPushButton("Étape Suivante >>")
        next_btn.clicked.connect(self.next_step)
        layout.addWidget(next_btn)

        quit_btn = QPushButton("Quitter")
        quit_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(quit_btn)

        self.stack.addWidget(self.active_page)

    # --- LOGIQUE ---
    def start_workout(self):
        # Ici on pourrait parser le contenu de self.workout_layout pour remplir une liste
        self.stack.setCurrentIndex(1)
        self.current_ex_name.setText("C'est parti !")

    def next_step(self):
        # Logique pour passer à l'index suivant du plan
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SportApp()
    window.show()
    sys.exit(app.exec_())