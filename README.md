# Questionnaire de fin de stage — Octobre 2026

Conversion du formulaire Framaforms exporté (`nid=1564678`), sans dépendance à Framaforms lors des soumissions.

## Usage éphémère (20 minutes)

- Régler `OPENS_AT` et `CLOSES_AT` dans `.env` avec le décalage horaire, puis démarrer le conteneur.
- Le formulaire refuse les nouvelles soumissions hors de cet intervalle, mais `/admin` reste accessible pour exporter les résultats après fermeture.
- **Ne pas arrêter ni effacer le volume `data` avant récupération et vérification du CSV**.
- Vérifier le nombre de lignes, conserver une copie sécurisée et supprimer le volume lorsque la période de conservation décidée est terminée.
- Un dépôt GitHub, même privé, n’est pas recommandé pour les réponses d’élèves : une suppression ultérieure ne purge pas nécessairement l’historique Git.

## Installation via Docker Compose

1. Installer Docker et Docker Compose sur un serveur autorisé par l'établissement.
2. Dans ce dossier, créer un `.env` avec :
   ```
   ADMIN_PASSWORD=CHOISIR_UN_MOT_DE_PASSE_LONG_ET_UNIQUE
   SECRET_KEY=REMPLACER_PAR_UNE_CLE_ALEATOIRE_D_AU_MOINS_32_OCTETS
   ```
   Une clé peut être générée par `python -c "import secrets;print(secrets.token_hex(32))"`.
3. Exécuter `docker compose up -d --build`.
4. Exposer l'application derrière un reverse proxy HTTPS sécurisé, disposant d'une authentification adaptée pour `/admin`. Dans cette configuration, le conteneur écoute uniquement sur `127.0.0.1:8000` de l'hôte.
5. Formulaire : `/` ; interface enseignant : `/admin` ; export CSV : `/admin/export.csv`.

## Notes importantes

- Les réponses sont enregistrées dans `./data/responses.sqlite3`, sans nom, courriel ni IP stockée explicitement par l'application.
- La journalisation du reverse proxy ou de l'hébergeur peut toutefois enregistrer les adresses IP. Adapter la conservation des logs.
- Le formulaire comporte 3 questions d'inscription et 9 éléments sur la deuxième page, dont deux conditionnels. Les réponses cachées ne sont pas exigées.
- Dans le fichier Framaforms exporté, plusieurs choix Oui/Non utilisent par erreur des *valeurs internes* correspondant aux réponses de la question « ambiance ». Ce clone conserve les libellés visibles, mais normalise les valeurs en Oui/Non et répare la condition liée à « modifier ».
- Sauvegarder régulièrement le dossier `data`, définir une politique de suppression/rétention des réponses, restreindre les droits d'accès, faire valider l'hébergement et la protection des données par le responsable de traitement / DPO de l'établissement.
- Pas de limitation par IP : les élèves partageant une même IP peuvent soumettre simultanément. La capacité exacte dépend du serveur, de la configuration proxy et du nombre de requêtes : effectuer un test avant usage réel.
- Démo technique nécessitant une revue de sécurité avant mise en production : notamment protection CSRF, verrouillage des tentatives de connexion, supervision et HTTPS.

## Design et navigation

Interface élève responsive et accessible sur mobile, en deux étapes. Retour en arrière possible avant validation. Les réponses Oui/Non apparaissent comme des cartes sélectionnables ; les questions sur les absences et les changements d'organisation apparaissent uniquement quand elles s'appliquent. Le dépôt ne contient aucune réponse d'élève.

## Publier le code sur GitHub

Depuis un terminal avec Git et GitHub CLI (`gh`) connectés :

```bash
cd questionnaire-stage
 git init
 git add .
 git commit -m "Questionnaire de fin de stage"
 gh repo create questionnaire-stage --private --source=. --remote=origin --push
```

Le dépôt doit être **privé** pendant la revue de sécurité, même si le code pourra être publié après vérification. Le code sur GitHub ne suffit **pas** à faire fonctionner le formulaire : GitHub Pages héberge des sites statiques et n'exécute pas Flask/SQLite. Il faut donc aussi héberger le conteneur Docker sur un serveur autorisé.

**Ne pas stocker les réponses dans GitHub**, particulièrement les commentaires libres des élèves. La base SQLite doit rester dans le volume `data` hors du dépôt Git, être sauvegardée de façon chiffrée et faire l'objet d'une politique de rétention. Les exports CSV doivent rester dans un espace protégé.

## Vérifications avant mise en service

- Configurer un mot de passe administrateur long et unique et une `SECRET_KEY` aléatoire.
- Activer HTTPS avec reverse proxy, limiter le trafic vers `/admin`, renforcer la connexion administrateur (anti-bruteforce et CSRF).
- Obtenir la validation de l'établissement / DPO pour l'hébergement, la notice d'information et la durée de conservation.
- Tester 30 envois simultanés et les exports avec des données fictives.
- Ne pas activer l'accès Internet avant ces vérifications.
