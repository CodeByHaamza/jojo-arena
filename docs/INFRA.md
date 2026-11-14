# Infra, qualité et maintenance

Comment le projet se construit, se vérifie et se publie. Ce qui existe déjà, et ce qui
reste à faire, dans l'ordre où ça vaut le coup.

## En une ligne

Un jeu solo en Python qui se distribue en **un seul `.exe` Windows**. Pas de serveur,
pas de base de données, pas de déploiement : la « prod », c'est une Release GitHub. Tout
l'effort d'infra sert donc à **une seule chose** — qu'on puisse changer le jeu vite sans
casser ce qui marche.

## Les cinq filets

| Filet | Ce qu'il attrape | Quand |
| --- | --- | --- |
| `ruff` (lint + format) | code mort, imports cassés, style | à chaque sauvegarde (hook), au commit, en CI |
| `pytest` (630 tests, 93 % de couverture) | la simulation, les menus, les données | au commit (rapides), en CI (tous) |
| Tournée de captures | texte qui se chevauche, HUD recouvert | en CI, artefact à regarder |
| Combats aléatoires (`test_fuzz`) | plantages dans des situations non prévues | en CI |
| Smoke test du `.exe` | données manquantes dans le paquet | à chaque merge sur `main` (release) |

Le plus précieux des cinq : la simulation est **déterministe** et **ne dépend pas de
pygame**, donc un combat entier se rejoue sans écran, dans un test, en millisecondes.
C'est ce qui rend les tests rapides et fiables ici. **À protéger avant tout le reste.**

## Avant de committer

```
make check      # lint, format, tous les tests - exactement ce que fait la CI
make hooks      # une fois : lint + tests rapides avant chaque commit, et message vérifié
```

`make hooks` installe deux crochets git :

- **pre-commit** : `ruff check`, `ruff format --check`, puis les tests rapides.
- **commit-msg** : refuse un message qui ne commence pas par `feat:`, `fix:`, `docs:`…,
  un sujet de plus de 72 caractères, et toute mention d'un outil d'IA dans l'historique
  (règle du projet, voir `CLAUDE.md`).

Un troisième crochet, côté Claude Code (`.claude/settings.json`), lance `ruff format`
sur chaque fichier Python juste après son écriture : la CI ne tombe plus jamais sur un
problème de formatage seul.

## Intégration continue

Deux branches (depuis le 14/11/2026, design dans
[`docs/superpowers/specs/2026-11-14-ci-develop-main-design.md`](superpowers/specs/2026-11-14-ci-develop-main-design.md)) :

- **`develop`**, la branche par défaut : toutes les pull requests y vont ;
- **`main`**, protégée : on n'y entre que par une pull request, et **chaque merge est une
  release**.

| Événement | Où | Quoi |
| --- | --- | --- |
| PR vers `develop` ou `main` depuis une branche du dépôt | serveur maison (runner `maison`) | `ci.yml` : lint, tous les tests (`-n auto`, 3 workers), tournée de captures |
| PR depuis un fork | Ubuntu de GitHub, **après approbation** | la même chose |
| PR qui ne touche que `docs/` ou du Markdown | rien (sauf `pull-request.yml`) | — |
| PR vers `main` | serveur maison | en plus : `tools/release_pr.py --check` (version nouvelle, section du CHANGELOG) |
| push sur `main` | serveur maison puis Windows de GitHub | `release.yml` : tests Linux avec couverture, tests Windows, `.exe`, smoke test, tag et Release |
| lundi, et PR qui touche un kit | serveur maison | `balance.yml` : le bot d'équilibrage |

Une PR ne tourne **qu'une fois par push** (plus de double déclenchement push + PR), et un
nouveau push annule le run en cours.

**Le runner maison** vit dans le dépôt `maison` (`jojo-runner/`) : un conteneur éphémère
qui **repart d'un runner neuf à chaque job** (rien de ce qu'un job écrit ne survit, ni
cache ni volume), sans `sudo`, sans socket Docker, plafonné à 3 CPU et 2 Go sans swap.
Le jeton GitHub qui l'enregistre n'est lu qu'en root, et aucun processus qui dure ne le
porte ; les jobs tournent sous un autre utilisateur, avec un environnement vide. Un
script « job-started » du runner refuse tout job qui ne vient pas de ce dépôt : une PR
de fork qui réécrirait `runs-on` ne s'exécute jamais sur le serveur. Le job Linux de la
release ne reçoit qu'un jeton en lecture : seul le job Windows, chez GitHub, publie.

**Si le serveur est éteint**, les jobs attendent dans la file de GitHub, et une PR vers
`main` ne peut pas être fusionnée tant que `check` n'a pas tourné. L'admin peut passer
outre la règle de `main` en cas d'urgence.

## Publier

Voir la skill `cut-release`. En résumé, depuis `develop` à jour :
`make release-pr VERSION=x.y.z`, puis on fusionne la PR qu'il ouvre ; `release.yml` crée
le tag et la Release. Une version déjà publiée ne republie rien.

## Docker

`docker compose run --rm check` : lint + tests dans une image Debian avec SDL en mode
muet. **Ce n'est pas pour jouer** — le jeu se joue depuis le `.exe` ou les sources. C'est
pour reproduire un échec de CI sans rien installer, et pour qu'un contributeur sous Linux
ou macOS vérifie son travail exactement comme la CI.

> **Pas encore vérifié en vrai** : le `Dockerfile` et le `docker-compose.yml` sont écrits
> et la configuration compose est valide (`docker compose config`), mais l'image n'a pas
> été construite — le démon Docker n'était pas lancé. La liste des bibliothèques SDL est à
> confirmer au premier `docker build`.

## Couverture

```
make coverage       # rapport en console + htmlcov/index.html
```

Au 16/10/2026 : **93 %** sur 11 843 lignes, 630 tests, un peu plus de 3 minutes.

La couverture est un **indicateur, pas un objectif**. Ce qui compte ici :
`jojo_arena/combat/` et `jojo_arena/characters/` doivent être très couverts (c'est la
règle du jeu, et c'est testable sans écran) ; `jojo_arena/ui/` l'est surtout par les
écrans que les tests ouvrent, ligne par ligne ça n'a pas de sens.

Un seuil bloquant n'a pas été mis volontairement : il pousse à écrire des tests qui
passent sur du code de dessin au lieu de tests qui vérifient des règles. Si on en veut
un, le mettre **sur `combat/` seulement**.

## Contribuer

- `.github/pull_request_template.md` : la checklist du projet (GDD, données en TOML, pas
  de JoJo dans `engine/`, textes FR + EN, un test).
- `.github/ISSUE_TEMPLATE/` : un gabarit bug (qui **demande le replay** : F9 en combat,
  et le bug est reproductible à l'image près) et un gabarit idée.
- `.github/dependabot.yml` : mises à jour groupées, une fois par mois, trois PR max.

## Ce qui reste à faire, par ordre d'intérêt

1. **Test de non-régression de déterminisme** : garder deux ou trois replays courts dans
   `tests/replays/` et vérifier en CI qu'ils donnent exactement le même état final. C'est
   le filet qui manque sur la propriété la plus importante du projet.
2. **Test de référence d'images** (golden screenshots) sur deux ou trois écrans stables :
   compare la capture à une image de référence, tolérance zéro. Attrape les régressions
   visuelles que personne ne va voir à l'œil.
3. **Budget de performance** : un test qui mesure le temps de 1000 pas de simulation et
   échoue s'il double. Le jeu doit tenir 60 Hz sur une machine modeste.
4. **`make check` incrémental** : ne lancer que les tests touchés par le diff, pour que le
   pre-commit reste sous 10 secondes quand la suite grossira.
5. **Signature du `.exe`** : Windows SmartScreen effraie les joueurs. Un certificat coûte
   cher ; à défaut, documenter « Informations complémentaires → Exécuter quand même » dans
   la Release.
6. **Journal des changements** : `CHANGELOG.md` tenu à la main, lu par les joueurs, repris
   dans les notes de Release.
