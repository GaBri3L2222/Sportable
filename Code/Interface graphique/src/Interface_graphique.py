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
import json
import threading
import webview
import os


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
        self.exercises = []  # List of exercises: {"name": str, "reps": int, "sets": int}
        self.current_exercise_index = 0
        
        # Local rest timer variables
        self.local_rest_seconds = None
        self.local_rest_active = False
        self._last_rest_item_key = None
        
    def initialize_gui(self):
        """Initialize and show the GUI using pywebview"""
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(script_dir, 'interface.html')
        
        # Create the API bridge
        api = Api(self)
        
        # Create and start the window
        self.window = webview.create_window(
            'Appli Sport Fonctionnelle',
            html_path,
            js_api=api,
            width=1200,
            height=800,
            resizable=True
        )
        
        # Start the webview on the main thread (blocking call)
        # This should be the last call in your main script
        webview.start(debug=True)
            
    def on_exercice_added(self, sender_agent_name, sender_agent_uuid, exercise_id):
        """Service callback when an exercise is added in Moteur"""
        print(f"Received exercice added with ID: {exercise_id}")
        if len(self.exercises) > 0:
            self.exercises[-1]["id"] = exercise_id
    
    def add_exercise(self, exercise_name, reps, sets):
        """Add exercise to the list"""
        try:
            result = igs.service_call("Moteur", "addExercice", (), "")
        except:
            result = None
            
        self.exercises.append({
            "type": "exercice",
            "nom": exercise_name,
            "series": sets,
            "repetitions": reps,
            "id": result,
            "done": "false"
        })

    def remove_exercise(self, index):
        """Supprime un élément (exercice ou pause)"""
        if 0 <= index < len(self.exercises):
            item = self.exercises.pop(index)
            try:
                elem_id = item.get("id")
                print(f"Removing element with ID: {elem_id}")
                if item.get("type") == "pause":
                    igs.service_call("Moteur", "removeRecuperation", elem_id, "")
                else:
                    igs.service_call("Moteur", "removeExercice", elem_id, "")
            except:
                pass

    def start_workout(self):
        """Start the workout session"""
        if len(self.exercises) > 0:
            self.current_exercise_index = 0
            js = {'nom': 'Séance', 'elements': self.exercises}
            try:
                igs.service_call("Moteur", "startWorkout", json.dumps(js), "")
            except:
                pass

    def stop_workout(self):
        """Stop the workout session"""
        try:
            js = igs.service_call("Moteur", "stopWorkout", None, "")
            # self.exercises = js.elements # TODO
        except:
            pass
                
    def add_rest(self, duration_seconds: int):
        """Add a rest period"""
        try:
            result = igs.service_call("Moteur", "addRecuperation", None, "")
        except:
            result = None
        self.exercises.append({
            "type": "pause",
            "duree_secondes": int(duration_seconds),
            "id": result,
            "done": "false"
        })
                
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
        except:
            pass


class Api:
    """API bridge between JavaScript and Python"""
    
    def __init__(self, interface):
        self.interface = interface
    
    def add_exercise(self, name, reps, sets):
        """Add an exercise"""
        self.interface.add_exercise(name, reps, sets)
        return True
    
    def add_rest(self, duration):
        """Add a rest period"""
        self.interface.add_rest(duration)
        return True
    
    def remove_exercise(self, index):
        """Remove an exercise at index"""
        self.interface.remove_exercise(index)
        return True
    
    def get_exercises(self):
        """Get the list of exercises"""
        return self.interface.exercises
    
    def start_workout(self):
        """Start the workout"""
        self.interface.start_workout()
        return True
    
    def stop_workout(self):
        """Stop the workout"""
        self.interface.stop_workout()
        return True
    
    def get_execution_state(self):
        """Get current execution state for display"""
        interface = self.interface
        
        # Determine current exercise info
        current_exercise_name = "En attente..."
        if 0 <= interface.current_exercise_index < len(interface.exercises):
            exercise = interface.exercises[interface.current_exercise_index]
            if exercise.get("type") == "pause":
                duree = exercise.get("duree_secondes", 0)
                current_exercise_name = f"Pause : {duree} s"
            else:
                current_exercise_name = f"Exercice actuel: {exercise.get('nom', 'Exercice')}"
        
        # Handle rest time with local timer fallback
        rest_time = 0
        if interface.Rest_Time_RemainingI is not None:
            # Motor provides rest time
            try:
                rest_time = int(interface.Rest_Time_RemainingI)
            except:
                rest_time = 0
        elif (0 <= interface.current_exercise_index < len(interface.exercises) and 
            interface.exercises[interface.current_exercise_index].get("type") == "pause"):
            # Local rest timer for pause items
            if interface.local_rest_seconds is not None:
                rest_time = interface.local_rest_seconds
            else:
                # Initialize local rest timer
                duration = interface.exercises[interface.current_exercise_index].get("duree_secondes", 0)
                interface.local_rest_seconds = duration
                rest_time = duration
        
        return {
            'current_exercise_name': current_exercise_name,
            'reps_remaining': interface.Rep_RemainingI or 0,
            'sets_remaining': interface.Set_RemainingI or 0,
            'vision_state': interface.Vision_StateI or False,
            'feedback': interface.FeedbackI or "",
            'rest_time': rest_time,
            'current_index': interface.current_exercise_index,
            'total_exercises': len(interface.exercises),
            'skeleton_data': interface.SqueletteI
        }