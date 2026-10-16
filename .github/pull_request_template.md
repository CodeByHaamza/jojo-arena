## Ce que ça change

<!-- Une ou deux phrases, côté joueur : ce qu'on voit ou ce qu'on sent en jouant. -->

## Pourquoi

<!-- Le point du GDD ou de la ROADMAP concerné, ou le bug corrigé (fixes #123). -->

## Comment vérifier

<!-- Les commandes ou la manip : `make training P1=jotaro_p3 P2=dio_p3`, puis... -->

## Checklist

- [ ] `make check` passe (lint, format, tous les tests)
- [ ] Une modification de gameplay suit le [GDD](../docs/GDD.md) ; sinon, le GDD est mis à jour dans la même PR
- [ ] Les valeurs d'équilibrage sont dans les fichiers de données (kits, `combat/rules.toml`), pas dans le code
- [ ] `engine/` et `combat/` ne citent pas JoJo, et `combat/` n'importe pas pygame
- [ ] Toute logique nouvelle a son test dans `tests/`
- [ ] Les textes à l'écran existent en français **et** en anglais (`ui/text.py`, suffixe `_en` dans les données)
- [ ] La doc touchée est à jour (README, ROADMAP, KITS, ARCHITECTURE)

## Captures

<!-- Pour un changement visible : avant / après. `make screens` fait la tournée complète. -->
