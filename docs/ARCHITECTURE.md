# Architecture

Comment le code est rangé, et par où passe une image du jeu. À lire avant de toucher au moteur ou d'ajouter un perso.

## Les dossiers

| Dossier | Rôle | Règle |
| --- | --- | --- |
| `jojo_arena/engine/` | Boucle à pas fixe, affichage, entrées (clavier, manette), géométrie, sprites, police pixel | **Aucune référence à JoJo.** Réutilisable tel quel |
| `jojo_arena/combat/` | Règles du combat : combattants, coups, garde, jauges, clash, rounds, entraînement, interactions (temps arrêté) | Aucune référence à JoJo, **pas de pygame** : la simulation se teste sans écran |
| `jojo_arena/characters/` | Un kit par perso (`<id>.toml`), leur apparence (`looks/`), le roster (`roster.toml`) | Données ; un nouveau perso n'oblige pas à toucher au moteur |
| `jojo_arena/stages/` | Les arènes : données et dessin | |
| `jojo_arena/ui/` | Écrans (scènes), HUD, vue du combat, effets, onomatopées | Lit la simulation, ne la modifie jamais |
| `jojo_arena/assets/` | Planches de sprites générées | |
| `tools/` | Générateur de sprites, construction du `.exe`, tournée de captures | |
| `tests/` | Tests `pytest` | |

En cas de demande de retrait, on supprime `characters/`, `stages/` et `assets/`, et le moteur survit.

## Une image du jeu

1. `app.Game.run` lit les événements de pygame. Les touches et boutons vont à `engine.input.InputManager`.
2. À chaque pas logique (60 par seconde, pas fixe), la scène courante lit un `InputFrame` par joueur : direction, touches tenues, appuis depuis le pas précédent.
3. La scène de combat appelle `Rounds.step` (ou `Training.step`), qui appelle `Match.step` :
   - contrôle des combattants ;
   - temps arrêté ;
   - déplacements ;
   - coups qui sortent ;
   - projectiles et pièges ;
   - touches au corps à corps ;
   - clash ;
   - avance des états.
4. `Match.step` renvoie une liste d'`Event` (`hit`, `block`, `ko`, `time_stop`…). La simulation ne dessine rien et ne joue aucun son : elle **raconte** ce qui s'est passé.
5. La vue (`ui/fight_view.py`), le HUD et les effets réagissent à ces événements (étincelles, onomatopées, tremblement), puis dessinent l'état du match sur une surface de 480 × 270.
6. `engine.display` agrandit cette surface sans lissage jusqu'à la fenêtre.

La simulation est **déterministe** : mêmes entrées, même combat. C'est ce qui permettra le mode en ligne et ce qui rend les tests fiables.

## Un combattant

`combat/fighter.py` est une machine à états :

| État | Signification |
| --- | --- |
| `IDLE`, `WALK` | Libre de ses mouvements |
| `ATTACK` | Un coup est en cours |
| `GUARD`, `BLOCKSTUN`, `GUARD_BROKEN` | Garde |
| `DASH`, `POSE`, `SWITCH` | Dash, pose, sortie ou rappel du Stand |
| `CLASH` | Duel à marteler |
| `HITSTUN`, `KO` | Touché, K.O. |

Un coup a trois phases : démarrage (`startup_f`), actif (`active_f`, il peut toucher) et récupération (`recovery_f`). Les zones de frappe et de dégâts sont des cercles au sol. Un Stand sorti a son propre cercle de dégâts, et un coup sur le Stand blesse son manieur.

Les appuis sont mémorisés quelques images (le *buffer*), pour qu'un coup appuyé un peu tôt sorte quand même.

## Ajouter un perso

1. Son apparence : `characters/looks/<id>.toml`, puis `make sprites` (voir le README).
2. Son kit : `characters/<id>.toml` (voir [KITS.md](KITS.md) pour tous les champs).
3. Son entrée dans `characters/roster.toml` : nom, kit, sprites, couleur, aura, Stand, rôle, description.
4. `make check`. Le test de la liste des coups vérifie que chaque coup a un nom ; les combats aléatoires vérifient que rien ne plante.

## Les écrans

Chaque écran est une `Scene` (`update` à chaque pas logique, `draw` à chaque image). Elles se trouvent dans `ui/` :

```
TitleScene → MainMenuScene → CharacterSelectScene ─┬→ TrainingScene
                          ↘ OptionsScene           └→ SetupScene (VS) → FightScene
```

Les textes à l'écran sont tous dans `ui/text.py`, en français et en anglais ; la langue courante est dans `engine/i18n.py`, et les fichiers de données donnent leurs traductions avec le suffixe `_en`.
