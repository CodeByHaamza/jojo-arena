# Costumes et couleurs

Design proposé le 15/11/2026, **à valider par le propriétaire**. Étape 3 du plan en tête
du [ROADMAP](../../ROADMAP.md).

## Pourquoi

Dans ASBR et EoH, on choisit la tenue de son perso et sa couleur. Chez nous, un perso a
une seule planche : deux joueurs qui prennent le même perso voient deux sprites
identiques et ne savent plus qui est qui. Le propriétaire veut les tenues des jeux et du
manga (Jonathan torse nu, les tenues blanches de *JOESTAR The Inherited Soul*, « le père
d'Avdol ? »), plusieurs couleurs par tenue, et un match miroir lisible.

## Objectifs

- Un perso peut avoir **plusieurs costumes**, chacun sourcé (jeu, chapitre, épisode,
  couverture).
- Chaque costume a **plusieurs couleurs**. Règle fixée par le propriétaire : une couleur
  **sourcée d'abord** (les couleurs d'ASBR et d'EoH, dont le wiki donne l'origine) ; une
  couleur **inventée seulement s'il n'y en a pas**, et son `source` le dit, comme pour
  les poses.
- La couleur du **Stand suit** celle du manieur.
- À l'écran de sélection, le costume et la couleur se choisissent dans le même panneau
  que les poses, avec l'aperçu en direct. Le dernier choix est retenu par perso.
- En **match miroir**, les deux persos ne sont jamais identiques.
- Le choix est **purement visuel** : ni la simulation, ni l'équilibrage, ni les replays ne
  bougent.
- Ajouter une couleur, c'est quelques lignes de données. Ajouter un costume, c'est une
  fiche et une ligne dans le roster. Jamais de code.
- **Premier lot** : Jonathan, Jotaro, DIO et Avdol, pour valider le système avant de
  l'étendre aux seize autres.

## Non-objectifs

- Pas de déblocage : tout est disponible dès le départ.
- Les costumes des seize autres persos, et les tenues du manga qui ne sont dans aucun
  jeu : après la validation du premier lot.
- Un costume ne change ni les coups, ni les zones de frappe, ni les cris.
- Les formes qui changent le corps en combat (Kars ultime, les futurs éveils de Jotaro et
  DIO de l'étape 4) restent des formes, pas des costumes. C'est pour ça que « DIO après
  le sang de Joseph » (costume spécial A d'ASBR) n'est pas dans le lot.
- La grille de sélection, l'écran titre, le menu principal et le glossaire montrent
  toujours la tenue normale.
- La couleur d'aura et la couleur du perso dans le HUD ne changent pas.
- Un Stand n'a pas de costume, seulement des couleurs.

## Anti-objectifs

- Une couleur inventée alors qu'une couleur sourcée existe.
- Une image de référence (couverture, carte, capture d'un jeu) dans le dépôt : on ne garde
  que les teintes relevées et le nom de la source.
- Une planche actuelle dont les pixels changent sans raison. Si deux teintes d'une fiche
  se confondent et qu'il faut en décaler une d'une unité, on le dit dans le commit.
- Un deuxième système de couleurs à côté de celui des mannequins : c'est le même.

## Approches envisagées

| Approche | Pour | Contre |
| --- | --- | --- |
| **A. Une planche par costume, les couleurs appliquées au chargement** (choisie par le propriétaire) | ~145 Ko par costume, rien par couleur ; une couleur est une ligne de données ; le chargeur sait déjà repeindre (les mannequins rouge et bleu) | les teintes d'une fiche doivent toutes être distinctes ; 32 ms pour repeindre une planche (mesuré sur celle de Jotaro) |
| B. Une planche par costume et par couleur | rien à repeindre, aucun risque de teintes confondues | 4 persos × 3 costumes × 4 couleurs = 48 planches, ~7 Mo, et le roster complet rendrait le dépôt et le `.exe` très lourds |
| C. Les planches générées au lancement depuis les fiches | aucune image de plus | le générateur embarqué dans le jeu, un démarrage lent, plus de planche dessinée à la main |

## Le design

### Les fiches

**Un costume est une fiche** `characters/looks/<perso>_<costume>.toml` qui commence par
`base = "<perso>"`. Elle hérite de tout (morphologie, visage, palette, pièces, animations,
poses) et ne redit que ce qui change :

- `[palette]`, `[body]`, `[build]`, `[face]` : les entrées données remplacent celles de la
  base, les autres restent ;
- `[[parts]]` : si la fiche en donne, sa liste **remplace** celle de la base (l'ordre des
  pièces compte, on ne les fusionne pas) ;
- les animations et les poses viennent de la base, telles quelles : un costume ne change
  pas la façon de bouger ;
- `[costume]` : `label`, `label_en`, `source`.

Le commentaire en tête cite la recherche (section « Apparence » de la fiche JoJo Wiki, le
chapitre ou la couverture), comme toute fiche.

**Une couleur est une table** `[colors.<id>]` dans une fiche (de base, de costume ou de
Stand). Les teintes ci-dessous sont des exemples de format, pas des relevés :

```toml
[colors.anime]              # la première : la palette de la fiche, telle quelle
label = "Anime"
label_en = "Anime"
source = "ASBR, couleur A : les couleurs de l'anime"

[colors.tome16]
label = "Tome 16"
label_en = "Volume 16"
source = "ASBR, couleur B : couverture du tome 16"
stand = "tome17"            # la couleur de Star Platinum qui va avec (facultatif)

[colors.tome16.palette]     # seulement les matières qui changent
uniform = "#2b3f8f"
gold = "#e8d27a"
```

- La première couleur n'a pas de `palette` : c'est celle de la fiche. Elle a quand même
  son nom et sa source.
- Une couleur a toujours `label`, `label_en` et `source`. Une couleur inventée l'écrit dans
  son `source`.
- Les couleurs ne s'héritent pas d'une base à son costume : les matières ne sont pas les
  mêmes, chaque costume liste les siennes.
- Les teintes se relèvent sur l'image citée par la source (couverture, carte, capture du
  jeu), téléchargée hors du dépôt le temps du relevé.

### Les planches

- `make sprites` produit une planche par fiche, costume compris, dans
  `assets/sprites/<id>/`.
- Le TOML de la planche reçoit `[costume]`, `[recolor]` (les teintes d'origine de chaque
  matière qu'au moins une couleur change, calculées par le générateur) et
  `[colors.<id>]` (nom, source, couleur du Stand, teintes finales par matière). Le jeu ne
  lit que la planche, jamais la fiche : une planche dessinée à la main peut toujours
  remplacer une planche générée.
- Le générateur **refuse** une fiche à couleurs où une teinte à repeindre est égale à une
  autre teinte de la planche (une autre matière, le contour, une couleur fixe), et nomme
  les deux matières : sinon elles seraient repeintes ensemble.

### Le roster

`roster.toml`, comme `stand_sprites` et `body_sprites` :

```toml
sprite = "jonathan/jonathan"          # la tenue normale, inchangée
costumes = { shirtless = "jonathan_shirtless/jonathan_shirtless", inherited_soul = "jonathan_inherited_soul/jonathan_inherited_soul" }
```

L'ordre de la table est l'ordre affiché, après la tenue normale.

### En jeu

- `Loadout` gagne `costume` (`""` : la tenue normale) et `color` (`""` : la première).
  `resolve_loadout` ramène à la tenue normale ou à la première couleur ce que la planche
  ne connaît pas (vieux fichier de réglages, costume retiré).
- `FighterView` et `FighterLook` chargent la planche du costume, repeinte dans la couleur
  choisie, et la planche du Stand dans la couleur que la couleur du manieur désigne (la
  première du Stand par défaut).
- Le chargeur repeint **à partir des teintes d'origine**, pas en chaîne : une teinte déjà
  repeinte ne doit pas être reprise par la matière suivante.
- Tout ce qui montre les deux combattants d'un match suit le choix : aperçu de sélection,
  écran VS, combat, duel de rafales, cinématiques d'ultime, écran de fin.
- `settings.json` retient `outfits` : perso → `[costume, couleur]`. `poses` ne change pas.
- Les planches repeintes pèsent 6 à 12 Mo chacune en mémoire. Celles qu'on ne fait que
  survoler à l'écran de sélection ne restent pas dans le cache (le runner de la CI a
  3 Go).

### Le match miroir

Une fonction pure dans `ui/loadout.py` : même perso, même costume, même couleur → le
second côté passe à la couleur suivante de ce costume.

- **Joueur 2** : la couleur prise par le joueur 1 est sautée quand il fait défiler, et à
  l'ouverture du panneau.
- **Ordinateur** : tire un costume et une couleur au hasard parmi les autres.
  **Mannequin d'entraînement** et **adversaires de l'arcade** : tenue normale, première
  couleur libre.
- La même fonction repasse quand le combat se construit, pour qu'aucun chemin n'y échappe.
- Les seize persos qui n'ont pas encore de couleurs restent identiques en miroir, comme
  aujourd'hui, jusqu'à ce qu'on les fasse.
- Un costume inscrit au roster a **au moins deux couleurs** (un test le vérifie).

### L'écran de sélection

Le panneau de réglage passe de deux lignes côte à côte à une liste, une ligne par choix :

```
 J1
┌──────────────────────────────┐
│ JOTARO KUJO                  │
│ Star Platinum                │
│ COSTUME   < Sans manteau >   │   ← ligne active : en or, avec les flèches
│ COULEUR     Anime            │
│ POSE        Main au visage   │
│ STAND       Dos à dos        │
│ EoH, costume spécial E :     │   ← la source de la ligne active
│ chapitre 153, épisode 13     │
└──────────────────────────────┘
```

- Haut/Bas change de ligne, Gauche/Droite change la valeur, Entrée confirme, Échap
  revient à la grille : comme aujourd'hui.
- Une ligne n'apparaît que s'il y a un choix à faire : un perso sans costume ni couleur
  garde ses deux lignes de pose.
- Pendant le réglage, le rôle, la vie et la présentation laissent la place aux lignes.
- L'aperçu montre le costume et la couleur en direct : au repos, Stand sorti, sur les
  lignes Costume et Couleur ; dans la pose sur les lignes de pose.
- Changer de costume garde les poses et prend la première couleur de ce costume.
- Un nom de costume, de couleur ou de pose tient sur sa ligne (un test mesure la largeur).
- Les nouveaux textes existent en français et en anglais (`ui/text.py`).

### Le contenu du premier lot

Sources : pages « Costumes & Tints » d'ASBR et d'EoH sur JoJo Wiki, et « Video Game
Callbacks ★ Costumes ».

| Perso | Costume | Source du costume | Couleurs (source) |
| --- | --- | --- | --- |
| Jonathan | Normal | tenue de *Phantom Blood* | anime ; couverture du tome 4 ; couverture du tome 3 ; carte Adventure Battle J-534 |
| Jonathan | Torse nu | EoH, spécial F : chapitre 35, épisode 7 | anime, épisode 7 ; la version inversée d'EoH |
| Jonathan | Inherited Soul | ASBR, extra A : produits *JOESTAR The Inherited Soul* | les deux couleurs des produits |
| Jotaro | Normal | tenue de *Stardust Crusaders* | anime ; couverture du tome 16 ; du tome 26 ; du tome 24 |
| Jotaro | Sans manteau | EoH, spécial E : chapitre 153 (40ᵉ de la partie 3), épisode 13 | anime, épisode 13 ; manga (Jump 1991 n° 24) |
| Jotaro | Inherited Soul | ASBR, extra A | les produits ; une couleur propre à ASBR |
| DIO | Normal | tenue de *Stardust Crusaders* | anime ; Jump n° 7 et Super Action Statue ; une couleur propre à ASB ; carte J-367 |
| DIO | Dans l'ombre | ASBR, spécial D : sa première apparition, dans l'ombre | celle du costume ; Statue Legend |
| Avdol | Normal | tenue de *Stardust Crusaders* | anime ; couverture A du chapitre 136 ; une couleur d'ASBR dont le wiki ne note pas l'origine ; carte J-039 |
| Avdol | « Le père d'Avdol ? » | ASBR, extra A : le déguisement de l'arc Judgement | anime ; manga colorisé (JOJO-D) |

Stands : Star Platinum (anime ; couverture du tome 17), The World (anime ; Super Action
Statue), Magician's Red (anime ; carte J-083).

Six costumes nouveaux, soit environ 0,9 Mo de planches.

**Ordre de travail** : d'abord le système de bout en bout sur Jonathan (la tenue normale
et ses couleurs, puis Torse nu), le propriétaire regarde les captures, puis les trois
autres persos un par un, chacun avec sa planche d'aperçu.

## Tests

- Repeindre : une teinte déjà repeinte n'est pas reprise ; une couleur inconnue ne change
  rien.
- Le générateur refuse deux teintes confondues, avec un message qui nomme les matières.
- Toute couleur a ses deux noms et sa source ; tout costume du roster a sa planche, à
  jour, et au moins deux couleurs.
- `resolve_loadout` avec un costume ou une couleur inconnus ; le tirage de l'ordinateur.
- Le match miroir : joueur 2, ordinateur, mannequin, arcade.
- L'écran de sélection : les lignes, le défilement, la couleur prise sautée, les
  réglages retenus, la largeur des noms.
- Un replay rejoue le même combat quel que soit le costume.

## Laissé au constructeur

- Les teintes exactes de chaque couleur, relevées sur l'image citée ; le nom affiché de
  chaque couleur.
- Si une image citée est introuvable : le dire au propriétaire, pas inventer.
- La technique pour repeindre en une passe et pour borner le cache.
- Les positions au pixel près dans le panneau.
- À la fin : la section du GDD, la case du ROADMAP, ARCHITECTURE, et l'étape « costumes et
  couleurs » dans le skill `new-fighter` et dans la liste « Imaginer un perso » de
  `CLAUDE.md` (le propriétaire a demandé qu'elle soit écrite après l'implémentation).
