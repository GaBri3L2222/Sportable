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

Les **trois agents** doivent être lancés **séparément**, chacun dans un terminal, avec la commande suivante :

```bash
python main.py --verbose --port 5670 --device "Wi-Fi"
