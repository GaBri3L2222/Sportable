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

    # services
    def Stopworkout(self, sender_agent_name, sender_agent_uuid):
        pass
        # add code here if needed

    def Startworkout(self, sender_agent_name, sender_agent_uuid):
        pass
        # add code here if needed

    def Removerecuperation(self, sender_agent_name, sender_agent_uuid, Recuperationid):
        pass
        # add code here if needed

    def Addrecuperation(self, sender_agent_name, sender_agent_uuid):
        pass
        # add code here if needed

    def Addexercice(self, sender_agent_name, sender_agent_uuid):
        pass
        # add code here if needed

    def Removeexercice(self, sender_agent_name, sender_agent_uuid, Exerciceid):
        pass
        # add code here if needed


