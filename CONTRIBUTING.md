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
- [docs/ROADMAP.md](docs/ROADMAP.md) : ce qui reste à faire.

## Style

- Code, noms et commentaires en anglais ; textes du jeu en français, dans `ui/text.py`.
- Messages de commit courts et conventionnels : `feat: ...`, `fix: ...`, `refactor: ...`, `docs: ...`, `test: ...`, `chore: ...`. Un commit par étape logique.
- Formatage et lint : `ruff` (`make format` corrige ce qui peut l'être).

## Images

Les sprites des persos sont générés depuis leur fiche (`characters/looks/<id>.toml`) par `make sprites`. Une planche dessinée à la main peut remplacer une planche générée sans toucher au code.
