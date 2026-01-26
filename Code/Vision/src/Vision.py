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


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Vision(metaclass=Singleton):
    def __init__(self):
        # Initialisation MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        # inputs
        self.Current_ExerciceI = None

        # outputs
        self._SqueletteO = None
        self._Vision_StateO = None
        self._FeedbackO = None
        
        # Variables de session
        self.counter = 0
        self.stage = "down"
        self.feedback = "EN ATTENTE..."
        self.tracked_joints = []
        self.skeleton_color = (100, 100, 100)

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
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
        return angle

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
        
        # Connexions du squelette MediaPipe
        connections = [
            (11, 13), (13, 15),  # Bras gauche
            (12, 14), (14, 16),  # Bras droit
            (11, 23), (12, 24),  # Torse vers hanches
            (23, 24),             # Hanches
            (23, 25), (25, 27),  # Jambe gauche
            (24, 26), (26, 28),  # Jambe droite
            (11, 12),             # Épaules
            (9, 10),              # Yeux
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
        
        hip = self.get_coords(landmarks, "LEFT_HIP")
        knee = self.get_coords(landmarks, "LEFT_KNEE")
        back_angle = self.calculate_angle(shoulder, hip, knee)
        
        ankle = self.get_coords(landmarks, "LEFT_ANKLE")
        leg_angle = self.calculate_angle(hip, knee, ankle)

        form_is_valid = back_angle > 150 and leg_angle > 150
        
        self.skeleton_color = (0, 255, 0) if form_is_valid else (0, 165, 255)
        
        self.tracked_joints = [
            ("LEFT_ELBOW", (0, 255, 255) if elbow_angle < 90 or elbow_angle > 160 else (0, 165, 255)),
            ("LEFT_SHOULDER", (0, 255, 0) if back_angle > 150 else (0, 0, 255)),
            ("LEFT_HIP", (0, 255, 0) if back_angle > 150 else (0, 0, 255)),
            ("LEFT_KNEE", (0, 255, 0) if leg_angle > 150 else (0, 0, 255)),
        ]
        
        cv2.putText(image, f"Coude: {int(elbow_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Dos: {int(back_angle)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if back_angle > 150 else (0,0,255), 1)
        
        if not form_is_valid:
            self.feedback = "DOS OU JAMBES PLIES !"
        else:
            self.feedback = "FORME OK"
            
            if elbow_angle > 160:
                self.stage = "up"
            if elbow_angle < 90 and self.stage == "up":
                self.stage = "down"
                self.counter += 1
                self.set_Rep_ValidatedO()

    def analyze_squats(self, landmarks, image):
        hip = self.get_coords(landmarks, "LEFT_HIP")
        knee = self.get_coords(landmarks, "LEFT_KNEE")
        ankle = self.get_coords(landmarks, "LEFT_ANKLE")
        knee_angle = self.calculate_angle(hip, knee, ankle)
        
        shoulder = self.get_coords(landmarks, "LEFT_SHOULDER")
        hip_angle = self.calculate_angle(shoulder, hip, knee)
        
        depth_check = hip[1] > (knee[1] - 0.1)

        valid_form = hip_angle > 60
        
        self.skeleton_color = (0, 255, 0) if valid_form and (depth_check or knee_angle < 100) else (0, 165, 255)
        
        self.tracked_joints = [
            ("LEFT_KNEE", (0, 255, 255) if knee_angle < 90 else (0, 255, 0) if knee_angle > 100 else (0, 165, 255)),
            ("LEFT_HIP", (0, 255, 0) if hip_angle > 60 else (0, 0, 255)),
            ("LEFT_ANKLE", (0, 165, 255)),
        ]
        
        cv2.putText(image, f"Genoux: {int(knee_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Buste: {int(hip_angle)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if hip_angle > 60 else (0,0,255), 1)

        if not valid_form:
            self.feedback = "BUSTE TROP PENCHE !"
        elif not depth_check and knee_angle < 100:
            self.feedback = "DESCENDEZ PLUS BAS !"
        else:
            self.feedback = "FORME OK"
            if knee_angle > 160:
                self.stage = "up"
            if knee_angle < 90 and self.stage == "up" and valid_form:
                self.stage = "down"
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
        
        cv2.putText(image, f"Bras Amp: {int(arm_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        
        if not valid_form:
            self.feedback = "TENDEZ LES BRAS !"
        else:
            self.feedback = "GO !"
            
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
        
        cv2.putText(image, f"Hanche: {int(hip_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Genou: {int(knee_angle)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if knee_angle > 150 else (0,0,255), 1)
        
        if not valid_form:
            self.feedback = "JAMBE TROP PLIEE !"
        else:
            self.feedback = "BONNE FORME"
            if hip_angle > 160:
                self.stage = "down"
            if hip_angle < 100 and self.stage == "down" and valid_form:
                self.stage = "up"
                self.counter += 1
                self.set_Rep_ValidatedO()

    def analyze_montee_genou(self, landmarks, image):
        l_hip = self.get_coords(landmarks, "LEFT_HIP")
        l_knee = self.get_coords(landmarks, "LEFT_KNEE")
        r_hip = self.get_coords(landmarks, "RIGHT_HIP")
        r_knee = self.get_coords(landmarks, "RIGHT_KNEE")
        
        l_knee_height = l_hip[1] - l_knee[1]
        r_knee_height = r_hip[1] - r_knee[1]
        
        shoulder = self.get_coords(landmarks, "LEFT_SHOULDER")
        hip = self.get_coords(landmarks, "LEFT_HIP")
        ankle = self.get_coords(landmarks, "LEFT_ANKLE")
        posture_angle = self.calculate_angle(shoulder, hip, ankle)
        
        valid_form = posture_angle > 160
        knee_is_high = l_knee_height > 0.15 or r_knee_height > 0.15
        
        self.skeleton_color = (0, 255, 0) if valid_form and knee_is_high else (0, 165, 255)
        
        self.tracked_joints = [
            ("LEFT_KNEE", (0, 255, 255) if l_knee_height > 0.15 else (0, 165, 255)),
            ("RIGHT_KNEE", (0, 255, 255) if r_knee_height > 0.15 else (0, 165, 255)),
            ("LEFT_HIP", (0, 255, 0) if valid_form else (0, 0, 255)),
        ]
        
        cv2.putText(image, f"Genou L: {int(l_knee_height * 100)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Genou R: {int(r_knee_height * 100)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Posture: {int(posture_angle)}", (10, 190), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if valid_form else (0,0,255), 1)
        
        if not valid_form:
            self.feedback = "BUSTE DROIT !"
        elif not knee_is_high:
            self.feedback = "MONTEZ LES GENOUX !"
        else:
            self.feedback = "PARFAIT !"
            if (l_knee_height > 0.15 or r_knee_height > 0.15) and valid_form:
                if self.stage == "down":
                    self.stage = "up"
            elif l_knee_height < 0.05 and r_knee_height < 0.05 and self.stage == "up":
                self.stage = "down"
                self.counter += 1
                self.set_Rep_ValidatedO()

    def process_frame(self, image, landmarks, exercise_name):
        # Initialiser les variables
        self.feedback = "EN ATTENTE..."
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
                self.feedback = f"EXERCICE INCONNU: {exercise_name}"
        except Exception as e:
            self.feedback = f"ERREUR: {str(e)[:30]}"
        
        # Envoyer les landmarks à l'interface
        self.send_skeleton_to_interface(landmarks)
    
    def draw_dashboard(self, image, results):
        # Dashboard
        cv2.rectangle(image, (0,0), (350, 120), (245,117,16), -1)
        
        cv2.putText(image, 'REPS', (15,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, str(self.counter), (10,80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
        
        cv2.putText(image, 'PHASE', (130,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, self.stage, (120,80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
        
        color_feedback = (0,255,0) if "OK" in self.feedback or "GO" in self.feedback or "PARFAIT" in self.feedback else (0,0,255) if "PENCHE" in self.feedback or "PLIE" in self.feedback or "BASSE" in self.feedback or "DROIT" in self.feedback or "MONTEZ" in self.feedback or "TENDEZ" in self.feedback else (0, 165, 255)
        cv2.rectangle(image, (0, 680), (1280, 720), color_feedback, -1)
        cv2.putText(image, self.feedback, (400, 710), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)

        # Squelette coloré
        if results.pose_landmarks is not None:
            self.draw_colored_skeleton(image, results.pose_landmarks.landmark, self.skeleton_color)
            
            # Articulations trackées
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