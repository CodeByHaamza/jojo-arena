# Contribuer

Merci de ton aide ! JoJo Arena est un fan game gratuit, non officiel et sans but lucratif.

## Démarrer

```
make install   # crée .venv et installe tout
make hooks     # lint et tests rapides avant chaque commit
make run       # lance le jeu
```

Sans `make`, voir les commandes équivalentes dans le README.

## Avant de proposer une modification

- `make check` doit passer (lint, puis tous les tests). La CI le refait sur GitHub.
- Une modification de gameplay suit le [GDD](docs/GDD.md). S'il est ambigu, ouvre une discussion plutôt que d'inventer.
- Les valeurs d'équilibrage vont dans les fichiers de données (kits, `combat/rules.toml`), jamais dans le code.
- `engine/` et `combat/` ne citent jamais JoJo, et `combat/` n'importe pas pygame.
- Ajoute un test pour toute logique nouvelle (`tests/`).
- `make screens` montre tous les écrans d'un coup dans `screenshots/tour/`.

Pour aller plus loin :
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) : l'organisation du code ;
- [docs/KITS.md](docs/KITS.md) : tous les champs d'un kit ;
- [docs/ROADMAP.md](docs/ROADMAP.md) : ce qui reste à faire ;
- [docs/INFRA.md](docs/INFRA.md) : les tests, la CI, Docker, les crochets, les Releases ;
- [docs/AGENTS.md](docs/AGENTS.md) : découper le travail entre agents, et les skills.

`make hooks` installe aussi un crochet `commit-msg` : message conventionnel, sujet de
72 caractères maximum, et aucune mention d'un outil d'IA dans l'historique.

Sans Python local, `docker compose run --rm check` lance le lint et les tests dans un
conteneur, exactement comme la CI.

## Style

- Code, noms et commentaires en anglais ; textes du jeu en français et en anglais, dans `ui/text.py` (tables `FR` et `EN`, lues au moment de dessiner : `text.FIGHT`). Dans les données, la traduction anglaise d'un champ texte s'écrit à côté avec le suffixe `_en` (`label_en`, `info_en`, `role_en`…).
- Messages de commit courts et conventionnels : `feat: ...`, `fix: ...`, `refactor: ...`, `docs: ...`, `test: ...`, `chore: ...`. Un commit par étape logique.
- Formatage et lint : `ruff` (`make format` corrige ce qui peut l'être).

## Images

Les sprites des persos sont générés depuis leur fiche (`characters/looks/<id>.toml`) par `make sprites`. Une planche dessinée à la main peut remplacer une planche générée sans toucher au code.

### Glossaire

Le glossaire du jeu (menu principal) lit `characters/lore/part<n>.toml`, un fichier par partie : `[[terms]]` (termes du lore, avec une icône), `[[characters]]` (`fighter` = le perso dont le sprite s'affiche, `stand`, `family`, `name_origin`) et `[[stands]]` (`sprite`, `user`, `stats` = six lettres de A à E : puissance, vitesse, portée, endurance, précision, potentiel). Chaque texte a sa traduction `_en`. Un test vérifie que chaque perso jouable et son Stand ont leur fiche : on remplit le glossaire au fur et à mesure qu'on ajoute des persos. Sources : JoJo Wiki, le manga, l'anime.

### Icônes

Les petites images (emblèmes des parties, icônes du glossaire) sont dessinées en texte dans `tools/icons/<id>.toml` : une palette (une lettre par couleur, `.` transparent) et les lignes de pixels. `make icons` les transforme en PNG dans `assets/icons/`. Les emblèmes des parties sont choisis dans `characters/parts.toml`.

### Animations par images-clés

Une fiche de look peut écrire ses propres animations, pose par pose, au lieu de celles du générateur :

```toml
[anims.special_splash]   # remplace l'animation de ce nom, ou en ajoute une nouvelle
fps = 12
phases = [2, 1, 2]       # poses clés du démarrage, de la phase active, de la récupération
tween = 1                # images intermédiaires calculées après chaque pose clé

[[anims.special_splash.right]]   # une table par pose clé, pour down, up et right
lean = -1
hand_r = [3, -9]                 # décalages en pixels depuis la position de repos
```

- Les réglages d'une pose sont ceux de `Pose` dans `tools/spritegen/skeleton.py` : `bob`, `lean`, `head`, `hand_l`, `hand_r`, `foot_l`, `foot_r`, `big_hand_r`.
- Une vue absente copie une autre (`up` copie `down`, et inversement ; `right` copie `down`).
- Le coup choisit l'animation dans son kit : `anim = "special_splash"`.
