# Journal des changements

Ce que chaque version apporte, écrit pour un joueur. Les versions suivent
[SemVer](https://semver.org/lang/fr/) : un perso ou un mode en plus fait une mineure,
des corrections seules une patch.

## Non publié

### Ajouté

- **Entraînement avancé.** Le mannequin peut répéter **une action choisie dans son
  propre kit** (ORA ORA ORA, Star Finger, HHA, GHA, dash, pose…), avec le **délai de ton
  choix** entre chaque répétition, compté dès qu'il redevient libre d'agir — délai 0 =
  riposte à la frame près, pour vérifier si un coup est vraiment sûr. Options : enchaîner
  la suite du coup, se rapprocher quand le coup ne porte pas, tenir la garde entre deux.
  Un coup qui demande le Stand sorti : le mannequin le sort tout seul.
- **Enregistrer une action du mannequin** : J2 joue, Échap arrête, et la suite est
  rejouée en boucle.
- **Frise des frames** : deux bandes, une par perso, une colonne par image (démarrage,
  actif, récupération, garde, blocage, dégâts, gel), avec l'**avantage mesuré** du
  dernier échange.
- Données de frames **des deux côtés**, au format habituel `4/3/10  +6/-2`.
- **Détection de la manette par son constructeur** (identifiant SDL) : une DualShock 4 ou
  une DualSense affiche CROIX, CARRÉ, OPTIONS ; une manette Xbox affiche A, X, MENU,
  VIEW.
- **Vibration de la manette**, pilotée par ce qui se passe en combat : celui qui encaisse
  sent le poids du coup, celui qui le place sent le claquement ; Guard Break, mur, K.O.,
  gel, contre, arrêt du temps et ultimes ont leur propre motif. Sur DualShock 4 et
  DualSense, la **barre lumineuse prend la couleur du perso**. Réglable de 0 à 10 dans
  Options.
- **Deux réglages d'affichage** dans Options : `Clavier` (auto / AZERTY / QWERTY) et
  `Manette` (auto / Xbox / PlayStation), pour les cas où la détection se trompe. Ils ne
  changent que les noms affichés. Le nom exact des manettes branchées s'affiche sous le
  tableau des touches.

### Ajouté (combat)

- **L'aube tue pour de bon.** Les rais de soleil tombent d'abord sous les fenêtres, puis
  s'allongent jusqu'au mur du fond en 22 secondes : à la fin il ne reste que des bandes
  d'ombre. Et un mort-vivant qui s'attarde dans la lumière brûle de plus en plus vite
  (jusqu'à 3,5 fois) ; sortir de la lumière le calme. Un vampire qui ne bouge pas à l'aube
  perd le round.
- **Écran de choix de l'arène**, après le choix des persos : un aperçu grandeur demie du
  vrai décor (dessiné par le décor lui-même, pas une image), son nom, sa partie, et une
  entrée « au hasard ». Il s'ouvre sur l'arène de la partie du joueur 1.
- **Le château suisse**, l'arène de la partie 2 : dalles froides, neige qui traverse le
  hall, braseros, et les piliers sculptés de ceux qui dormaient dedans. L'aube des Alpes
  y finit par remplir 77 % du sol — contre 39 % au manoir : chaque hall a son propre
  rapport à la lumière.
- **Speedwagon appelle sa bande.** La touche Stand fait venir **Tattoo** et ses couteaux
  lancés, puis **Amato** et son kempo, chacun avec son propre moveset et son sprite.
  Nouveau style réutilisable `stance_cycle`.
- **Jonathan** : Luck & Pluck est une rafale de six estocs de Hamon au lieu d'un seul, et
  Scarlet Overdrive frappe le sol pour envoyer une onde de Hamon à travers l'arène.
- **Bruford** : ses cheveux accompagnent l'épée sur tous ses coups, et le deuxième coup de
  son enchaînement est un fouet de mèches qui porte plus loin que la lame.

### Corrigé

- La grille de sélection des persos affichait une rangée de cases vides sous la partie 1 :
  elle s'arrête maintenant à la dernière rangée occupée.

- **Avantage de frame faux d'une image.** `TOUCHÉ` et `GARDE` comptaient l'image du coup
  deux fois côté attaquant : le direct de Jotaro annonçait +7 et −1 au lieu de +6 et −2.
  Les chiffres correspondent maintenant à ce que la frise mesure sur un vrai combat.
- **Icônes du glossaire** : les Hommes du Pilier montraient un pilier de pierre au lieu
  d'un homme, et le Rokakaka une boule orange au lieu du fruit.
- Les derniers endroits où une touche était écrite en dur (« ENTRÉE OU A », « ÉCHAP »)
  suivent maintenant la configuration du joueur et sa manette.

### Interne

- `make coverage`, `make docker-check`, image Docker pour vérifier le code sans rien
  installer.
- CI : lint séparé et rapide, tests sur Windows **et** Linux, couverture, annulation des
  runs devenus inutiles, cache pip. La Release refuse de publier si la version et le tag
  ne correspondent pas.
- Gabarits de PR et d'issues (le gabarit bug demande le replay), Dependabot mensuel.
- Crochet `commit-msg` : format conventionnel, sujet court, aucune mention d'outil d'IA.
- `.claude/agents/` et `.claude/skills/` : voir [docs/AGENTS.md](docs/AGENTS.md).

## 0.1.0

Premier prototype jouable : le moteur à 60 Hz déterministe, les parties 1, 2 et 3 (16
persos), deux arènes, les styles Stand / Hamon / Vampire, les modes Entraînement, Combat
local, Contre l'IA et Arcade, les ultimes en cinématique, la musique et les bruitages
générés dans le code, le français et l'anglais, les touches modifiables et les replays.
