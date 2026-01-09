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


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Vision(metaclass=Singleton):
    def __init__(self):
        # inputs
        self.Current_ExerciceI = None

        # outputs
        self._SqueletteO = None
        self._Vision_StateO = None

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

    # services
    def Start_Detection(self, sender_agent_name, sender_agent_uuid, Current_Exercice):
        pass
        # add code here if needed


