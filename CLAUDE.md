# JoJo Arena — contexte projet pour Claude Code

## Le projet

Fan game gratuit, open source et non commercial : un **arena fighter 1v1 en temps réel**, en **pixel art vu de dessus**, avec un grand roster des 9 parties de JoJo's Bizarre Adventure.

- Référence visuelle : Pokémon Arena (Big Kid Nation). Arène fermée vue de dessus, sol terne et peu contrasté, persos saturés, ombre portée elliptique sous chaque perso, glow additif sur les effets.
- Référence gameplay : All Star Battle R (Stand on/off, jauges, clash), Eyes of Heaven (décor destructible).
- Le game design complet est dans `docs/GDD.md`. **Lis-le avant toute tâche de gameplay.** Il fait foi en cas de doute.

## Langue

- Le propriétaire du projet parle français : réponds-lui en français.
- Code, noms de variables, commentaires et messages de commit : en anglais.

## Git et attribution — RÈGLE STRICTE

- Les commits sont faits au nom du propriétaire du repo (config git locale). Ne modifie jamais `user.name` ni `user.email`.
- **N'ajoute jamais de ligne `Co-Authored-By`**, ni aucune mention de Claude ou d'un outil d'IA, dans les messages de commit, les descriptions de PR ou les fichiers du repo.
- Messages de commit courts au format conventionnel : `feat: ...`, `fix: ...`, `refactor: ...`, `docs: ...`, `chore: ...`.
- Un commit par étape logique. Ne push que quand on te le demande.

## Stack technique

- Python 3.12, **pygame-ce**. Pas d'autre moteur.
- Distribution : `.exe` Windows via **PyInstaller**, construit par GitHub Actions quand on pousse un tag `v*`, et attaché à une Release.
- Tests : `pytest` pour toute la logique qui ne dépend pas de l'affichage. Lint : `ruff`.
- Pas de dépendance lourde sans demander.

## Rendu (décisions fixées)

- Résolution interne **480 × 270**, dessinée sur une surface puis agrandie **sans lissage** (nearest neighbor) vers la fenêtre, à l'échelle entière la plus grande possible (×4 = 1920 × 1080). Bandes noires si la fenêtre ne tombe pas juste.
- Sprites des persos : **48 px**, **style A** : contour noir (#17121f), ombrage 2-3 tons, petit highlight.
- Sol de l'arène : tuiles ternes, peu contrastées. Persos saturés.
- Ombre portée : ellipse noire semi-transparente sous chaque perso, dessinée avant le sprite.
- Effets lumineux : dégradés radiaux pré-rendus blittés en `BLEND_ADD`.
- Boucle à 60 FPS avec pas de temps fixe pour la logique (déterministe, utile pour un futur mode en ligne).

## Architecture

```
jojo_arena/
  engine/        # moteur générique, ZÉRO référence à JoJo : boucle, rendu, input, physique, collisions, hitboxes
  combat/        # règles génériques : vie, garde, esquive, clash, jauges, rounds, éveils, interactions
  characters/    # un module par perso + un fichier de données (frames, hitboxes, valeurs)
  stages/        # arènes : données + éléments interactifs
  ui/            # menus, HUD, sélection des persos
  assets/        # sprites, sons, polices (voir la règle assets)
tests/
docs/GDD.md
```

- `engine/` et `combat/` doivent rester réutilisables sans aucun asset JoJo : en cas de demande de retrait, on supprime `characters/`, `stages/` et `assets/` et le moteur survit.
- Persos **data-driven** : un nouveau perso s'ajoute sans toucher au moteur.
- Les **styles de combat** (Stand, Stand autonome, mode contrôle, Hamon, Vampire / Pillar Man, Rotation, Cheval, Posture) sont des composants réutilisables.
- Les **interactions spéciales** (time stop contre time stop, Tusk Act 4, King Crimson, Requiem, Love Train, Made in Heaven, Wonder of U…) vivent dans `combat/interactions.py`.
- Les valeurs d'équilibrage (dégâts, durées, vitesses) sont dans des fichiers de données, jamais en dur dans la logique.
- Contrôles : clavier et manette, rebindables (mapping par défaut dans le GDD).

## Assets — RÈGLE STRICTE

- **Ne dessine et ne génère jamais de sprite, d'image ou de son représentant un personnage, un Stand ou un logo de JoJo**, même à partir d'une référence. Les sprites JoJo sont faits à la main par le propriétaire ou des contributeurs.
- Ton travail côté visuel : des **placeholders génériques** (formes simples, bonne taille, couleur propre à chaque perso) et des **mannequins de base** génériques en 48 px, style A (corps neutre avec idle, marche, coups, dash, dégâts, KO), qui servent de base à habiller.
- Le moteur charge les sprite sheets depuis `assets/` ; si un sprite manque, il affiche le placeholder. Remplacer un placeholder ne doit demander aucun changement de code.

## Licence et mentions

- Code sous licence **MIT**.
- Le README précise que c'est un fan game non officiel, gratuit, sans but lucratif, non affilié à Hirohiko Araki, Shueisha, David Production ou CyberConnect2, et que les marques appartiennent à leurs propriétaires.

## Façon de travailler

- Avant une tâche qui touche plus d'un fichier : propose un plan court, puis code.
- Après chaque étape : lance les tests et vérifie que le jeu démarre avant de dire que c'est fini.
- Si une règle du GDD est ambiguë, pose la question au lieu d'inventer.
