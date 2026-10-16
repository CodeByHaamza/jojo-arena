# JoJo Arena

Fan game **gratuit, open source et non commercial** : un arena fighter 1v1 en temps réel, en pixel art vu de dessus, avec un grand roster des 9 parties de JoJo's Bizarre Adventure.

> **Fan game non officiel.** Ce projet est gratuit, sans but lucratif, et n'est affilié ni à Hirohiko Araki, ni à Shueisha, ni à David Production, ni à CyberConnect2. JoJo's Bizarre Adventure et toutes les marques citées appartiennent à leurs propriétaires respectifs.

## État du projet

Prototype jouable : le moteur (**Vague 0**) et quatre persos de la Partie 3 (**Vague 1**) : Jotaro, Kakyoin, DIO et Polnareff, chacun avec son Stand et ses coups. Deux modes sont jouables, **Entraînement** et **Combat local** ; Histoire, Arcade, Contre l'IA et En ligne sont annoncés dans le menu et arriveront plus tard. Le game design complet est dans [docs/GDD.md](docs/GDD.md).

Ce qui marche déjà :

- attaques légère, lourde et spéciale, enchaînements de trois coups sur la même touche, baisse des dégâts sur les longs combos ;
- coups variés : contres, bonds, coups blindés, casse-garde, tentacule qui attire, grappin visé à la souris ou au stick droit ;
- garde (−80 % de dégâts), jauge de garde et Guard Break ;
- dash avec invincibilité, Stylish Evade (esquive au dernier moment : ralenti) ;
- jauge Heart Heat à 3 barres, HHA (1 barre), Flash Cancel (½ barre), Pose, Résolution ;
- clash : deux attaques simultanées, on martèle pour gagner le duel ; rafale contre rafale, l'écran passe en face-à-face (5 s) ;
- onomatopées façon JoJo (ゴゴゴ, ドン, ORA, MUDA…), poses iconiques, effets d'impact ;
- ultimes en cinématique avec caméra (Road Roller, Ora Ora final, clones de Chariot, toile de Hierophant), seulement si le premier coup touche ;
- mode contrôle de Hierophant Green (maintenir Stand) avec possession ;
- caisses et jarres : le Stand les prend (Pose) et les lance (Pose), plus ou moins fort selon sa puissance ; elles reviennent à leur place ;
- recul, rebond sur les murs, étals et caisses cassables ;
- touche Stand : le Stand apparaît à côté de son manieur et change les coups ; un coup sur le Stand blesse son manieur ;
- coups propres à chaque perso : arrêt du temps (Jotaro, DIO), couteaux, saisie qui draine la vie, fils piégés, Emerald Splash, Armor Off, GHA (2 barres) ;
- rounds (1, 3 ou 5 gagnants), timer de 99 s, mort subite en cas d'égalité ;
- clavier et manette (Xbox, DualShock 4, DualSense), touches modifiables ;
- menus : écran titre partie par partie, menu principal, sélection des persos en onglets par partie (fiche, Stand, rôle), écran VS, pause, options (dont la langue : français ou anglais) ;
- glossaire : termes du lore, personnages et Stands, partie par partie ;
- modes : combat local, contre l'IA (quatre niveaux), Arcade (six combats jusqu'à DIO), entraînement ;
- liste des coups de chaque perso, avec les vraies touches du joueur (sélection des persos et pause) ;
- entraînement poussé : mannequin immobile, en garde, joué par J2, qui **répète une action de son kit** (ORA ORA ORA, Star Finger, ultime...) avec le **délai de ton choix** entre chaque, ou qui **rejoue une suite enregistrée** ; vie et jauge infinies, compteur de combo et de dégâts, données de frames des deux côtés et **frise des frames** avec l'avantage mesuré.

## Jouer

Télécharge `JoJoArena.exe` dans la dernière [Release](../../releases) et lance-le. Rien à installer.

- **F11** ou **Alt+Entrée** : plein écran.
- **Échap** (ou Start) : pause. En entraînement, la pause contient les réglages (mannequin, vie, jauge, replacer).
- **Tab** (ou Y) sur la sélection des persos : liste des coups du perso survolé. Elle est aussi dans la pause.
- **F3** en combat : affiche les zones de frappe. En entraînement, les touches reconnues s'affichent en bas à gauche.

### Mode entraînement

La pause (**Échap**) contient les réglages, et l'entrée **Réglages du mannequin** ouvre tout ce qu'il faut pour travailler un coup :

| Réglage | Effet |
| --- | --- |
| **Action** | ce que le mannequin répète, choisi parmi les coups de **son** kit (avec la posture qu'il faut : il sort son Stand tout seul), plus dash et pose |
| **Délai** | images d'attente entre deux répétitions, comptées dès qu'il est libre d'agir. **0 = riposte à la frame près** (reversal) : de quoi vérifier si ton coup est vraiment sûr |
| **Enchaîne** | il continue l'enchaînement du coup (ORA, ORA ORA, ORAAA) au lieu de s'arrêter au premier |
| **Se rapproche** | il marche vers toi tant que son coup ne peut pas porter |
| **Entre deux** | il ne fait rien, ou il tient la garde : pour travailler les combos sur un adversaire qui bloque |
| **Enregistrer une action** | J2 joue le mannequin, puis **Échap** arrête : la suite enregistrée est rejouée en boucle (avec le même délai) |
| **Frise des frames** | deux bandes, une par perso, une colonne par image |

La frise se lit comme dans les jeux de combat : **jaune** = démarrage, **rouge** = actif (le coup peut toucher), **bleu** = récupération, **violet** = dégâts subis, **gris** = blocage, **vert** = garde, **blanc** = tout est figé (impact, temps arrêté, cinématique). À droite s'affiche l'avantage **mesuré** du dernier échange (`J1 TOUCHÉ +6`) : si ton coup est à −3 en garde et que le mannequin riposte avec un coup qui démarre en 4, tu le vois arriver.

En bas à gauche, la ligne de données de frames donne le dernier coup de chaque côté au format habituel : `DIRECT 4/3/10 +6/-2` (démarrage / actif / récupération, puis avantage touché / en garde).

### Contrôles par défaut

Les touches sont liées à leur **position** sur le clavier : ZQSD en AZERTY correspond à WASD en QWERTY.

| Action | J1 clavier | Manette | Clavier partagé J1 | Clavier partagé J2 |
| --- | --- | --- | --- | --- |
| Déplacement | ZQSD | Stick gauche / croix | ZQSD | Flèches |
| Attaque légère | J | X / Carré | F | 4 (pavé num.) |
| Attaque lourde | K | Y / Triangle | G | 5 |
| Spéciale | L | B / Rond | H | 6 |
| Stand on/off | I | RB / R1 | R | 8 |
| Dash / esquive | Espace | A / Croix | V | 0 |
| Garde (Flash Cancel pendant une attaque) | Maj gauche | LB / L1 | C | 1 |
| Heart Heat : HHA ; direction + Heart Heat : GHA (2 barres) | O | RT / R2 | T | 9 |
| Pose (près d'un objet : le Stand le prend, puis le lance) | P | Select / Touchpad | Y | 7 |
| Power Up (pas encore utilisé) | U | LT / L2 | B | 3 |

Choisis la configuration (J1 clavier + J2 manette, clavier partagé, deux manettes) dans **Options** ou sur l'écran VS du **Combat local**, qui permet aussi de choisir l'arène (le Caire de nuit, le manoir Joestar en flammes, ou au hasard). Options affiche aussi le tableau des touches des deux joueurs (modifiables avec « Changer les touches »), et règle la langue du jeu (français ou anglais), gardée dans `settings.json` à côté de `controls.json`.

### Les bonnes touches, quel que soit ton matériel

Les touches sont liées à une **position physique**, pas à une lettre : le jeu se joue pareil en AZERTY et en QWERTY, et il **affiche partout le nom imprimé sur ta touche** (`W` devient `Z` en AZERTY). Pareil pour les manettes : le jeu lit le constructeur dans l'identifiant SDL de la manette, donc une **DualShock 4 / DualSense affiche CROIX, CARRÉ, OPTIONS** là où une **manette Xbox affiche A, X, MENU, VIEW**.

Deux réglages dans Options si la détection se trompe (manette générique, disposition système différente du clavier physique) :

| Réglage | Valeurs |
| --- | --- |
| **Clavier** | `AUTO (QWERTY)` — ce que le système annonce — ou `AZERTY` / `QWERTY` forcé |
| **Manette** | `AUTO (XBOX)` — ce que la manette annonce — ou `XBOX` / `PLAYSTATION` forcé |

Ça ne change **que les noms affichés** : les touches réelles ne bougent pas. Sous le tableau, le jeu affiche le nom exact des manettes qu'il voit, pour vérifier d'un coup d'œil qu'elles sont bien détectées.

Pour changer les touches, modifie `controls.json` dans `%APPDATA%\JoJoArena\` puis relance le jeu. Le fichier explique les noms de touches. Supprime-le pour revenir aux réglages par défaut.

## Développement

Pour contribuer, commence par [CONTRIBUTING.md](CONTRIBUTING.md). La doc du projet :

- [docs/GDD.md](docs/GDD.md) : le game design, qui fait foi ;
- [docs/ROADMAP.md](docs/ROADMAP.md) : ce qui est fait, en cours et à venir ;
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) : l'organisation du code ;
- [docs/KITS.md](docs/KITS.md) : tous les champs d'un kit de perso ;
- [docs/INFRA.md](docs/INFRA.md) : tests, CI, Docker, crochets git, Releases ;
- [docs/AGENTS.md](docs/AGENTS.md) : comment le travail se découpe entre agents.

Il faut Python 3.12 ou plus récent.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Raccourcis avec make

Le `Makefile` regroupe les commandes courantes ; `make` tout seul affiche la liste. Il crée `.venv` et installe tout au premier usage.

| Commande | Effet |
| --- | --- |
| `make run` | lance le jeu (écran titre) |
| `make training P1=dio_p3 P2=kakyoin` | va droit à l'entraînement |
| `make fight`, `make versus`, `make demo` | combat direct, écran VS, ou ordinateur contre ordinateur |
| `make check` | lint puis tests, comme la CI : à lancer avant un commit |
| `make hooks` | une fois : lint et tests rapides automatiques avant chaque commit |
| `make test-fast` | les tests sans ceux qui lancent le jeu entier |
| `make screens` | capture tous les écrans dans `screenshots/tour/` |
| `make sprites`, `make exe`, `make clean` | planches de sprites, `.exe`, nettoyage |

Sous Windows il faut un GNU make : `winget install ezwinports.make` ou `choco install make` (ou `mingw32-make`). Les commandes marchent pareil dans PowerShell, cmd ou Git Bash.

### Lancer le jeu

```powershell
.\.venv\Scripts\python.exe -m jojo_arena
```

Options utiles :

| Commande | Effet |
| --- | --- |
| `--demo` | combat joué par l'ordinateur des deux côtés |
| `--scene fight --rounds 1` | va droit au combat, en 1 round gagnant |
| `--scene training --p1 dio_p3 --p2 kakyoin` | va droit à l'entraînement avec ces persos |
| `--scene menu`, `select`, `setup`, `options`, `glossary` | ouvre directement un écran (`--mode training` pour la sélection de l'entraînement) |
| `--p1 jotaro_p3 --p2 mannequin_red` | choisit les persos (avec `--scene fight`, `training`, `setup` ou `--demo`) |
| `--fullscreen` | démarre en plein écran |
| `--lang en` | textes en anglais (`fr` ou `en` ; sinon la langue choisie dans Options) |
| `--frames 300 --screenshot capture.png` | joue 300 images puis enregistre l'image 480 × 270 (tests rapides) |

> Si Python vient du Microsoft Store, Windows range `controls.json` dans `%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.xx_...\LocalCache\Roaming\JoJoArena\` quand le jeu tourne depuis les sources. Le `.exe`, lui, utilise bien `%APPDATA%\JoJoArena\`.

### Tests et lint

```powershell
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

GitHub Actions les lance aussi à chaque push (`.github/workflows/ci.yml`).

Les tests couvrent la logique de combat, les menus (parcours au clavier simulé), et lancent chaque écran du jeu dans une fenêtre cachée. Pour voir tous les écrans d'un coup après une modification :

```powershell
.\.venv\Scripts\python.exe tools\screenshot_tour.py
```

Les captures arrivent dans `screenshots/tour/` (ignoré par git).

### Construire le .exe en local

```powershell
.\.venv\Scripts\python.exe tools\build_exe.py
```

Résultat : `dist\JoJoArena.exe`, un seul fichier qui embarque toutes les données.

### Publier une Release

Change la version dans `pyproject.toml` et `jojo_arena/__init__.py`, commit, puis crée et pousse un tag qui commence par `v` :

```powershell
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions (`.github/workflows/release.yml`) lance les tests, construit le `.exe`, vérifie qu'il démarre, puis publie la Release avec le `.exe` en pièce jointe.

## Organisation du code

```text
jojo_arena/
  engine/       moteur générique (boucle, rendu, entrées, géométrie, sprites, police) : zéro référence à JoJo
  combat/       règles génériques (combattant, garde, dash, clash, jauges, rounds) + rules.toml
  characters/   roster.toml, une fiche de jeu par perso, et looks/ (apparence des persos)
  stages/       arènes : données (.toml) et rendu
  ui/           écrans, HUD, menus
  assets/       sprites (et plus tard sons, portraits)
tools/          générateur de sprites (spritegen, make_sprites.py), build du .exe
tests/          pytest
```

Toutes les valeurs d'équilibrage sont dans des fichiers TOML commentés : `combat/rules.toml` (règles globales) et `characters/*.toml` (attaques de chaque perso).

## Créer ou modifier l'apparence d'un perso

Les sprites des persos sont **générés à partir d'une fiche de données**, sans dessin à la main. La fiche se trouve dans `jojo_arena/characters/looks/<id>.toml` (voir `jotaro_p3.toml` et `kakyoin.toml`). Elle contient :

- `[build]` : la morphologie, en pixels : taille de la tête (`head_r`), longueur du torse, des jambes et des bras, largeur des épaules, épaisseur des membres… C'est ce qui donne à chaque perso sa silhouette (Jotaro grand et carré, Kakyoin élancé).
- `[palette]` : les couleurs du perso. Une seule couleur suffit, les ombres et les reflets sont calculés.
- `[body]` : la couleur de chaque partie du corps (tête, torse, bras = manches, jambes = pantalon…).
- `[face]` : couleur des yeux, style (`dot`, `tall`, `wide` avec paupière), sourcils, bouche, nez de profil.
- `[[parts]]` : les pièces de costume :
  - `hair` : styles `short`, `long`, `tower`, `spiky`, `swept`, `crest` (crête de casque) ; mèches sur la nuque ; mèche `curl` ondulée ou frange `fringe` ;
  - `cap` : hauteur, bandeau, un ou deux insignes, mèches effilochées sous la casquette ;
  - `headband` : avec une pierre au milieu en option ;
  - `mask` : un visage d'une autre couleur que la tête (casque, visière) ;
  - `coat` : longueur, ouvert ou fermé, évasement, col, épingles de col, boutons, doublure, boutons de manche ;
  - `belt` : une ou deux, rivets, boucle ;
  - `chain` : longueur ;
  - `emblem` : cœur, rond ou losange, sur la poitrine ou les genoux ;
  - `earring` : simple ou en cerise ;
  - `scarf`, `pauldrons` (épaulettes), `gloves` (longs gants, clous, annelés), `loincloth` (pagne) ;
  - `top` (haut ajusté, épaules nues, une bretelle), `boots` (bottes, bouts pointus, annelées) ;
  - `helmet` (casque à pointe en V, tuyau entre les oreilles), `tanks` (bouteilles dans le dos), `cheek_guards` (protections de joues) ;
  - `body_lines` (lignes ondulées sur le corps), `veins` (veines), `tendrils` (filaments qui se déroulent des jambes) ;
  - `sword` : une lame tenue en main, avec garde simple ou en panier.

  `emblem` se place aussi sur les coudes, la ceinture ou sous le menton ; `headband` peut porter une pierre en cœur ; `earring` existe en cœur brisé ; `belt` peut avoir des poches.

Les Stands se font de la même façon (`star_platinum.toml`, `hierophant_green.toml`, `the_world.toml`, `silver_chariot.toml`). Dans `roster.toml`, la clé `stand_sprite` d'un perso indique la planche de son Stand : en combat, quand on appuie sur la touche Stand, il apparaît derrière son manieur et passe devant lui pour frapper.

Après une modification, régénère la planche :

```powershell
.\.venv\Scripts\python.exe tools\make_sprites.py jotaro_p3
```

Le script écrit la planche du jeu dans `jojo_arena/assets/sprites/<id>/`, et des aperçus agrandis dans `build/sprite_previews/` : `<id>.png` pour les 3 vues, `<id>_sheet.png` pour toutes les animations. Pour qu'un nouveau perso apparaisse dans le jeu, ajoute-le aussi dans `jojo_arena/characters/roster.toml`. Un test vérifie que les planches sont à jour par rapport à leur fiche.

### Format d'une planche

Une planche est un PNG en cases carrées (64 × 64 pour les persos générés) accompagné d'un TOML du même nom, qui donne aussi la taille des cases, le point des pieds, et les hauteurs de la poitrine et du haut de la tête (pour placer les effets). Le TOML liste les animations (`idle`, `walk`, `light`, `heavy`, `special`, `dash`, `guard`, `hurt`, `ko`, `pose`). Chaque animation occupe 3 lignes de la planche : vue de face (`down`), de dos (`up`) et de profil vers la droite (`right`). La gauche est le miroir de la droite.

- Une planche dessinée à la main peut remplacer une planche générée, sans changer le code : il suffit de garder les mêmes noms de fichiers.
- Si une planche manque, le jeu affiche une forme simple de la couleur du perso.

## Licence

Code sous licence [MIT](LICENSE).
