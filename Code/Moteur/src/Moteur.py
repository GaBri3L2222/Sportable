#!/usr/bin/env -P /usr/bin:/usr/local/bin python3 -B
# coding: utf-8

#
#  Moteur.py
#  Moteur
#  Created by Sportable & Co on 2026/01/09
#
# "no description"
#
import ingescape as igs
import FonctionsJSON as funcJSON
import ElemsWorkout as EW
import json

## Etat du moteur ##
MoteurCOMPOSING = "composing"
MoteurRUNNING = "running"

## Type d'element ##
EXERCICE = "exercice"
PAUSE = "pause"

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    
class StructWorkout():
    
    def __init__(self):
        self.__elements = []
        self.__ID_global = 0
        
    def FindID(self, id: int, type: str):
        for element in self.__elements:
            if element.GetID() == id and element.GetType() == type:
                return element
        return None
    
    def GetNewID(self):
        self.__ID_global += 1
        return self.__ID_global
            
    def AddExercice(self):
        id = self.GetNewID()
        if self.FindID(id, EXERCICE) is not None:
            print(f"Erreur de AddExercice : l'exercice d'ID {id} existe déjà.")
            return
        self.__elements.append(EW.Exercice(id))
        print(f"Ajout de l'exercice d'ID {id}.")
        return id
        
    def RemoveExercice(self, id: int):
        element = self.FindID(id, EXERCICE)
        if element != None:
            del self.__elements[self.__elements.index(element)]
            print(f"Suppression de l'exercice d'ID {id}.")
            return True
        else:
            print(f"Erreur de RemoveExercice : l'exercice d'ID {id} n'existe pas.")
            return False
        
    def AddPause(self):
        id = self.GetNewID()
        if self.FindID(id, PAUSE) is not None:
            print(f"Erreur de AddPause : la pause d'ID {id} existe déjà.")
            return
        self.__elements.append(EW.Pause(id))
        print(f"Ajout de la pause d'ID {id}.")
        return id
        
    def RemovePause(self, id: int):
        element = self.FindID(id, PAUSE)
        if element != None:
            del self.__elements[self.__elements.index(element)]
            print(f"Suppression de la pause d'ID {id}.")
            return True
        else:
            print(f"Erreur de RemovePause : la pause d'ID {id} n'existe pas.")
            return False
        
    def UpdateAll(self, json: dict):
        size = len(json["elements"])
        if (size != len(self.__elements)):
            print("Erreur de mise à jour des exercices : taille différente entre le JSON et la structure interne.")
            return
        
        newArray = []
        for elemSW in self.__elements:
            elemJSON = funcJSON.findID(json, elemSW.GetID(), elemSW.GetType())
            if elemJSON is None:
                print(f"Erreur de mise à jour des exercices : l'élément d'ID {elemSW.GetID()} et de type {elemSW.GetType()} n'a pas été trouvé dans le JSON.")
                return
            
            if elemSW.GetType() == EXERCICE:
                newArray.append(EW.Exercice(id=elemSW.GetID(), nom=elemJSON["nom"], series=elemJSON["series"], repetitions=elemJSON["repetitions"]))
                    
            elif elemSW.GetType() == PAUSE:   
                newArray.append(EW.Pause(id=elemSW.GetID(), duree_secondes=elemJSON["duree_secondes"]))
                    
        self.__elements = newArray
        
    def GetSummaryJSON(self, ID_exo_en_cours: int, Exercice_en_cours: dict):
        elements_summary = []

        for elem in self.__elements:

            # On ignore les pauses
            if elem.GetType() != EXERCICE:
                continue

            # Cas 1 : exercice déjà terminé
            if elem.GetDone():
                elements_summary.append({
                    "type": elem.GetType(),
                    "nom": elem.GetNom(),
                    "series": elem.GetSeries(),
                    "repetitions": elem.GetRepetitions(),
                    "id": elem.GetID(),
                    "done": True
                })

            # Cas 2 : exercice en cours
            elif elem.GetID() == ID_exo_en_cours:
                elements_summary.append({
                    "type": elem.GetType(),
                    "nom": elem.GetNom(),
                    "series": elem.GetSeries() - Exercice_en_cours.get("séries_restantes", 0),
                    "repetitions": elem.GetRepetitions() - Exercice_en_cours.get("répétitions_restantes", 0),
                    "id": elem.GetID(),
                    "done": False
                })

            # Cas 3 : exercice pas encore commencé
            else:
                elements_summary.append({
                    "type": elem.GetType(),
                    "nom": elem.GetNom(),
                    "series": 0,
                    "repetitions": 0,
                    "id": elem.GetID(),
                    "done": False
                })

        summary = {
            "nom": "Séance",
            "elements": elements_summary
        }

        return json.dumps(summary, ensure_ascii=False)
    
    def ResetDone(self):
        for element in self.__elements:
            element.SetDone(False)
        
    def ToJSON(self):
        elements_json = []

        for elem in self.__elements:

            if elem.GetType() == EXERCICE:
                elements_json.append({
                    "type": elem.GetType(),
                    "nom": elem.GetNom(),
                    "series": elem.GetSeries(),
                    "repetitions": elem.GetRepetitions(),
                    "id": elem.GetID(),
                    "done": elem.GetDone()
                })

            elif elem.GetType() == PAUSE:
                elements_json.append({
                    "type": elem.GetType(),
                    "duree_secondes": elem.GetDuree(),
                    "id": elem.GetID(),
                    "done": elem.GetDone()
                })

        workout_json = {
            "nom": "Séance",
            "elements": elements_json
        }

        return json.dumps(workout_json, ensure_ascii=False)

    def GetNextElement(self):
        for element in self.__elements:
            if not element.GetDone():
                return element
        return None
    
class Moteur(metaclass=Singleton):
    def __init__(self):
        # inputs

        # outputs
        self._Current_ExerciceO = None
        self._Rep_RemainingO = None
        self._Set_RemainingO = None
        self._Rest_Time_RemainingO = None
        self._Session_StateO = MoteurCOMPOSING
        self._Workout_SummaryO = None
        
        # Variables internes
        self.__Pause_en_cours = {"id": -1, "temps_restant": 0}
        self.__Exercice_en_cours = {"id": -1, "séries_restantes": 0, "répétitions_restantes": 0}
        
        ## Le planning de la séance ##
        self.__Planning_workout = StructWorkout()

    # outputs
    @property
    def Current_ExerciceO(self):
        return self._Current_ExerciceO

    @Current_ExerciceO.setter
    def Current_ExerciceO(self, value):
        self._Current_ExerciceO = value
        if self._Current_ExerciceO is not None:
            igs.output_set_string("current_exercice", self._Current_ExerciceO)
            
    @property
    def Rep_RemainingO(self):
        return self._Rep_RemainingO

    @Rep_RemainingO.setter
    def Rep_RemainingO(self, value):
        self._Rep_RemainingO = value
        if self._Rep_RemainingO is not None:
            igs.output_set_int("rep_remaining", self._Rep_RemainingO)
            
    @property
    def Set_RemainingO(self):
        return self._Set_RemainingO

    @Set_RemainingO.setter
    def Set_RemainingO(self, value):
        self._Set_RemainingO = value
        if self._Set_RemainingO is not None:
            igs.output_set_int("set_remaining", self._Set_RemainingO)
            
    @property
    def Rest_Time_RemainingO(self):
        return self._Rest_Time_RemainingO

    @Rest_Time_RemainingO.setter
    def Rest_Time_RemainingO(self, value):
        self._Rest_Time_RemainingO = value
        if self._Rest_Time_RemainingO is not None:
            igs.output_set_int("rest_time_remaining", self._Rest_Time_RemainingO)
            
    @property
    def Session_StateO(self):
        return self._Session_StateO

    @Session_StateO.setter
    def Session_StateO(self, value):
        self._Session_StateO = value
        if self._Session_StateO is not None:
            igs.output_set_string("session_state", self._Session_StateO)
            
    @property
    def Workout_SummaryO(self):
        return self._Workout_SummaryO

    @Workout_SummaryO.setter
    def Workout_SummaryO(self, value):
        self._Workout_SummaryO = value
        if self._Workout_SummaryO is not None:
            igs.output_set_string("workout_summary", self._Workout_SummaryO)


    # SERVICES (fonctions appelées par l'interface graphique)
    
    def Stopworkout(self, sender_agent_name, sender_agent_uuid):
        if(sender_agent_name == "Interface graphique" or sender_agent_name == "Ingescape Circle"):
            
            if self.VerifyState(MoteurRUNNING):
                
                # On récupère le résumé de la session
                data = self.__Planning_workout.GetSummaryJSON(self.__Exercice_en_cours["id"], self.__Exercice_en_cours)
                
                # On envoie le résumé de la session au WhiteBoard
                self.Workout_SummaryO = data
                
                # On reset l'état d'avancement des exercices du fichier JSON 
                self.__Planning_workout.ResetDone()
                
                # On arrête la session en cours
                self.Session_StateO = MoteurCOMPOSING
                
                # On met à jour nos attributs internes
                self.__Exercice_en_cours["id"] = -1
                self.__Exercice_en_cours["séries_restantes"] = 0
                self.__Exercice_en_cours["répétitions_restantes"] = 0
                self.__Pause_en_cours["temps_restant"] = 0
                self.__Pause_en_cours["id"] = -1
                
                # On met à jour les derniers outputs
                self.Current_ExerciceO = None
                self.Rep_RemainingO = None
                self.Set_RemainingO = None
                self.Rest_Time_RemainingO = None
                
                print("Arrêt de la séance.")
            
            return self.__Planning_workout.ToJSON()
        else:
            print("Service Stopworkout appelé par un agent non autorisé :", sender_agent_name)
            
    def Startworkout(self, sender_agent_name, sender_agent_uuid, Displayjson):
        if(sender_agent_name == "Interface graphique" or sender_agent_name == "Ingescape Circle"):
            
            if self.VerifyState(MoteurCOMPOSING):
                
                # On met à jour le planning de la séance
                self.__Planning_workout.UpdateAll(json.loads(Displayjson))
            
                # On démarre la session en cours
                self.Session_StateO = MoteurRUNNING
                
                # On récupère le premier element du fichier JSON
                next_element = self.__Planning_workout.GetNextElement()
                
                if next_element is None:
                    print("Erreur de Startworkout : aucun exercice ou pause à effectuer.")
                    
                    # On arrête la session en cours
                    self.Session_StateO = MoteurCOMPOSING
                    return
                
                elif next_element.GetType() == EXERCICE:
                
                    # On met à jour nos attributs internes
                    self.__Exercice_en_cours["id"] = next_element.GetID()
                    self.__Exercice_en_cours["séries_restantes"] = next_element.GetSeries()
                    self.__Exercice_en_cours["répétitions_restantes"] = next_element.GetRepetitions()
                    
                    # On met à jour les outputs
                    self.Current_ExerciceO = next_element.GetNom()
                    self.Rep_RemainingO = self.__Exercice_en_cours["répétitions_restantes"]
                    self.Set_RemainingO = self.__Exercice_en_cours["séries_restantes"]
                    
                elif next_element.GetType() == PAUSE:
                    
                    # On met à jour nos attributs internes
                    self.__Pause_en_cours["id"] = next_element.GetID()
                    self.__Pause_en_cours["temps_restant"] = next_element.GetDuree()
                    
                    # On met à jour les outputs
                    self.Rest_Time_RemainingO = self.__Pause_en_cours["temps_restant"]
                    
                print("Démarrage de la séance.")
            
        else:
            print("Service Startworkout appelé par un agent non autorisé :", sender_agent_name)

    def Removerecuperation(self, sender_agent_name, sender_agent_uuid, Recuperationid):
        if(sender_agent_name == "Interface graphique" or sender_agent_name == "Ingescape Circle"):
            
            if self.VerifyState(MoteurCOMPOSING):
                
                print(f"Suppression de la récupération d'ID {Recuperationid} demandée par {sender_agent_name}.")
                # On retire la récupération
                bool = self.__Planning_workout.RemovePause(Recuperationid)
                
                # On retourne le planning mis à jour
                return bool
        else:
            print("Service Removerecuperation appelé par un agent non autorisé :", sender_agent_name)

    def Addrecuperation(self, sender_agent_name, sender_agent_uuid):
        if(sender_agent_name == "Interface graphique" or sender_agent_name == "Ingescape Circle"):
            
            if self.VerifyState(MoteurCOMPOSING):
                
                print(f"Ajout d'une récupération demandé par {sender_agent_name}.")
                # On ajoute la récupération
                newIDPause = self.__Planning_workout.AddPause()
                
                arguments = (newIDPause,)
                igs.service_call(sender_agent_name, "on_exercice_added", arguments, "")
                print(f"Service on_recuperation_added appelé avec l'ID {newIDPause}")
                
                # On retourne le planning mis à jour
                return newIDPause
        else:
            print("Service Addrecuperation appelé par un agent non autorisé :", sender_agent_name)

    def Addexercice(self, sender_agent_name, sender_agent_uuid):
        if(sender_agent_name == "Interface graphique" or sender_agent_name == "Ingescape Circle"):
            
            if self.VerifyState(MoteurCOMPOSING):
                
                # On ajoute l'exercice 
                newIDExo = self.__Planning_workout.AddExercice()
                
                arguments = (newIDExo,)
                igs.service_call(sender_agent_name, "on_exercice_added", arguments, "")
                print(f"Service on_exercice_added appelé avec l'ID {newIDExo}")
                
                # On retourne le planning mis à jour
                return newIDExo
        else:
            print("Service Addexercice appelé par un agent non autorisé :", sender_agent_name)

    def Removeexercice(self, sender_agent_name, sender_agent_uuid, Exerciceid):
        if(sender_agent_name == "Interface graphique" or sender_agent_name == "Ingescape Circle"):
            
            if self.VerifyState(MoteurCOMPOSING):
                
                print(f"Suppression de l'exercice d'ID {Exerciceid} demandée par {sender_agent_name}.")
                
                # On retire l'exercice 
                bool = self.__Planning_workout.RemoveExercice(Exerciceid)
                
                # On retourne le planning mis à jour
                return bool
        else:
            print("Service Removeexercice appelé par un agent non autorisé :", sender_agent_name)

    # Autres fonctions internes
    
    def VerifyState(self, senssionState):
        if self._Session_StateO != senssionState:
            if senssionState == MoteurRUNNING:
                print("Erreur : il n'y a pas session en cours.")
            elif senssionState == MoteurCOMPOSING:
                print("Erreur : une session est en cours.")
            else:
                print("Erreur : état de session inconnu.")
            return False 
        return True

    def StopworkoutIntra(self):
          
            # On récupère le résumé de la session
            data = self.__Planning_workout.GetSummaryJSON(self.__Exercice_en_cours["id"], self.__Exercice_en_cours)
            
            # On envoie le résumé de la session au WhiteBoard
            self.Workout_SummaryO = data
            
            # On reset l'état d'avancement des exercices du fichier JSON 
            self.__Planning_workout.ResetDone()
            
            # On arrête la session en cours
            self.Session_StateO = MoteurCOMPOSING
            
            # On met à jour nos attributs internes
            self.__Exercice_en_cours["id"] = -1
            self.__Exercice_en_cours["séries_restantes"] = 0
            self.__Exercice_en_cours["répétitions_restantes"] = 0
            self.__Pause_en_cours["temps_restant"] = 0
            self.__Pause_en_cours["id"] = -1
            
            # On met à jour les derniers outputs
            self.Current_ExerciceO = None
            self.Rep_RemainingO = None
            self.Set_RemainingO = None
            self.Rest_Time_RemainingO = None
            
            print("Arrêt de la séance.")
            
            return self.__Planning_workout.ToJSON()
    
    def DecrementReps(self):
        self.__Exercice_en_cours["répétitions_restantes"] -= 1
        self.Rep_RemainingO = self.__Exercice_en_cours["répétitions_restantes"]
        return self.__Exercice_en_cours["répétitions_restantes"]
        
    def DecrementSets(self):
        self.__Exercice_en_cours["séries_restantes"] -= 1
        self.Set_RemainingO = self.__Exercice_en_cours["séries_restantes"]
        return self.__Exercice_en_cours["séries_restantes"]
    
    def ResetReps(self, id: int):
        exercice = self.__Planning_workout.FindID(id, EXERCICE)
        if exercice is not None:
            self.__Exercice_en_cours["répétitions_restantes"] = exercice.GetRepetitions()
            self.Rep_RemainingO = self.__Exercice_en_cours["répétitions_restantes"]
            
    def SetDoneCurrentExercice(self):
        exercice = self.__Planning_workout.FindID(self.__Exercice_en_cours["id"], EXERCICE)
        if exercice is not None:
            exercice.SetDone(True)
          
    def SetDoneCurrentPause(self):
        pause = self.__Planning_workout.FindID(self.__Pause_en_cours["id"], PAUSE)
        if pause is not None:
            pause.SetDone(True)
      
    def GoNextElement(self):
        elemnt = self.__Planning_workout.GetNextElement()
        if elemnt is not None:
            
            if elemnt.GetType() == EXERCICE:
                # On met à jour les nouveaux attributs
                self.__Exercice_en_cours["id"] = elemnt.GetID()
                self.__Exercice_en_cours["séries_restantes"] = elemnt.GetSeries()
                self.__Exercice_en_cours["répétitions_restantes"] = elemnt.GetRepetitions()
                self.Current_ExerciceO = elemnt.GetNom()
                self.Set_RemainingO = elemnt.GetSeries()
                self.Rep_RemainingO = elemnt.GetRepetitions()
                
                # On met à jour les ancien attributs de pause
                self.__Pause_en_cours["temps_restant"] = 0
                self.__Pause_en_cours["id"] = -1
                self.Rest_Time_RemainingO = 0
                
                return EXERCICE
            
            elif elemnt.GetType() == PAUSE:
                # On met à jour les nouveaux attributs
                self.__Pause_en_cours["id"] = elemnt.GetID()
                self.__Pause_en_cours["temps_restant"] = elemnt.GetDuree()
                self.Rest_Time_RemainingO = elemnt.GetDuree()
                
                # On met à jour les ancien attributs d'exercice
                self.__Exercice_en_cours["id"] = -1
                self.__Exercice_en_cours["séries_restantes"] = 0
                self.__Exercice_en_cours["répétitions_restantes"] = 0
                self.Current_ExerciceO = "Pause"
                self.Rep_RemainingO = 0
                self.Set_RemainingO = 0
                
                return PAUSE
            
        return None
