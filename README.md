# JoJo Arena

Fan game **gratuit, open source et non commercial** : un arena fighter 1v1 en temps réel, en pixel art vu de dessus, avec un grand roster des 9 parties de JoJo's Bizarre Adventure.

> **Fan game non officiel.** Ce projet est gratuit, sans but lucratif, et n'est affilié ni à Hirohiko Araki, ni à Shueisha, ni à David Production, ni à CyberConnect2. JoJo's Bizarre Adventure et toutes les marques citées appartiennent à leurs propriétaires respectifs.

## État du projet

Prototype jouable de la **Vague 0** (moteur) : combat local J1 contre J2 sur l'arène du Caire. Jotaro, Kakyoin, DIO et Polnareff (Partie 3) ont leur apparence et leur Stand visible, mais combattent encore avec les coups du mannequin générique en attendant leur kit (Vague 1). Le game design complet est dans [docs/GDD.md](docs/GDD.md).

Ce qui marche déjà :

- attaques légère, lourde et spéciale (projectile), combos par annulation sur coup réussi ;
- garde (−80 % de dégâts), jauge de garde et Guard Break ;
- dash avec invincibilité, Stylish Evade (esquive au dernier moment : ralenti) ;
- jauge Heart Heat à 3 barres, HHA (1 barre), Flash Cancel (½ barre), Pose, Résolution ;
- clash : deux attaques simultanées, on martèle pour gagner le duel ;
- recul, rebond sur les murs, étals et caisses cassables ;
- touche Stand : bascule entre deux jeux d'attaques, avec une aura ;
- rounds (1, 3 ou 5 gagnants), timer de 99 s, mort subite en cas d'égalité ;
- clavier et manette (Xbox, DualShock 4, DualSense), touches modifiables.

## Jouer

Télécharge `JoJoArena.exe` dans la dernière [Release](../../releases) et lance-le. Rien à installer.

- **F11** ou **Alt+Entrée** : plein écran.
- **Échap** (ou Start) : pause.

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
| Heart Heat (HHA) | O | RT / R2 | T | 9 |
| Pose | P | Select / Touchpad | Y | 7 |
| Power Up (pas encore utilisé) | U | LT / L2 | B | 3 |

Choisis la configuration (J1 clavier + J2 manette, clavier partagé, deux manettes) dans l'écran **Combat local**.

Pour changer les touches, modifie `controls.json` dans `%APPDATA%\JoJoArena\` puis relance le jeu. Le fichier explique les noms de touches. Supprime-le pour revenir aux réglages par défaut.

## Développement

Il faut Python 3.12 ou plus récent.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Lancer le jeu

```powershell
.\.venv\Scripts\python.exe -m jojo_arena
```

Options utiles :

| Commande | Effet |
| --- | --- |
| `--demo` | combat joué par l'ordinateur des deux côtés |
| `--scene fight --rounds 1` | va droit au combat, en 1 round gagnant |
| `--p1 jotaro_p3 --p2 mannequin_red` | choisit les persos (avec `--scene fight` ou `--demo`) |
| `--fullscreen` | démarre en plein écran |
| `--frames 300 --screenshot capture.png` | joue 300 images puis enregistre l'image 480 × 270 (tests rapides) |

> Si Python vient du Microsoft Store, Windows range `controls.json` dans `%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.xx_...\LocalCache\Roaming\JoJoArena\` quand le jeu tourne depuis les sources. Le `.exe`, lui, utilise bien `%APPDATA%\JoJoArena\`.

### Tests et lint

```powershell
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

GitHub Actions les lance aussi à chaque push (`.github/workflows/ci.yml`).

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
