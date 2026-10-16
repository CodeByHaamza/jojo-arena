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
- Sprites des persos : **environ 48 px de haut** (cases de 64 × 64), **style A** : contour noir (#17121f), ombrage 2-3 tons, petit highlight. Chaque perso a sa morphologie (fiche `characters/looks/<id>.toml`).
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

## Assets

- Ton travail côté visuel : des **placeholders génériques** (formes simples, bonne taille, couleur propre à chaque perso), des **mannequins de base** génériques en 48 px, style A (corps neutre avec idle, marche, coups, dash, dégâts, KO), qui servent de base à habiller, et la **conversion des images fournies par le propriétaire** (dessins ou images générées) au format du jeu.
- Le moteur charge les sprite sheets depuis `assets/` ; si un sprite manque, il affiche le placeholder. Remplacer un placeholder ne doit demander aucun changement de code.

## Fidélité à l'œuvre — recherche en ligne OBLIGATOIRE

Rien de ce qui touche à un personnage ne s'invente. Avant d'écrire ou de retoucher un
perso, un coup, un ultime, une réplique, un design ou une icône : **cherche la source en
ligne**, et cite-la dans le commentaire du fichier concerné.

- Sources, dans cet ordre : **JoJo Wiki** (fr puis en) pour l'apparence, la personnalité,
  les techniques et les répliques ; les **listes de coups d'All Star Battle R** et d'Eyes
  of Heaven pour le gameplay (nom officiel du coup, HHA, GHA, mode) ; le manga et l'anime
  pour ce qu'on voit à l'écran.
- Un **design** se fait depuis la section « Apparence » de la fiche : coiffure, tenue,
  motifs, couleurs, silhouette. Pas de perso dessiné de mémoire.
- Un **coup** porte le nom de la vraie technique. Si le perso n'a pas de technique à cet
  emplacement, prends-en une de ses combats plutôt que d'inventer un « coup de poing ».
- Un **ultime** doit être reconnaissable **à sa forme**, pas seulement à son nom :
  - un rayon ou un souffle → `shape = "line"` et une grande `reach` (Space Ripper, le
    Rift Atmosphérique sort de la corne de Wamuu et traverse l'arène) ;
  - une zone, une explosion, une nappe → un gros `radius` (l'autodestruction de
    Stroheim) ;
  - un piège, un fil, un câble → `shape = "line"`, `radius` large, devant lui (les trucs
    du métier de Joseph) ;
  - des projectiles qui se referment → un `projectile` avec `count` et `ring`
    (les lentilles de Burn Black) ;
  - une saisie → `unblockable` (l'absorption de DIO, Santana) ;
  - **une hitbox de poing (`circle`, `reach` 15-25) seulement si la technique est
    vraiment un coup de poing** (Ora Ora Final, Sunlight Yellow Overdrive).
- Même règle pour les **ennemis et les persos secondaires** : la portée et la forme des
  coups suivent l'arme du perso (les cheveux de Bruford frappent de loin, les veines
  d'Esidisi aussi), jamais un gabarit par défaut.
- Si une source manque ou se contredit, dis-le au propriétaire au lieu de combler le
  trou.

## Licence et mentions

- Code sous licence **MIT**.
- Le README précise que c'est un fan game non officiel, gratuit, sans but lucratif, non affilié à Hirohiko Araki, Shueisha, David Production ou CyberConnect2, et que les marques appartiennent à leurs propriétaires.

## Façon de travailler

- Avant une tâche qui touche plus d'un fichier : propose un plan court, puis code.
- Après chaque étape : lance les tests et vérifie que le jeu démarre avant de dire que c'est fini.
- Si une règle du GDD est ambiguë, pose la question au lieu d'inventer.
