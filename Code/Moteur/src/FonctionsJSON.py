import json

## Constants globales ##

PATH_WORKOUT = "/DATA/workoutPlan.json"
EXERCICE = "exercice"
PAUSE = "pause"



## Fonctions de gestion de fichiers JSON ##

def read_json():
    with open(PATH_WORKOUT, "r") as f:
        return json.load(f)

def write_json(data):
    with open(PATH_WORKOUT, "w") as f:
        json.dump(data, f, indent=4)

def loadJson(data, f):
    json.dump(data, f, indent=4)

def findID(data, id_recherche, type_recherche):
    for element in data["elements"]:
        if element["id"] == id_recherche and element["type"] == type_recherche:
            return element
    return None
    
## Fonctions d'ajout de données dans le fichier JSON ##

# Pause de récupération
def AddRecuperationJSON(id: int):
    data = read_json()
    
    element = findID(data, id, PAUSE)
    if element is None:
        data["elements"].append({
            "type": PAUSE,
            "duree_secondes": 30,
            "id": id,
            "done": False
        })
        write_json(data)
        print(f"La pause de récupération avec l'ID {id} a été ajoutée dans le fichier JSON.")
    else :
        print(f"Erreur pour AddRecuperationJSON : l'ID de récupération {id} existe déjà pour une pause dans le fichier JSON.")


def RemoveRecuperationJSON(id: int):
    data = read_json()

    element = findID(data, id, PAUSE)
    if element is not None:
        data["elements"].remove(element)
        print(f"La pause de récupération avec l'ID {id} a été supprimée du fichier JSON.")
    else:
        print(f"Erreur pour RemoveRecuperationJSON : l'ID de récupération {id} n'existe pas pour une pause dans le fichier JSON.")        
    
    write_json(data)

# Exercice
def AddExerciceJSON(id: int):  
    data = read_json()
    
    element = findID(data, id, EXERCICE)
    if element is None:
        data["elements"].append({
            "type": EXERCICE,
            "nom": "Pompes",
            "repetitions": 10,
            "series": 1,
            "id": id,
            "done": False
        })
        write_json(data)
        print(f"L'exercice avec l'ID {id} a été ajouté dans le fichier JSON.")
    else :
        print(f"Erreur pour AddExerciceJSON : l'ID de l'exercice {id} existe déjà dans le fichier JSON.")

def RemoveExerciceJSON(id: int):
    data = read_json()

    element = findID(data, id, EXERCICE)
    if element is not None:
        data["elements"].remove(element)
        print(f"L'exercice avec l'ID {id} a été supprimé du fichier JSON.")
    else:
        print(f"Erreur pour RemoveExerciceJSON : l'ID de l'exercice {id} n'existe pas dans le fichier JSON.")

    write_json(data)

## Fonctions de reset de données dans le fichier JSON ##

def ResetDoneJSON():
    data = read_json()
    
    elements = data["elements"]
    for element in elements:
        if "done" in element:
            element["done"] = False

    write_json(data)

def ResetAllJSON():
    data = read_json()
    data = {"elements": []}
    write_json(data)
    
## Fonctions de lecture de données dans le fichier JSON ##

def ReadJSON():
    return read_json()

def ReadDoneJSON(Id_exo_en_cours: int, Exercice_en_cours: dict):
    data = read_json()
    
    elements = data["elements"]
    exercices_termine = {}
    for element in elements:
        if element["done"] and element["type"] != "pause":
            exercices_termine.add(element)
        else:
            if element["id"] == Id_exo_en_cours and element["type"] != "pause":
                elementCopie = element.copy()
                elementCopie["series"] -= Exercice_en_cours["séries_restantes"]
                elementCopie["repetitions"] -= Exercice_en_cours["répétitions_restantes"]
                exercices_termine.add(elementCopie)
            break;
    return exercices_termine

def ReadNextExerciceJSON():
    data = read_json()
    
    for element in data["elements"]:
        if not element["done"]:
            return element
    return None