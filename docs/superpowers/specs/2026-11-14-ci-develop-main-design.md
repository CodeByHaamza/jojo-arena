# CI : `develop` pour travailler, `main` pour publier

Design validé par le propriétaire le 14/11/2026.

## Pourquoi

La CI était trop lourde : chaque push sur une branche avec une PR tournait **deux fois**
(événement `push` + événement `pull_request`), chaque fois sous Windows **et** Ubuntu
(7 à 13 min par job), avec un `.exe` construit à chaque PR. Le propriétaire veut :

- les PR vers `develop` ;
- un merge sur `main` = une Release ;
- la CI lourde seulement sur `main` ;
- utiliser son serveur maison (dépôt `maison` : portable Ubuntu 26.04, Docker, 8 threads,
  7,1 Go de RAM, 15 conteneurs, alertes de température à 85 °C).

## Objectifs

- Une PR est testée **une fois par push**, sur le serveur maison, en quelques minutes.
- Un merge sur `main` publie la Release tout seul : tag, `.exe`, notes tirées du CHANGELOG.
- Personne d'extérieur ne peut exécuter de code sur le serveur maison.

## Non-objectifs

- Pas de notification Discord dans ce chantier (option proposée, pas encore choisie).
- Pas de changement du jeu ni des tests eux-mêmes.

## Anti-objectifs (échec même si ça « marche »)

- Une PR de fork qui tourne sur le serveur maison.
- Un secret (jeton GitHub) lisible depuis un job.
- Le runner qui affame les autres conteneurs ou fait chauffer le portable au point
  d'alerter.

## Approches envisagées

| Approche | Pour | Contre |
| --- | --- | --- |
| **A. Runner maison pour les PR des branches du dépôt, GitHub pour les forks et Windows** (choisie) | rapide, pas de file d'attente GitHub, gratuit | le serveur doit être allumé ; il faut sécuriser le runner |
| B. Tout chez GitHub, juste allégé (plus de double déclenchement, Ubuntu seul sur les PR) | zéro risque, rien à maintenir | garde la file d'attente que le propriétaire trouve lourde |
| C. Runner maison pour tout, y compris `main` | le plus rapide | impossible pour le `.exe` (PyInstaller doit tourner sous Windows) |

Choix : **A**. Le `.exe` reste sur le runner Windows de GitHub (gratuit pour un dépôt
public), et seulement sur `main`.

## Le design

### Branches

- `develop` : branche par défaut, cible de toutes les PR (Dependabot compris).
- `main` : protégée par une règle (ruleset) : pas de push direct, pas de force push, pas
  de suppression, entrée par PR uniquement. L'admin peut passer outre en cas d'urgence.

### Ce qui tourne

| Événement | Où | Quoi |
| --- | --- | --- |
| PR vers `develop` ou `main` depuis une branche du dépôt | serveur maison | lint + tous les tests (`-n auto`, 3 workers) + tournée de captures |
| PR depuis un fork | `ubuntu-latest` (GitHub), après approbation | lint + tous les tests |
| PR qui ne touche que `docs/` ou du Markdown | rien sauf le contrôle de forme | — |
| PR vers `main` | serveur maison | la version a monté par rapport au dernier tag, et le CHANGELOG a sa section |
| push sur `main` | Windows (GitHub) + serveur maison | tests Windows et Linux, `.exe`, smoke test, puis tag `vX.Y.Z` et Release |
| lundi 4 h 17 (et à la main) | serveur maison | bot d'équilibrage |
| PR qui touche un kit | serveur maison | bot d'équilibrage sur les persos touchés |

Plus de déclenchement sur `push` des branches de travail : la PR suffit. Plus de `.exe`
de test à chaque PR.

### Publier

`make release-pr VERSION=x.y.z` (outil `tools/release_pr.py`) :

1. vérifie qu'on est sur `develop`, propre et à jour ;
2. écrit la version dans `pyproject.toml` et `jojo_arena/__init__.py` ;
3. transforme la section « Non publié » du CHANGELOG en `## [x.y.z] - date` ;
4. committe `chore: release x.y.z`, pousse `develop` et ouvre la PR `develop` → `main`.

Au merge, `release.yml` lit la version : si le tag n'existe pas, il construit, teste, crée
le tag et la Release ; s'il existe déjà, il ne publie rien et le dit.

### Le runner maison

Il vit dans le dépôt `maison` (ses conventions s'appliquent : inventaire, déploiement par
`ops/deploy.sh`, noms en français).

- Image construite sur l'image officielle `ghcr.io/actions/actions-runner` (version
  épinglée), **sans sudo**, utilisateur `runner` non root.
- **Éphémère** : un job par enregistrement ; le conteneur redémarre, vide `_work` et se
  réenregistre.
- Plafonds : 3 CPU, 2 Go de RAM, `PYTEST_XDIST_AUTO_NUM_WORKERS=3`.
- **Aucun accès au socket Docker.**
- Le jeton GitHub (PAT à grain fin, « Administration : lecture et écriture » sur
  `jojo-arena` seulement) est un fichier du serveur en mode 600. L'entrée du conteneur le
  lit **en root**, demande un jeton d'enregistrement d'une heure, puis passe à
  l'utilisateur `runner` avec un environnement vide : un job ne peut lire ni le fichier
  ni la variable.
- **Garde côté serveur** : un script `job-started` (hook du runner, hors de portée des
  workflows) refuse tout job qui n'est pas un `push`, un `schedule`, un
  `workflow_dispatch` ou une `pull_request` **dont la tête est dans le dépôt lui-même**.
  Un fork qui réécrit `runs-on` est refusé avant la première étape.
- Réglage GitHub : approbation obligatoire pour les workflows de tous les contributeurs
  extérieurs.
- Cache pip et cache d'outils Python en volumes, pour que l'installation ne se refasse
  pas à chaque job.
- Entrées d'inventaire : `inventaire/conteneurs.json`, `inventaire/secrets.json` (le nom
  du fichier, jamais sa valeur).

### Limites connues

- Si le portable est éteint, les jobs attendent dans la file de GitHub et une PR ne peut
  pas être fusionnée tant qu'ils n'ont pas tourné. L'admin peut passer outre.
- ~~Le conteneur redémarré garde sa couche d'écriture.~~ Corrigé à la relecture du
  15/11 : une branche du dépôt n'est pas forcément écrite par le propriétaire (Dependabot,
  dépendances non épinglées). L'entrée vide tout ce que `runner` peut écrire et recopie
  le runner depuis un exemplaire à root ; plus aucun volume de cache (environ une minute
  de téléchargement par job).
- Le job Linux de la release n'a qu'un jeton en lecture ; seul le job Windows publie.

## Laissé au constructeur

- La version exacte de l'image `actions-runner` à épingler.
- Le nom du label du runner (`maison`).
- Les noms des jobs requis dans la règle de `main`.
