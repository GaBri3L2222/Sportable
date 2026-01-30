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
import time


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
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
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
        hip = self.get_coords(landmarks, "LEFT_HIP")
        knee = self.get_coords(landmarks, "LEFT_KNEE")
        ankle = self.get_coords(landmarks, "LEFT_ANKLE")
        knee_angle = self.calculate_angle(hip, knee, ankle)
        knee_angle = self.smooth_angle('squat_knee', knee_angle)

        shoulder = self.get_coords(landmarks, "LEFT_SHOULDER")
        hip_angle = self.calculate_angle(shoulder, hip, knee)
        hip_angle = self.smooth_angle('squat_hip', hip_angle)

        # Vérification de la profondeur du squat
        depth_check = hip[1] > (knee[1] - 0.1)

        valid_form = hip_angle > 60

        self.skeleton_color = (0, 255, 0) if valid_form and (depth_check or knee_angle < 100) else (0, 165, 255)
        
        self.tracked_joints = [
            ("LEFT_KNEE", (0, 255, 255) if knee_angle < 90 else (0, 255, 0) if knee_angle > 100 else (0, 165, 255)),
            ("LEFT_HIP", (0, 255, 0) if hip_angle > 60 else (0, 0, 255)),
            ("LEFT_ANKLE", (0, 165, 255)),
        ]
        
        cv2.putText(image, f"Knees: {int(knee_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Torso: {int(hip_angle)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if hip_angle > 60 else (0,0,255), 1)

        if not valid_form:
            self.feedback = "TORSO TOO FORWARD!"
        elif not depth_check and knee_angle < 100:
            self.feedback = "GO DEEPER!"
        else:
            self.feedback = "FORM OK"

            # FSM pour les squats avec 3 états: S1 (debout), S2 (mi-squat), S3 (bas)
            prev_state = self.fsm.get('squats', {}).get('state')
            t = {
                'S1_up': 32,
                'S2_low': 35,
                'S2_high': 65,
                'S3_low': 75,
                'S3_high': 95,
            }
            hyst = 3
            # Déterminer l'état actuel
            if prev_state == 'S1':
                if knee_angle > t['S2_low'] + hyst:
                    state = 'S2'
                else:
                    state = 'S1'
            elif prev_state == 'S2':
                if knee_angle > t['S3_low'] + hyst:
                    state = 'S3'
                elif knee_angle < t['S2_low'] - hyst:
                    state = 'S1'
                else:
                    state = 'S2'
            elif prev_state == 'S3':
                if knee_angle < t['S3_low'] - hyst:
                    state = 'S2'
                else:
                    state = 'S3'
            else:
                # Pour l'état initial
                if knee_angle < t['S1_up']:
                    state = 'S1'
                elif t['S2_low'] <= knee_angle <= t['S2_high']:
                    state = 'S2'
                elif t['S3_low'] <= knee_angle <= t['S3_high']:
                    state = 'S3'
                else:
                    state = 'S2'

            # Vérification des genoux au-delà des orteils
            try:
                toe = landmarks[self.mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value]
                knee_lm = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
                delta = 0.02
                knees_over_toes = knee_lm.x > toe.x + delta
                if knees_over_toes:
                    self.feedback = 'Knees over toes!'
            except Exception:
                pass

            self.fsm_append_state('squats', state)
            self.stage = state
            if self.fsm_check_and_count('squats') and valid_form:
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
        
        cv2.putText(image, f"Knee L: {int(l_knee_height * 100)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Knee R: {int(r_knee_height * 100)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(image, f"Posture: {int(posture_angle)}", (10, 190), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if valid_form else (0,0,255), 1)
        
        if not valid_form:
            self.feedback = "KEEP BACK STRAIGHT!"
        elif not knee_is_high:
            self.feedback = "RAISE YOUR KNEES!"
        else:
            self.feedback = "PERFECT!"
            if (l_knee_height > 0.15 or r_knee_height > 0.15) and valid_form:
                if self.stage == "down":
                    self.stage = "up"
            elif l_knee_height < 0.05 and r_knee_height < 0.05 and self.stage == "up":
                self.stage = "down"
                self.counter += 1
                self.set_Rep_ValidatedO()

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