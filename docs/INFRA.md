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
| Smoke test du `.exe` | données manquantes dans le paquet | sur `main` et à chaque tag |

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

`.github/workflows/ci.yml`, sur chaque push et chaque PR :

1. **lint** (Ubuntu, ~1 min) — répond vite, attrape l'essentiel.
2. **test** (Windows **et** Ubuntu) — toute la suite, avec la couverture. Windows parce
   que c'est là que le jeu est joué ; Ubuntu parce que c'est là que seront la plupart des
   contributeurs, et que ça attrape les suppositions de chemins.
3. **Tournée de captures** (Windows) — tous les écrans en artefact `screenshots`.
4. **test-exe** (sur `main`) — construit le `.exe` et le lance 600 images.

Deux réglages qui changent le quotidien : `concurrency` annule un run devenu inutile
quand on pousse à nouveau sur la même branche, et le cache pip économise l'installation.

## Publier

Voir la skill `cut-release`. En résumé : la version dans `pyproject.toml` **et**
`jojo_arena/__init__.py`, un tag `v*`, et `release.yml` fait le reste — il refuse
désormais de publier si la version et le tag ne correspondent pas.

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
