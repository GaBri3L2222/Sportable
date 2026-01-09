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


    # services
    def Settotaldisplay(self, sender_agent_name, sender_agent_uuid, Displayjson):
        pass
        # add code here if needed


