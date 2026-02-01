import cv2
import mediapipe as mp
import numpy as np

# --- Initialisation ---
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# --- Fonction de calcul de l'angle ---
def calculate_angle(a, b, c):
    a = np.array(a) # Premier point
    b = np.array(b) # Sommet de l'angle
    c = np.array(c) # Dernier point
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
    return angle

# --- Fonction utilitaire pour récupérer les coords ---
def get_coords(landmarks, part_name):
    return [
        landmarks[mp_pose.PoseLandmark[part_name].value].x,
        landmarks[mp_pose.PoseLandmark[part_name].value].y
    ]

# --- Fonction pour dessiner un point articulé en couleur ---
def draw_joint(image, x, y, color, radius=8):
    h, w, _ = image.shape
    pixel_x = int(x * w)
    pixel_y = int(y * h)
    cv2.circle(image, (pixel_x, pixel_y), radius, color, -1)
    cv2.circle(image, (pixel_x, pixel_y), radius, (0,0,0), 2)

# --- Fonction pour dessiner le squelette coloré ---
def draw_colored_skeleton(image, landmarks, skeleton_color):
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

# --- Sélection de l'exercice ---
print("=" * 50)
print("EXERCICE AVANCE (VALIDATION 3 POINTS)")
print("=" * 50)
print("1. Pompes (Profil)")
print("2. Squats (Profil recommandé)")
print("3. Jumping Jacks (Face)")
print("4. Lever de jambes (Profil au sol)")
print("5. Montées de genou (Face)")

while True:
    choice = input("Choix (1-5) : ").strip()
    if choice == '1': exercise = 'pompes'; break
    elif choice == '2': exercise = 'squats'; break
    elif choice == '3': exercise = 'jumping_jacks'; break
    elif choice == '4': exercise = 'lever_jambes'; break
    elif choice == '5': exercise = 'montee_genou'; break

# --- Variables ---
counter = 0
stage = "up" if exercise in ['pompes', 'squats'] else "down"
feedback_list = [] # Liste des erreurs détectées

# Configuration Webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        # Miroir + Couleur
        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Initialiser les variables
        feedback = "EN ATTENTE..."
        tracked_joints = []
        skeleton_color = (100, 100, 100)  # Gris par défaut (pas de détection)
        form_is_valid = False
        
        try:
            landmarks = results.pose_landmarks.landmark
            h, w, _ = frame.shape
            
            # --- LOGIQUE PAR EXERCICE ---
            
            if exercise == 'pompes':
                # 1. Action: Coude (Amplitude)
                shoulder = get_coords(landmarks, "LEFT_SHOULDER")
                elbow = get_coords(landmarks, "LEFT_ELBOW")
                wrist = get_coords(landmarks, "LEFT_WRIST")
                elbow_angle = calculate_angle(shoulder, elbow, wrist)
                
                # 2. Forme: Dos (Epaule-Hanche-Genou) - Doit être ~180
                hip = get_coords(landmarks, "LEFT_HIP")
                knee = get_coords(landmarks, "LEFT_KNEE")
                back_angle = calculate_angle(shoulder, hip, knee)
                
                # 3. Forme: Jambes (Hanche-Genou-Cheville) - Doit être ~180
                ankle = get_coords(landmarks, "LEFT_ANKLE")
                leg_angle = calculate_angle(hip, knee, ankle)

                # Validation
                form_is_valid = back_angle > 150 and leg_angle > 150
                
                # Colorer le squelette
                skeleton_color = (0, 255, 0) if form_is_valid else (0, 165, 255)  # Vert ou Orange
                
                # Articulations trackées
                tracked_joints = [
                    ("LEFT_ELBOW", (0, 255, 255) if elbow_angle < 90 or elbow_angle > 160 else (0, 165, 255)),
                    ("LEFT_SHOULDER", (0, 255, 0) if back_angle > 150 else (0, 0, 255)),
                    ("LEFT_HIP", (0, 255, 0) if back_angle > 150 else (0, 0, 255)),
                    ("LEFT_KNEE", (0, 255, 0) if leg_angle > 150 else (0, 0, 255)),
                ]
                
                # Feedback visuel sur l'image
                cv2.putText(image, f"Coude: {int(elbow_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
                cv2.putText(image, f"Dos: {int(back_angle)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if back_angle > 150 else (0,0,255), 1)
                
                if not form_is_valid:
                    feedback = "DOS OU JAMBES PLIES !"
                else:
                    feedback = "FORME OK"
                    
                    if elbow_angle > 160:
                        stage = "up"
                    if elbow_angle < 90 and stage == "up":
                        stage = "down"
                        counter += 1

            elif exercise == 'squats':
                # Pour le squat de profil (côté gauche visible)
                
                # 1. Action: Genou (Flexion)
                hip = get_coords(landmarks, "LEFT_HIP")
                knee = get_coords(landmarks, "LEFT_KNEE")
                ankle = get_coords(landmarks, "LEFT_ANKLE")
                knee_angle = calculate_angle(hip, knee, ankle)
                
                # 2. Forme: Dos/Hanche (Epaule-Hanche-Genou)
                shoulder = get_coords(landmarks, "LEFT_SHOULDER")
                hip_angle = calculate_angle(shoulder, hip, knee)
                
                # 3. Forme: Profondeur (Hanche Y vs Genou Y)
                # On vérifie si la hanche descend proche du niveau du genou
                depth_check = hip[1] > (knee[1] - 0.1) # Y augmente vers le bas

                valid_form = hip_angle > 60 # Si < 60, le buste est trop penché
                
                # Colorer le squelette
                skeleton_color = (0, 255, 0) if valid_form and (depth_check or knee_angle < 100) else (0, 165, 255)
                form_is_valid = valid_form
                
                # Articulations trackées
                tracked_joints = [
                    ("LEFT_KNEE", (0, 255, 255) if knee_angle < 90 else (0, 255, 0) if knee_angle > 100 else (0, 165, 255)),
                    ("LEFT_HIP", (0, 255, 0) if hip_angle > 60 else (0, 0, 255)),
                    ("LEFT_ANKLE", (0, 165, 255)),
                ]
                
                cv2.putText(image, f"Genoux: {int(knee_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
                cv2.putText(image, f"Buste: {int(hip_angle)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if hip_angle > 60 else (0,0,255), 1)

                if not valid_form:
                    feedback = "BUSTE TROP PENCHE !"
                elif not depth_check and knee_angle < 100:
                    feedback = "DESCENDEZ PLUS BAS !"
                else:
                    feedback = "FORME OK"
                    if knee_angle > 160:
                        stage = "up"
                    if knee_angle < 90 and stage == "up" and valid_form:
                        stage = "down"
                        counter += 1

            elif exercise == 'jumping_jacks':
                # 1. Action: Epaules (Bras levés)
                # On calcule l'angle Bras vs Corps (approximé par Hanche-Epaule-Coude)
                l_shoulder = get_coords(landmarks, "LEFT_SHOULDER")
                l_elbow = get_coords(landmarks, "LEFT_ELBOW")
                l_hip = get_coords(landmarks, "LEFT_HIP")
                arm_angle = calculate_angle(l_hip, l_shoulder, l_elbow)
                
                # 2. Action: Jambes (Ecartement)
                # Angle entrejambe ou verticalité jambe
                l_knee = get_coords(landmarks, "LEFT_KNEE")
                leg_abduction = calculate_angle(l_shoulder, l_hip, l_knee) # Doit s'ouvrir
                
                # 3. Forme: Bras tendus (Coude)
                l_wrist = get_coords(landmarks, "LEFT_WRIST")
                elbow_straight = calculate_angle(l_shoulder, l_elbow, l_wrist)
                
                valid_form = elbow_straight > 140 # Bras pas trop pliés
                
                # Colorer le squelette
                skeleton_color = (0, 255, 0) if valid_form else (0, 165, 255)
                form_is_valid = valid_form
                
                # Articulations trackées
                tracked_joints = [
                    ("LEFT_SHOULDER", (0, 255, 0) if valid_form else (0, 0, 255)),
                    ("LEFT_ELBOW", (0, 255, 0) if elbow_straight > 140 else (0, 0, 255)),
                    ("LEFT_WRIST", (0, 255, 255) if arm_angle > 100 else (0, 165, 255)),
                    ("LEFT_HIP", (0, 165, 255)),
                ]
                
                cv2.putText(image, f"Bras Amp: {int(arm_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
                
                if not valid_form:
                    feedback = "TENDEZ LES BRAS !"
                else:
                    feedback = "GO !"
                    # Logique JJ:
                    # OPEN: Bras > 150° (levés) ET Jambe ouverte (>20° écart axe vert)
                    # CLOSED: Bras < 40° (baissés) ET Jambe fermée
                    
                    if arm_angle > 150 and leg_abduction > 175: # 180 = jambe droite, donc ici logique inverse selon coords
                         # Simplification pour JJ : on regarde juste si mains se touchent en haut ou bras très haut
                         pass

                    # Logique simplifiée robuste JJ
                    wrist_y = l_wrist[1]
                    shoulder_y = l_shoulder[1]
                    
                    if wrist_y < shoulder_y and leg_abduction > 10: # Bras en l'air
                        stage = "open"
                    
                    if wrist_y > shoulder_y and stage == "open":
                        stage = "close"
                        counter += 1

            elif exercise == 'lever_jambes':
                # 1. Action: Hanche (Angle Torse-Jambe)
                shoulder = get_coords(landmarks, "RIGHT_SHOULDER")
                hip = get_coords(landmarks, "RIGHT_HIP")
                knee = get_coords(landmarks, "RIGHT_KNEE")
                hip_angle = calculate_angle(shoulder, hip, knee)
                
                # 2. Forme: Genou (Jambe tendue)
                ankle = get_coords(landmarks, "RIGHT_ANKLE")
                knee_angle = calculate_angle(hip, knee, ankle)
                
                # 3. Stabilité: L'autre jambe (Gauche) doit rester au sol (approximatif)
                # Ou simplement vérifier que le dos ne décolle pas trop (Angle Epaule-Hanche vs Verticale)
                # Ici on va valider que le GENOU actif reste > 150 (jambe tendue)
                
                valid_form = knee_angle > 150
                
                # Colorer le squelette
                skeleton_color = (0, 255, 0) if valid_form else (0, 165, 255)
                form_is_valid = valid_form
                
                # Articulations trackées
                tracked_joints = [
                    ("RIGHT_HIP", (0, 255, 255) if hip_angle > 100 else (0, 165, 255)),
                    ("RIGHT_KNEE", (0, 255, 0) if knee_angle > 150 else (0, 0, 255)),
                    ("RIGHT_ANKLE", (0, 165, 255)),
                ]
                
                cv2.putText(image, f"Hanche: {int(hip_angle)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
                cv2.putText(image, f"Genou: {int(knee_angle)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if knee_angle > 150 else (0,0,255), 1)
                
                if not valid_form:
                    feedback = "JAMBE TROP PLIEE !"
                else:
                    feedback = "BONNE FORME"
                    if hip_angle > 160: # Jambe au sol
                        stage = "down"
                    if hip_angle < 100 and stage == "down" and valid_form: # Jambe levée à 90°
                        stage = "up"
                        counter += 1

            elif exercise == 'montee_genou':
                # 1. Action: Hauteur du genou (Doit monter proche de la hanche)
                l_hip = get_coords(landmarks, "LEFT_HIP")
                l_knee = get_coords(landmarks, "LEFT_KNEE")
                r_hip = get_coords(landmarks, "RIGHT_HIP")
                r_knee = get_coords(landmarks, "RIGHT_KNEE")
                
                # Calcul: génou Y vs hanche Y (en coordonnées normalized: Y augmente vers le bas)
                l_knee_height = l_hip[1] - l_knee[1]  # Positif = genou élevé
                r_knee_height = r_hip[1] - r_knee[1]
                
                # 2. Forme: Stabilité du buste (pas de penche excessif)
                shoulder = get_coords(landmarks, "LEFT_SHOULDER")
                hip = get_coords(landmarks, "LEFT_HIP")
                ankle = get_coords(landmarks, "LEFT_ANKLE")
                posture_angle = calculate_angle(shoulder, hip, ankle)  # Doit être ~180 (droit)
                
                valid_form = posture_angle > 160  # Buste droit
                
                # Hauteur minimale du genou (0.15 = 15% de la hauteur entre hanche et sol)
                knee_is_high = l_knee_height > 0.15 or r_knee_height > 0.15
                
                # Déterminer quel genou est plus haut
                if l_knee_height > r_knee_height:
                    active_knee = "LEFT_KNEE"
                    active_height = l_knee_height
                else:
                    active_knee = "RIGHT_KNEE"
                    active_height = r_knee_height
                
                # Colorer le squelette
                skeleton_color = (0, 255, 0) if valid_form and knee_is_high else (0, 165, 255)
                form_is_valid = valid_form
                
                # Articulations trackées
                tracked_joints = [
                    ("LEFT_KNEE", (0, 255, 255) if l_knee_height > 0.15 else (0, 165, 255)),
                    ("RIGHT_KNEE", (0, 255, 255) if r_knee_height > 0.15 else (0, 165, 255)),
                    ("LEFT_HIP", (0, 255, 0) if valid_form else (0, 0, 255)),
                ]
                
                cv2.putText(image, f"Genou L: {int(l_knee_height * 100)}", (10, 150), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
                cv2.putText(image, f"Genou R: {int(r_knee_height * 100)}", (10, 170), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
                cv2.putText(image, f"Posture: {int(posture_angle)}", (10, 190), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0) if valid_form else (0,0,255), 1)
                
                if not valid_form:
                    feedback = "BUSTE DROIT !"
                elif not knee_is_high:
                    feedback = "MONTEZ LES GENOUX !"
                else:
                    feedback = "PARFAIT !"
                    # Logique: au repos (genoux bas) -> en haut (genoux hauts)
                    if (l_knee_height > 0.15 or r_knee_height > 0.15) and valid_form:
                        if stage == "down":
                            stage = "up"
                    elif l_knee_height < 0.05 and r_knee_height < 0.05 and stage == "up":
                        stage = "down"
                        counter += 1

        except Exception as e:
            pass

        # --- DESSIN DU DASHBOARD ---
        # Fond
        cv2.rectangle(image, (0,0), (350, 120), (245,117,16), -1)
        
        # Reps
        cv2.putText(image, 'REPS', (15,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, str(counter), (10,80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
        
        # Stage
        cv2.putText(image, 'PHASE', (130,12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, stage, (120,80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
        
        # Feedback dynamique
        color_feedback = (0,255,0) if "OK" in feedback or "GO" in feedback else (0,0,255) if "PENCHE" in feedback or "PLIE" in feedback or "BASSE" in feedback else (0, 165, 255)
        cv2.rectangle(image, (0, 680), (1280, 720), color_feedback, -1)
        cv2.putText(image, feedback, (400, 710), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)

        # Dessin squelette coloré au lieu de MediaPipe défaut
        if results.pose_landmarks is not None:
            draw_colored_skeleton(image, results.pose_landmarks.landmark, skeleton_color)
            
            # Dessiner les articulations trackées en surbrillance
            for joint_name, joint_color in tracked_joints:
                try:
                    landmark = landmarks[mp_pose.PoseLandmark[joint_name].value]
                    h, w, _ = image.shape
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(image, (x, y), 10, joint_color, -1)
                    cv2.circle(image, (x, y), 10, (0, 0, 0), 2)
                except:
                    pass
        
        cv2.imshow('Mediapipe Pro Counter', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()