#!/usr/bin/env -P /usr/bin:/usr/local/bin python3 -B
# coding: utf-8

#
#  Vision.py
#  Vision
#  Created by Sportable & Co on 2026/01/09
#
# "no description"
#
import ingescape as igs
import cv2
import mediapipe as mp
import numpy as np
import json
from collections import deque



class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Vision(metaclass=Singleton):
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(static_image_mode=False, model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        # inputs
        self.Current_ExerciceI = None

        # outputs
        self._SqueletteO = None
        self._Vision_StateO = None
        self._FeedbackO = None
        

        self.counter = 0
        self.stage = "IDLE"
        self.feedback = "WAITING..."
        self.tracked_joints = []
        self.skeleton_color = (100, 100, 100)
        self.buffer_size = 7
        self.angle_buffers = {}

        # Machine d'état pour le comptage des répétitions
        self.fsm = {}


    # outputs
    def set_Rep_ValidatedO(self):
        igs.output_set_impulsion("rep_validated")

    @property
    def SqueletteO(self):
        return self._SqueletteO

    @SqueletteO.setter
    def SqueletteO(self, value):
        self._SqueletteO = value
        if self._SqueletteO is not None:
            igs.output_set_string("squelette", self._SqueletteO)
    
    @property
    def Vision_StateO(self):
        return self._Vision_StateO

    @Vision_StateO.setter
    def Vision_StateO(self, value):
        self._Vision_StateO = value
        if self._Vision_StateO is not None:
            igs.output_set_bool("vision_state", self._Vision_StateO)
    
    @property
    def FeedbackO(self):
        return self._FeedbackO

    @FeedbackO.setter
    def FeedbackO(self, value):
        self._FeedbackO = value
        if self._FeedbackO is not None:
            igs.output_set_string("feedback", self._FeedbackO)

    def calculate_angle(self, a, b, c):
        """Calcul des angles entre les points a, b, c"""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        
        # Calcul de l'angle en radians avec la fonction arctan2
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        
        # Convertir en degrés
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
        return angle

    def smooth_angle(self, key, value):
        """Lissage des angles avec une moyenne mobile, évite les faux positifs"""
        if key not in self.angle_buffers:
            self.angle_buffers[key] = deque(maxlen=self.buffer_size)
        buf = self.angle_buffers[key]
        buf.append(value)
        return float(sum(buf) / len(buf))
    
    def fsm_append_state(self, exercise, state):
        if state is None:
            return self.fsm.setdefault(exercise, {"state": None, "seq": []})
        entry = self.fsm.setdefault(exercise, {"state": None, "seq": []})
        prev = entry["state"]
        if state != prev:
            entry["state"] = state
            if len(entry["seq"]) == 0 or entry["seq"][-1] != state:
                entry["seq"].append(state)
        return entry

    def fsm_check_and_count(self, exercise):
        entry = self.fsm.get(exercise)
        if not entry:
            return False
        seq = entry["seq"]
        # Squat doit suivre la séquence [S1, S2, S3, S2, S1]
        if exercise == 'squats' and len(seq) >= 5:
            pattern = ['S1','S2','S3','S2','S1']
            i = 0
            found = True
            for token in pattern:
                try:
                    j = seq.index(token, i)
                except ValueError:
                    found = False
                    break
                i = j + 1
            if found:
                entry['seq'] = []
                return True
            if exercise != 'squats' and len(seq) >= 3:
                for i in range(len(seq)-2):
                    a,b,c = seq[i], seq[i+1], seq[i+2]
                    if a != b and b != c and a == c:
                        entry['seq'] = []
                        return True
        return False

    def get_coords(self, landmarks, part_name):
        return [
            landmarks[self.mp_pose.PoseLandmark[part_name].value].x,
            landmarks[self.mp_pose.PoseLandmark[part_name].value].y
        ]
    
    def landmarks_to_json(self, landmarks):
        landmarks_data = []
        
        # Noms des 33 landmarks MediaPipe Pose
        landmark_names = [
            "NOSE", "LEFT_EYE_INNER", "LEFT_EYE", "LEFT_EYE_OUTER",
            "RIGHT_EYE_INNER", "RIGHT_EYE", "RIGHT_EYE_OUTER",
            "LEFT_EAR", "RIGHT_EAR",
            "MOUTH_LEFT", "MOUTH_RIGHT",
            "LEFT_SHOULDER", "RIGHT_SHOULDER",
            "LEFT_ELBOW", "RIGHT_ELBOW",
            "LEFT_WRIST", "RIGHT_WRIST",
            "LEFT_PINKY", "RIGHT_PINKY",
            "LEFT_INDEX", "RIGHT_INDEX",
            "LEFT_THUMB", "RIGHT_THUMB",
            "LEFT_HIP", "RIGHT_HIP",
            "LEFT_KNEE", "RIGHT_KNEE",
            "LEFT_ANKLE", "RIGHT_ANKLE",
            "LEFT_HEEL", "RIGHT_HEEL",
            "LEFT_FOOT_INDEX", "RIGHT_FOOT_INDEX"
        ]
        
        for i, landmark in enumerate(landmarks):
            landmark_dict = {
                "id": i,
                "name": landmark_names[i] if i < len(landmark_names) else f"LANDMARK_{i}",
                "x": float(landmark.x),
                "y": float(landmark.y),
                "z": float(landmark.z),
                "visibility": float(landmark.visibility)
            }
            landmarks_data.append(landmark_dict)
        
        return json.dumps({
            "landmarks": landmarks_data,
            "timestamp": int(cv2.getTickCount()),
            "counter": self.counter,
            "stage": self.stage,
            "feedback": self.feedback
        })
    
    def send_skeleton_to_interface(self, landmarks):
        try:
            skeleton_json = self.landmarks_to_json(landmarks)
            self.SqueletteO = skeleton_json
            # Envoyer aussi le feedback
            self.FeedbackO = self.feedback
        except Exception as e:
            pass

    def draw_colored_skeleton(self, image, landmarks, skeleton_color):
        h, w, _ = image.shape
        
        connections = [
            (11, 13), (13, 15),  # bras gauche
            (12, 14), (14, 16),  # bras droit
            (11, 23), (12, 24),  # épaules aux hanches
            (23, 24),             # Hanches
            (23, 25), (25, 27),  # jambe gauche
            (24, 26), (26, 28),  # jambe droite
            (11, 12),             # épaules
            (9, 10),              # yeux
        ]
        
        # Dessiner les connexions
        for start, end in connections:
            if start < len(landmarks) and end < len(landmarks):
                x1 = int(landmarks[start].x * w)
                y1 = int(landmarks[start].y * h)
                x2 = int(landmarks[end].x * w)
                y2 = int(landmarks[end].y * h)
                cv2.line(image, (x1, y1), (x2, y2), skeleton_color, 3)
        
        # Dessiner les points
        for landmark in landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(image, (x, y), 4, skeleton_color, -1)

    def analyze_pompes(self, landmarks, image):
        shoulder = self.get_coords(landmarks, "LEFT_SHOULDER")
        elbow = self.get_coords(landmarks, "LEFT_ELBOW")
        wrist = self.get_coords(landmarks, "LEFT_WRIST")
        elbow_angle = self.calculate_angle(shoulder, elbow, wrist)
        elbow_angle = self.smooth_angle('pompes_elbow', elbow_angle)
        
        hip = self.get_coords(landmarks, "LEFT_HIP")
        knee = self.get_coords(landmarks, "LEFT_KNEE")
        back_angle = self.calculate_angle(shoulder, hip, knee)
        back_angle = self.smooth_angle('pompes_back', back_angle)
        
        ankle = self.get_coords(landmarks, "LEFT_ANKLE")
        leg_angle = self.calculate_angle(hip, knee, ankle)
        leg_angle = self.smooth_angle('pompes_leg', leg_angle)

        # Si l'angle est > 150°, le dos et les jambes sont considérés comme droits
        form_is_valid = back_angle > 150 and leg_angle > 150
        if back_angle < 170:
            self.feedback = 'Hips too high'

        self.skeleton_color = (0, 255, 0) if form_is_valid else (0, 165, 255)
        
        self.tracked_joints = [
            ("LEFT_ELBOW", (0, 255, 255) if elbow_angle < 90 or elbow_angle > 160 else (0, 165, 255)),
            ("LEFT_SHOULDER", (0, 255, 0) if back_angle > 150 else (0, 0, 255)),
            ("LEFT_HIP", (0, 255, 0) if back_angle > 150 else (0, 0, 255)),
            ("LEFT_KNEE", (0, 255, 0) if leg_angle > 150 else (0, 0, 255)),
        ]
        
        cv2.putText(image, f"Elbow: {int(elbow_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Back: {int(back_angle)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if back_angle > 150 else (0,0,255), 1)
        
        if not form_is_valid:
            self.feedback = "BACK OR LEGS BENT!"
        else:
            self.feedback = "GOOD FORM"
            
            prev_state = self.fsm.get('pompes', {}).get('state')
            up_thr = 160
            down_thr = 90
            hyst = 5
            state = prev_state or 'IDLE'
            if prev_state == 'UP':
                if elbow_angle < down_thr + hyst:
                    state = 'DOWN'
                else:
                    state = 'UP'
            elif prev_state == 'DOWN':
                if elbow_angle > up_thr - hyst:
                    state = 'UP'
                else:
                    state = 'DOWN'
            else:
                if elbow_angle > up_thr:
                    state = 'UP'
                elif elbow_angle < down_thr:
                    state = 'DOWN'
                else:
                    state = 'TRANSITION'

            self.fsm_append_state('pompes', state)
            self.stage = state
            if self.fsm_check_and_count('pompes'):
                self.counter += 1
                self.set_Rep_ValidatedO()

    def analyze_squats(self, landmarks, image):
        # 1. Récupération des coordonnées (Côté GAUCHE)
        shoulder = self.get_coords(landmarks, "LEFT_SHOULDER")
        hip = self.get_coords(landmarks, "LEFT_HIP")
        knee = self.get_coords(landmarks, "LEFT_KNEE")
        ankle = self.get_coords(landmarks, "LEFT_ANKLE")

        # 2. Création des points "Virtuels" pour la verticale
        # OpenCV : Y augmente vers le bas. Donc (x, y - 1) est vers le HAUT.
        hip_vert_up = [hip[0], hip[1] - 1.0]      # Point vertical au-dessus des hanches
        hip_vert_down = [hip[0], hip[1] + 1.0]    # Point vertical en-dessous des hanches
        ankle_vert_up = [ankle[0], ankle[1] - 1.0] # Point vertical au-dessus de la cheville

        # 3. Calcul des Angles selon vos contraintes (en utilisant votre fonction calculate_angle)
        
        # --- Feedback 1 & 2 : Angle du dos (Shoulder-Hip vs Vertical) ---
        # 0° = Dos vertical, >0° = Penché
        back_angle = self.calculate_angle(shoulder, hip, hip_vert_up)
        back_angle = self.smooth_angle('back_vert', back_angle)

        # --- Feedback 3 & 5 : Angle des cuisses (Hip-Knee vs Vertical Bas) ---
        # 0° = Debout (Jambe verticale), 90° = Parallèle, >90° = Profond
        thigh_angle = self.calculate_angle(knee, hip, hip_vert_down)
        thigh_angle = self.smooth_angle('thigh_vert', thigh_angle)

        # --- Feedback 4 : Angle des tibias (Knee-Ankle vs Vertical Haut) ---
        # 0° = Tibia vertical, >0° = Genou qui avance
        shin_angle = self.calculate_angle(knee, ankle, ankle_vert_up)
        shin_angle = self.smooth_angle('shin_vert', shin_angle)
        
        # --- Angle de flexion classique pour l'affichage Squelette (Optionnel mais utile) ---
        raw_knee = self.calculate_angle(hip, knee, ankle)

        # 4. Logique FSM (Machine à États) basée sur l'angle des cuisses (Thigh Angle)
        # S1: Debout (<30°) | S2: Transition (30°-85°) | S3: Bas (>85°)
        
        prev_state = self.fsm.get('squats', {}).get('state')
        state = prev_state or 'S1'

        if state == 'S1':
            if thigh_angle > 35: state = 'S2'
        elif state == 'S2':
            if thigh_angle > 85: state = 'S3'
            elif thigh_angle < 30: state = 'S1'
        elif state == 'S3':
            if thigh_angle < 80: state = 'S2'

        # 5. Gestion des Feedbacks (Priorité aux erreurs sévères)
        self.feedback = "FORM OK"

        # > Feedback 4 (Sévère): Genoux trop avancés (> 30°)
        if shin_angle > 30:
            self.feedback = "KNEE OVER TOES" # "Knee falling over toes"
        
        # > Feedback 5 (Sévère): Squat trop profond (> 95°)
        # La consigne dit que c'est une "incorrect posture" si > 95
        elif state == 'S3' and thigh_angle > 95:
            self.feedback = "TOO DEEP"

        # > Feedback 1: Dos trop vertical (< 20°)
        elif back_angle < 20 and state != 'S1':
            self.feedback = "BEND FORWARD" # Penchez-vous en avant

        # > Feedback 2: Dos trop penché (> 45°)
        elif back_angle > 45:
            self.feedback = "BEND BACKWARD" # Redressez-vous

        # > Feedback 3: Transition (Lower hips)
        # S'affiche quand on est en S2 (descente) et angle entre 50 et 80
        elif (state == 'S2' and prev_state == 'S1') and (50 < thigh_angle < 80):
            self.feedback = "LOWER YOUR HIPS"
        
        # Feedback positif final
        elif state == 'S3':
            self.feedback = "GOOD DEPTH"

        # 6. Couleurs et Affichage       
        self.skeleton_color = (0, 255, 0) if self.feedback == "FORM OK" else (0, 0, 255)
        
        self.tracked_joints = [
            # Genou: Vert si angle cuisse OK, Rouge si trop profond
            ("LEFT_KNEE", (0, 0, 255) if thigh_angle > 95 else (0, 255, 0)),
            # Hanche: Vert si dos entre 20 et 45
            ("LEFT_HIP", (0, 255, 0) if 20 <= back_angle <= 45 else (0, 0, 255)),
            # Cheville: Rouge si tibia trop avancé
            ("LEFT_ANKLE", (0, 0, 255) if shin_angle > 30 else (0, 165, 255))
        ]
        
        # Affichage des valeurs sur l'écran
        cv2.putText(image, f"Back: {int(back_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Thigh: {int(thigh_angle)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Shin: {int(shin_angle)}", (10, 190), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)

        # 7. Mise à jour finale
        self.fsm_append_state('squats', state)
        self.stage = state
        
        # Comptage : S1 -> S2 -> S3 -> S2 -> S1
        if self.fsm_check_and_count('squats'):
            self.counter += 1
            self.set_Rep_ValidatedO()

    def analyze_jumping_jacks(self, landmarks, image):
        l_shoulder = self.get_coords(landmarks, "LEFT_SHOULDER")
        l_elbow = self.get_coords(landmarks, "LEFT_ELBOW")
        l_hip = self.get_coords(landmarks, "LEFT_HIP")
        arm_angle = self.calculate_angle(l_hip, l_shoulder, l_elbow)
        
        l_knee = self.get_coords(landmarks, "LEFT_KNEE")
        leg_abduction = self.calculate_angle(l_shoulder, l_hip, l_knee)
        
        l_wrist = self.get_coords(landmarks, "LEFT_WRIST")
        elbow_straight = self.calculate_angle(l_shoulder, l_elbow, l_wrist)
        
        valid_form = elbow_straight > 140
        
        self.skeleton_color = (0, 255, 0) if valid_form else (0, 165, 255)
        
        self.tracked_joints = [
            ("LEFT_SHOULDER", (0, 255, 0) if valid_form else (0, 0, 255)),
            ("LEFT_ELBOW", (0, 255, 0) if elbow_straight > 140 else (0, 0, 255)),
            ("LEFT_WRIST", (0, 255, 255) if arm_angle > 100 else (0, 165, 255)),
            ("LEFT_HIP", (0, 165, 255)),
        ]
        
        cv2.putText(image, f"Arm Amp: {int(arm_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        
        if not valid_form:
            self.feedback = "STRAIGHTEN YOUR ARMS!"
        else:
            self.feedback = "GO!"
            
            wrist_y = l_wrist[1]
            shoulder_y = l_shoulder[1]
            
            if wrist_y < shoulder_y and leg_abduction > 10:
                self.stage = "open"
            
            if wrist_y > shoulder_y and self.stage == "open":
                self.stage = "close"
                self.counter += 1
                self.set_Rep_ValidatedO()

    def analyze_lever_jambes(self, landmarks, image):
        shoulder = self.get_coords(landmarks, "RIGHT_SHOULDER")
        hip = self.get_coords(landmarks, "RIGHT_HIP")
        knee = self.get_coords(landmarks, "RIGHT_KNEE")
        hip_angle = self.calculate_angle(shoulder, hip, knee)
        
        ankle = self.get_coords(landmarks, "RIGHT_ANKLE")
        knee_angle = self.calculate_angle(hip, knee, ankle)
        
        valid_form = knee_angle > 150
        
        self.skeleton_color = (0, 255, 0) if valid_form else (0, 165, 255)
        
        self.tracked_joints = [
            ("RIGHT_HIP", (0, 255, 255) if hip_angle > 100 else (0, 165, 255)),
            ("RIGHT_KNEE", (0, 255, 0) if knee_angle > 150 else (0, 0, 255)),
            ("RIGHT_ANKLE", (0, 165, 255)),
        ]
        
        cv2.putText(image, f"Hip: {int(hip_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Knee: {int(knee_angle)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if knee_angle > 150 else (0,0,255), 1)
        
        if not valid_form:
            self.feedback = "LEG TOO BENT!"
        else:
            self.feedback = "GOOD FORM"
            if hip_angle > 160:
                self.stage = "down"
            if hip_angle < 100 and self.stage == "down" and valid_form:
                self.stage = "up"
                self.counter += 1
                self.set_Rep_ValidatedO()

    def analyze_montee_genou(self, landmarks, image):
        # 1. Récupération des coordonnées (G = Gauche, D = Droite)
        l_hip = self.get_coords(landmarks, "LEFT_HIP")
        l_knee = self.get_coords(landmarks, "LEFT_KNEE")
        r_hip = self.get_coords(landmarks, "RIGHT_HIP")
        r_knee = self.get_coords(landmarks, "RIGHT_KNEE")
        shoulder = self.get_coords(landmarks, "LEFT_SHOULDER")

        # 2. Points virtuels pour la verticale (Y augmente vers le bas)
        hip_vert_down_l = [l_hip[0], l_hip[1] + 1.0] # Pour angle cuisse G
        hip_vert_down_r = [r_hip[0], r_hip[1] + 1.0] # Pour angle cuisse D
        hip_vert_up = [l_hip[0], l_hip[1] - 1.0]     # Pour angle dos

        # 3. Calcul des Angles (0° = Debout/Vertical, 90° = Horizontal)
        
        # Angle Cuisse Gauche
        l_thigh_angle = self.calculate_angle(l_knee, l_hip, hip_vert_down_l)
        l_thigh_angle = self.smooth_angle('mk_l_thigh', l_thigh_angle)
        
        # Angle Cuisse Droite
        r_thigh_angle = self.calculate_angle(r_knee, r_hip, hip_vert_down_r)
        r_thigh_angle = self.smooth_angle('mk_r_thigh', r_thigh_angle)

        # Angle du Dos (Posture)
        back_angle = self.calculate_angle(shoulder, l_hip, hip_vert_up)
        back_angle = self.smooth_angle('mk_back', back_angle)

        # 4. Vérification Posture (Dos droit)
        # On tolère jusqu'à 25° de penchement arrière/avant
        valid_form = back_angle < 25
        
        # 5. Machine à États (Alternance Gauche -> Droite)
        
        # Récupération de l'état précédent ('WAIT_L', 'WAIT_R', ou 'IDLE')
        # 'seq' nous servira à savoir quelle jambe a été validée en dernier
        entry = self.fsm.setdefault('montee_genou', {'state': 'IDLE', 'last_leg': None})
        state = entry['state']
        
        # Seuils
        UP_THRESH = 75  # La cuisse doit monter haut (>75°)
        DOWN_THRESH = 30 # La jambe doit redescendre (<30°) pour valider le cycle

        # Détection de quelle jambe est levée "maintenant"
        current_lift = None
        if l_thigh_angle > UP_THRESH:
            current_lift = 'LEFT'
        elif r_thigh_angle > UP_THRESH:
            current_lift = 'RIGHT'
        
        # Logique FSM
        # Etat initial ou Reset
        if state == 'IDLE':
            self.feedback = "START LEFT OR RIGHT"
            if current_lift == 'LEFT':
                entry['state'] = 'L_UP'
                entry['last_leg'] = 'LEFT'
            elif current_lift == 'RIGHT':
                entry['state'] = 'R_UP'
                entry['last_leg'] = 'RIGHT'
        
        # Si on est en train de lever la GAUCHE
        elif state == 'L_UP':
            self.feedback = "GOOD LEFT!"
            # On attend que ça redescende
            if l_thigh_angle < DOWN_THRESH:
                entry['state'] = 'WAIT_R' # Maintenant on veut la droite !
        
        # Si on est en train de lever la DROITE
        elif state == 'R_UP':
            self.feedback = "GOOD RIGHT!"
            # On attend que ça redescende
            if r_thigh_angle < DOWN_THRESH:
                entry['state'] = 'WAIT_L' # Maintenant on veut la gauche !

        # On attend la jambe DROITE
        elif state == 'WAIT_R':
            self.feedback = "NOW RIGHT !"
            if current_lift == 'RIGHT':
                entry['state'] = 'R_UP'
                entry['last_leg'] = 'RIGHT'
                # C'est ici qu'on valide une "demi-rep" ou la fin d'un cycle
                # Si vous comptez 1 rep = G + D, on incrémente ici si on a commencé par G
            elif current_lift == 'LEFT':
                self.feedback = "NO! USE RIGHT LEG"
        
        # On attend la jambe GAUCHE
        elif state == 'WAIT_L':
            self.feedback = "NOW LEFT !"
            if current_lift == 'LEFT':
                entry['state'] = 'L_UP'
                entry['last_leg'] = 'LEFT'
                # Cycle complet G -> D -> G (début nouveau cycle) ou D -> G
                self.counter += 1
                self.set_Rep_ValidatedO()
            elif current_lift == 'RIGHT':
                self.feedback = "NO! USE LEFT LEG"

        # 6. Feedback Posture prioritaire
        if not valid_form:
            self.feedback = "STRAIGHTEN BACK!"
            
        # 7. Couleurs et Affichage
        self.skeleton_color = (0, 255, 0) if valid_form else (0, 0, 255)
        
        # Tracking visuel
        self.tracked_joints = [
            ("LEFT_KNEE", (0, 255, 255) if l_thigh_angle > UP_THRESH else (0, 165, 255)),
            ("RIGHT_KNEE", (0, 255, 255) if r_thigh_angle > UP_THRESH else (0, 165, 255)),
            ("LEFT_HIP", (0, 255, 0) if valid_form else (0, 0, 255))
        ]
        
        # Affichage Texte sur l'image
        h, w, _ = image.shape
        # Afficher L ou R à côté des genoux
        cx_l, cy_l = int(l_knee[0]*w), int(l_knee[1]*h)
        cx_r, cy_r = int(r_knee[0]*w), int(r_knee[1]*h)
        
        cv2.putText(image, f"L: {int(l_thigh_angle)}", (cx_l + 10, cy_l), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 2)
        cv2.putText(image, f"R: {int(r_thigh_angle)}", (cx_r - 60, cy_r), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 2)
        
        # Dashboard
        cv2.putText(image, f"Back: {int(back_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        
        # Mise à jour globale
        self.stage = entry['state']
    
    def process_frame(self, image, landmarks, exercise_name):
        self.feedback = "WAITING..."
        self.tracked_joints = []
        self.skeleton_color = (100, 100, 100)
        
        try:
            if exercise_name == 'pompes':
                self.analyze_pompes(landmarks, image)
            elif exercise_name == 'squats':
                self.analyze_squats(landmarks, image)
            elif exercise_name == 'jumping_jacks':
                self.analyze_jumping_jacks(landmarks, image)
            elif exercise_name == 'lever_jambes':
                self.analyze_lever_jambes(landmarks, image)
            elif exercise_name == 'montee_genou':
                self.analyze_montee_genou(landmarks, image)
            else:
                self.feedback = f"UNKNOWN EXERCISE: {exercise_name}"
        except Exception as e:
            self.feedback = f"ERROR: {str(e)[:30]}"
        
        self.send_skeleton_to_interface(landmarks)
    
    def draw_dashboard(self, image, results):
        cv2.rectangle(image, (0,0), (350, 120), (245,117,16), -1)
        
        cv2.putText(image, 'REPS', (15,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, str(self.counter), (10,80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
        
        cv2.putText(image, 'STATE', (130,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, self.stage, (120,80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
        
        color_feedback = (0,255,0) if "OK" in self.feedback or "GO" in self.feedback or "PERFECT" in self.feedback else (0,0,255) if "FORWARD" in self.feedback or "BENT" in self.feedback or "DEEPER" in self.feedback or "STRAIGHT" in self.feedback or "RAISE" in self.feedback or "STRAIGHTEN" in self.feedback else (0, 165, 255)
        cv2.rectangle(image, (0, 680), (1280, 720), color_feedback, -1)
        cv2.putText(image, self.feedback, (400, 710), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)

        if results.pose_landmarks is not None:
            self.draw_colored_skeleton(image, results.pose_landmarks.landmark, self.skeleton_color)
            
            landmarks = results.pose_landmarks.landmark
            for joint_name, joint_color in self.tracked_joints:
                try:
                    landmark = landmarks[self.mp_pose.PoseLandmark[joint_name].value]
                    h, w, _ = image.shape
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(image, (x, y), 10, joint_color, -1)
                    cv2.circle(image, (x, y), 10, (0, 0, 0), 2)
                except:
                    pass