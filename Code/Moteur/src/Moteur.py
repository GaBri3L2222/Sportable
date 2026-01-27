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

## Variables globales ##
Id_exo_en_cours = -1 # un exercice ou une pause
Exercice_en_cours = {"séries_restantes": 0, "répétitions_restantes": 0}
Pause_en_cours = {"temps_restant": 0}

ID_exo_global = [0]
ID_pause_global = [0]

## Etat du moteur ##
MoteurCOMPOSING = "composing"
MoteurRUNNING = "running"

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Moteur(metaclass=Singleton):
    def __init__(self):
        # inputs

        # outputs
        self._Current_ExerciceO = None
        self._Rep_RemainingO = None
        self._Set_RemainingO = None
        self._Rest_Time_RemainingO = None
        self._Session_StateO = None
        self._Workout_SummaryO = None
        
        # Variables internes
        self._ID_exo_global = [0]
        self._ID_pause_global = [0]
        self._Pause_en_cours = {"temps_restant": 0}
        self._Exercice_en_cours = {"séries_restantes": 0, "répétitions_restantes": 0}
        self._Id_exo_en_cours = -1 # un exercice ou une pause

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
        if(sender_agent_name == "Interface graphique"):
            
            if self.VerifyState(MoteurRUNNING):
                
                # On récupère le résumé de la session
                data = funcJSON.ReadDoneJSON(Id_exo_en_cours, Exercice_en_cours)
                
                # On envoie le résumé de la session au WhiteBoard
                self._Workout_SummaryO = data
                
                # On reset l'état d'avancement des exercices du fichier JSON 
                funcJSON.ResetDoneJSON()
                
                # On arrête la session en cours
                self._Session_StateO = MoteurCOMPOSING
                
                # On met à jour nos variables globales
                Id_exo_en_cours = -1
                Exercice_en_cours["séries_restantes"] = 0
                Exercice_en_cours["répétitions_restantes"] = 0
                Pause_en_cours["temps_restant"] = 0
            
            return funcJSON.ReadJSON()
        else:
            print("Service Stopworkout appelé par un agent non autorisé :", sender_agent_name)

    def Startworkout(self, sender_agent_name, sender_agent_uuid):
        if(sender_agent_name == "Interface graphique"):
            
            if self.VerifyState(MoteurCOMPOSING):
            
                # On démarre la session en cours
                self._Session_StateO = MoteurRUNNING
                
                # On récupère le premier exercice du fichier JSON
                next_exercice = funcJSON.ReadNextExerciceJSON()
                
                # On met à jour nos variables globales
                global Id_exo_en_cours
                Id_exo_en_cours = next_exercice["id"]
                global Exercice_en_cours
                Exercice_en_cours["séries_restantes"] = next_exercice["series"]
                Exercice_en_cours["répétitions_restantes"] = next_exercice["repetitions"]
                
                # On met à jour les outputs
                self._Current_ExerciceO = next_exercice["nom"]
                self._Rep_RemainingO = Exercice_en_cours["répétitions_restantes"]
                self._Set_RemainingO = Exercice_en_cours["séries_restantes"]
            
        else:
            print("Service Startworkout appelé par un agent non autorisé :", sender_agent_name)

    def Removerecuperation(self, sender_agent_name, sender_agent_uuid, Recuperationid):
        if(sender_agent_name == "Interface graphique"):
            
            if self.VerifyState(MoteurCOMPOSING):
                
                # On retire l'ID de la pause de récupération des IDs globaux
                self.RemoveIDPause(Recuperationid)
            
                # On retire la récupération du fichier JSON
                funcJSON.RemoveExerciceJSON(Recuperationid)
        else:
            print("Service Removerecuperation appelé par un agent non autorisé :", sender_agent_name)

    def Addrecuperation(self, sender_agent_name, sender_agent_uuid):
        if(sender_agent_name == "Interface graphique"):
            
            if self.VerifyState(MoteurCOMPOSING):
                funcJSON.AddRecuperationJSON(id=self.GetNewIDPause())
        else:
            print("Service Addrecuperation appelé par un agent non autorisé :", sender_agent_name)

    def Addexercice(self, sender_agent_name, sender_agent_uuid):
        if(sender_agent_name == "Interface graphique"):
            
            if self.VerifyState(MoteurCOMPOSING):
               funcJSON.AddExerciceJSON(id=self.GetNewIDExercice())
        else:
            print("Service Addexercice appelé par un agent non autorisé :", sender_agent_name)

    def Removeexercice(self, sender_agent_name, sender_agent_uuid, Exerciceid):
        if(sender_agent_name == "Interface graphique"):
            
            if self.VerifyState(MoteurCOMPOSING):
                
                # On retire l'ID de la pause de récupération des IDs globaux
                self.RemoveIDExercice(Exerciceid)
                
                # On retire l'exercice du fichier JSON
                funcJSON.RemoveExerciceJSON(Exerciceid)
        else:
            print("Service Removeexercice appelé par un agent non autorisé :", sender_agent_name)

    def VerifyState(self, senssionState):
        if self._Session_StateO != senssionState:
            match senssionState:
                case MoteurRUNNING:
                    print("Erreur : il n'y a pas session en cours.")
                case MoteurCOMPOSING:
                    print("Erreur : une session est en cours.")
                case _:
                    print("Erreur : état de session inconnu.")
            return False 
        return True

    def GetNewIDExercice(self):
        global ID_exo_global
        ID_exo_global.append(ID_exo_global[-1] + 1)
        return ID_exo_global[-1]
    
    def GetNewIDPause(self):
        global ID_pause_global
        ID_pause_global.append(ID_pause_global[-1] + 1)
        return ID_pause_global[-1]
    
    def FindIDExercice(self, id: int):
        return id in ID_exo_global
    
    def FindIDPause(self, id: int):
        return id in ID_pause_global
    
    def RemoveIDExercice(self, id: int):
        if self.FindIDExercice(id):
            global ID_exo_global
            ID_exo_global.remove(id)
            print(f"Suppresion de l'exercie d'ID {id} dans ID_exo_global")
        else:
            print(f"Erreur de RemoveIDExercice : l'ID {id} n'est pas présent dans ID_exo_global")
            
    def RemoveIDPause(self, id: int):
        if self.FindIDPause(id):
            global ID_pause_global
            ID_pause_global.remove(id)
            print(f"Suppresion de la pause d'ID {id} dans ID_pause_global")
        else:
            print(f"Erreur de RemoveIDPause : l'ID {id} n'est pas présent dans ID_pause_global")
    
    def VerifyCoherenceIDs(self):
        data = funcJSON.ReadJSON()
        for id in ID_exo_global:
            if funcJSON.findID(data, id, funcJSON.EXERCICE) == None:
                print(f"Erreur de cohérence : l'ID de l'exercice {id} n'existe pas dans le JSON.")
                return False
        for id in ID_pause_global:
            if funcJSON.findID(data, id, funcJSON.EXERCICE) == None:
                print(f"Erreur de cohérence : l'ID de la pause {id} n'existe pas dans le JSON.")
                return False
        return True
        
