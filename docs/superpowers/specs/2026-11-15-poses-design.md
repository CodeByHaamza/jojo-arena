# Poses : les vraies, au choix

Design validé par le propriétaire le 15/11/2026 (« oue vasy gooooo ») : les poses
iconiques de chaque perso, tirées du manga, de l'anime, des illustrations d'Araki,
d'ASBR et d'EoH, plusieurs par perso, avec et sans Stand, choisies à l'écran de sélection.

## Pourquoi

Aujourd'hui 7 poses génériques sont partagées par 20 persos, et le Stand ne pose jamais.
Le propriétaire veut voir *chaque* perso dans *sa* pose, comme dans ASBR (5 poses de
provocation par perso, choisies dans la personnalisation).

## Objectifs

- Chaque perso jouable a **3 poses seules** ; chaque manieur de Stand a en plus **3 poses
  en duo**, où son Stand prend sa propre pose à côté de lui.
- Chaque pose est **sourcée** (chapitre, épisode, illustration, ASBR/EoH), et la source
  est citée dans la fiche `looks/` du perso.
- À l'écran de sélection, après avoir validé un perso, le joueur choisit sa pose seule et
  sa pose avec Stand, avec un aperçu animé. Le dernier choix est retenu par perso.
- En combat, la touche Pose joue la pose seule si le Stand est rangé, la pose en duo s'il
  est sorti.

## Non-objectifs

- Pas de changement de règle : la pose reste l'état « Pose » de la simulation (Heart
  Heat, soin de Speedwagon, contre de Joseph). Le choix est purement visuel : ni
  l'équilibrage ni les replays ne bougent.
- L'écran VS et l'écran de victoire qui reprennent les poses : plus tard.
- Les costumes et les couleurs : étape 3 (la ligne s'ajoutera au même panneau).

## Anti-objectifs

- Des poses inventées ou « à la JoJo » sans source.
- Une seule planche existante qui change d'un pixel sans qu'une pose ait été ajoutée.

## Approches envisagées

| Approche | Pour | Contre |
| --- | --- | --- |
| Squelette actuel (membres droits) | rien à changer | une pose JoJo sans coude ni genou ressemble aux 7 actuelles |
| **Coudes, genoux et déhanché ajoutés au squelette** (choisie) | poses lisibles à 48 px ; optionnel, les animations existantes ne bougent pas | ~15 pièces de costume à faire suivre le membre plié |
| Chaque pose dessinée à la main | le plus fidèle | très long ; reste possible pose par pose (une planche dessinée remplace la générée) |

## Le design

### Squelette

- `Pose` gagne `elbow_l`, `elbow_r`, `knee_l`, `knee_r` (décalage du coude ou du genou par
  rapport au milieu du membre, à la même échelle que les mains) et `sway` (les hanches
  glissent sur le côté, le déhanché). À zéro, le membre est droit.
- Chaque bras et chaque jambe devient un `Limb` (racine, articulation, bout) :
  `point(t)` (un point à une fraction du membre) et `pixels(r, t0, t1)` (la forme d'une
  portion). **Droit, il rend exactement les mêmes pixels qu'avant** : le test « planches
  à jour » le prouve sur toutes les planches.
- Les pièces de costume qui suivent un membre (manches, gants, bottes, bracelets,
  plumes, veines, coutures, lames, épée) passent par `Limb`.

### Les fiches et les planches

- `looks/<id>.toml` : `[poses.<id_pose>]` avec `label`, `label_en`, `source`, `stand`
  (pose en duo ou non), `stand_offset = [devant, côté]` (où se tient le Stand pendant
  la pose, en pixels), `fps`, et les images-clés par vue comme `[anims.*]`.
- La fiche du Stand a la pose de même identifiant pour ses propres images.
- La planche reçoit une animation `pose_<id_pose>` par pose, et son TOML une table
  `[poses.<id_pose>]` (nom, nom anglais, source, stand, emplacement du Stand).
- Le jeu retombe sur la pose générique si une pose manque.

### En jeu

- `Loadout` par joueur (pose seule, pose Stand), dans le contexte du jeu ; l'IA tire au
  hasard, le mannequin prend la première.
- `FighterView` joue `pose_<id>` dans l'état Pose ; le Stand joue la même pose sur sa
  planche, décalé de `stand_offset` (vue seulement, la simulation ne bouge pas).
- `settings.json` retient le dernier choix par perso.

### Écran de sélection

Après avoir validé un perso qui a des poses, son panneau passe en réglage : une ligne
« POSE », une ligne « POSE STAND » (si le perso a un Stand), Gauche/Droite pour changer,
Haut/Bas pour passer d'une ligne à l'autre, Entrée pour confirmer, Échap pour revenir à la
grille. L'aperçu à gauche joue la pose (avec le Stand sur la ligne Stand).

### Le contenu

Toutes les parties à la suite, Partie 3 d'abord (elle a les Stands), puis 1 et 2. Pour
chaque perso : recherche (JoJo Wiki « JoJo Poses » et galeries, scans, poses de
provocation et de victoire d'ASBR, EoH), puis la pose écrite, puis une planche d'aperçu
regardée avant de passer au suivant. Le propriétaire relit tout à la fin.

## Laissé au constructeur

- Les décalages exacts du Stand pour chaque pose.
- Le choix entre poses ASBR et poses du manga quand il y en a plus de trois.
