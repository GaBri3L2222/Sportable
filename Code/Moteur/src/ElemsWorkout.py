from abc import ABC, abstractmethod

class ElemsWorkout(ABC):
    @abstractmethod
    def GetID(self):
        pass
    
    @abstractmethod
    def SetDone(self):
        pass
    
    @abstractmethod
    def Update(self):
        pass

    @abstractmethod
    def GetType(self):
        pass
    
    @abstractmethod
    def GetDone(self):
        pass
    
class Exercice(ElemsWorkout):

    def __init__(self, id: int, nom: str = "Pompes", series: int = 1, repetitions: int = 10, done: bool = False):
        self.__nom = nom
        self.__series = series
        self.__repetitions = repetitions
        self.__id = id
        self.__done = done
        
    def Update(self, nom: str, series: int, repetitions: int):
        self.__nom = nom
        self.__series = series
        self.__repetitions = repetitions

    def SetDone(self):
        self.__done = True
        
    def GetID(self):
        return self.__id
    
    def GetType(self):
        return "exercice"
    
    def GetNom(self):
        return self.__nom
    
    def GetSeries(self):
        return self.__series
    
    def GetRepetitions(self):
        return self.__repetitions
    
    def GetDone(self):
        return self.__done
    
        
class Pause(ElemsWorkout):
    
    def __init__(self, id: int, duree_secondes: int = 30, done: bool = False):
        self.__id = id
        self.__done = done
        self.__duree = duree_secondes

    def Update(self, duree: int):
        self.__duree = duree

    def SetDone(self):
        self.__done = True
        
    def GetID(self):
        return self.__id
    
    def GetType(self):
        return "pause"
    
    def GetDuree(self):
        return self.__duree
    
    def GetDone(self):
        return self.__done