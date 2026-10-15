# JoJo Arena

Fan game **gratuit, open source et non commercial** : un arena fighter 1v1 en temps réel, en pixel art vu de dessus, avec un grand roster des 9 parties de JoJo's Bizarre Adventure.

> **Fan game non officiel.** Ce projet est gratuit, sans but lucratif, et n'est affilié ni à Hirohiko Araki, ni à Shueisha, ni à David Production, ni à CyberConnect2. JoJo's Bizarre Adventure et toutes les marques citées appartiennent à leurs propriétaires respectifs.

## État du projet

Prototype jouable de la **Vague 0** (moteur) : combat local J1 contre J2 sur l'arène du Caire, avec deux mannequins génériques. Aucun personnage de JoJo n'est encore jouable. Le game design complet est dans [docs/GDD.md](docs/GDD.md).

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
  characters/   roster.toml et une fiche de jeu par perso (mannequin.toml)
  stages/       arènes : données (.toml) et rendu
  ui/           écrans, HUD, menus
  assets/       sprites (et plus tard sons, portraits)
tools/          générateur du mannequin, build du .exe
tests/          pytest
```

Toutes les valeurs d'équilibrage sont dans des fichiers TOML commentés : `combat/rules.toml` (règles globales) et `characters/*.toml` (attaques de chaque perso).

## Ajouter ou remplacer des sprites

Une planche de sprites, c'est un PNG en cases de 48 × 48 accompagné d'un TOML du même nom, dans `jojo_arena/assets/sprites/<nom>/`. Le TOML liste les animations (`idle`, `walk`, `light`, `heavy`, `special`, `dash`, `guard`, `hurt`, `ko`, `pose`). Chaque animation occupe 3 lignes de la planche : vue de face (`down`), de dos (`up`) et de profil vers la droite (`right`). La gauche est le miroir de la droite.

- Le mannequin générique `assets/sprites/mannequin/` sert de base à habiller. Il est généré par `tools/make_mannequin.py`.
- Remplacer une planche ne demande aucun changement de code : il suffit de garder les mêmes noms de fichiers.
- Si une planche manque, le jeu affiche une forme simple de la couleur du perso.

## Licence

Code sous licence [MIT](LICENSE).
