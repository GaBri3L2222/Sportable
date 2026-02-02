# Sportable

**Sportable** est une application de sport interactive permettant de **créer, modifier et exécuter une séance de sport**, tout en utilisant la **webcam de l’ordinateur** pour analyser les mouvements de l’utilisateur et fournir des **conseils sur l’exécution des exercices**.

L’analyse des mouvements repose sur la reconnaissance du squelette en temps réel grâce à **MediaPipe**.

---

## Fonctionnalités

- Création et édition de séances de sport personnalisées  
- Exécution guidée des séances  
- Analyse des mouvements via la webcam  
- Détection et suivi du squelette en temps réel  
- Synchronisation entre plusieurs agents via **Ingescape**

---

## Exercices implémentés

Les exercices actuellement disponibles sont :

- Pompes  
- Squats  
- Jumping Jacks  
- Montées de genoux  
- Levées de jambes  

---

## Architecture du projet

Le projet repose sur une architecture **multi-agents**, composée de trois agents distincts :

### Agent Vision
- Utilise **MediaPipe** pour la reconnaissance du squelette
- Analyse les mouvements de l’utilisateur via la webcam
- Envoie les informations de validation des répétitions au moteur
- Ouvre une fenêtre affichant le flux de la webcam avec le squelette détecté

### Agent Interface Graphique
- Permet à l’utilisateur d’interagir avec l’application
- Création, modification et lancement des séances de sport
- Affichage de l’état de la séance (exercice en cours, répétitions restantes, pauses, etc.)
- Ouvre la fenêtre principale de l’application

### Agent Moteur
- Gère la logique centrale de l’application
- Fait le lien entre l’agent Vision et l’Interface Graphique
- Maintient et met à jour la structure interne de la séance de sport
- Gère l’état d’avancement des exercices et des pauses

---

## Exécution du projet

### Prérequis
- Python installé
- Webcam fonctionnelle
- Ingescape installé et opérationnel

---

### Lancement des agents

Le projet nécessite le lancement de **trois agents distincts** :
- Vision  
- Moteur  
- Interface Graphique

Les trois agents doivent éxécutés avec la commande suivante :
```bash
python main.py --verbose --port PORT --device DEVICE
```
Avec **PORT** un port choisi (comme 5670), ainsi que **DEVICE** (comme "Wi-Fi")

**Important**  
Les trois agents doivent impérativement être **lancés avant toute interaction avec l’Interface Graphique**.  
Dans le cas contraire, des **problèmes de synchronisation** peuvent apparaître entre l’Interface Graphique et le Moteur.

---

### Configuration Ingescape

1. Ouvrir **Ingescape Circle**
2. Charger le fichier :
```bash
sportable.igssystem
```
3. Se connecter avec le même port et le même périphérique réseau que les agents
4. Ouvrir le **Whiteboard**

---

## Comportement au lancement

- L’agent **Vision** ouvre une fenêtre affichant :
- Le retour de la webcam
- Le squelette MediaPipe détecté sur la personne
- L’agent **Interface Graphique** ouvre la fenêtre principale de l’application Sportable

---

## Remarques

- Tous les agents doivent utiliser les mêmes paramètres réseau
- L’ordre de lancement des agents n'est pas essentiel
- Le Whiteboard permet d’observer et de déboguer les échanges entre agents

---

