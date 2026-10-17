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

- **La touche Power Up sert enfin : l'éveil.** Kars pose le masque de pierre et la Super
  Aja pour deux barres et devient la **forme de vie ultime** : le soleil ne lui fait plus
  rien, son moveset entier change (griffes qui s'adaptent, main qui dévore, ailes, sa
  propre onde), chaque coup lui rend de la vie, et il ne peut plus revenir en arrière.
  La mécanique est générique : n'importe quel kit peut déclarer son `[awakening]`.
- **Les persos de la partie 2 redessinés d'après JoJo Wiki.** Wamuu est bronzé avec une
  seule corne et le tatouage en barre, pas pâle avec deux cornes ; Esidisi a sa croix sur
  le visage ; Kars a les cheveux noirs ondulés sous un bandeau, pas une crête violette ;
  Santana a deux petites cornes et des cheveux jusqu'aux épaules ; Stroheim a un monocle
  sur l'œil droit, pas un demi-masque. Le générateur sait maintenant dessiner une corne
  unique et des marques de visage.
- **La partie 2 est complète** : Wamuu, Esidisi, Kars, Santana et Stroheim rejoignent
  Joseph, Caesar, Lisa Lisa et Straizo. Les quatre Hommes du Pilier ont la nature
  `pillar_man` — l'onde leur fait double, et le soleil les tue — et trois d'entre eux ont
  leur **Mode** sur la touche Stand : le vent, la flamme, la lumière. Santana n'en a
  aucun, parce qu'il ne l'a jamais appris.
- **Des coups qui coûtent de la vie** : le Final Mode de Wamuu prend 300 PV à Wamuu, les
  jets de sang d'Esidisi lui coûtent le sien, et Stroheim s'ouvre la poitrine. Un tel coup
  ne sort pas s'il tuerait son auteur.
- **Lame qui ricoche** : un projectile peut maintenant repartir du mur au lieu de mourir
  contre lui (la lame lancée de Kars, trois rebonds).
- Quatre nouvelles cinématiques d'ultime : le Rift Atmosphérique, les Larmes d'Esidisi,
  l'Ultimate Thing et l'autodestruction.

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

- **Aspiration.** Un coup peut tirer l'adversaire vers lui tant qu'il est actif
  (`pull`, `pull_range`) : le Contrecoup de la Tornade de Wamuu l'arrache de l'autre bout
  du terrain, et la Divine Sandstorm aspire ce qu'elle broie.
- **Les ultimes ont la forme de leur technique.** Rift Atmosphérique : un rayon de vent
  tiré par la corne, d'un bout à l'autre de l'arène. Les trucs du métier de Joseph : des
  câbles lancés sur toute la largeur devant lui. Les Larmes d'Esidisi : un jet de sang
  bouillant. Déluge de lumière de Kars : une nappe de neuf lames. Bubble Barrier et Burn
  Black de Caesar : le dôme de bulles et le cercle de loupes se referment là où
  l'adversaire se trouve. Autodestruction de Stroheim : tout ce qui l'entoure. Road
  Roller : il tombe sur sa position.
- **Divine Sandstorm** : les avant-bras tournent pendant tout le démarrage, puis deux
  vraies tornades qui portent à 92 (150 pour la version ultime) et aspirent.
- **La Chaîne d'Onde de Lisa Lisa.** Son premier coup ouvre une chaîne à
  embranchements : trois touches pour la continuer, trois pour la finir, dont une prise
  imparable. Personne d'autre n'a ça.
- **Caesar** : l'Uppercut d'une main et le Ripple Kick (intouchable pendant le vol) à la
  place de ses coups génériques, et ses Bubble Cutters ricochent sur les murs.
- **Équilibrage.** Kars descend de 81 % à 69 % de victoires contre le reste du casting
  (1000 PV, lames de lumière moins fortes, déluge moins long) ; Caesar remonte de 21 % à
  30 % — un maillon de son enchaînement lui coûtait du Hamon pour rien ; Esidisi de 18 %
  à 23 %, son sang lui coûte moins cher.

- **Bilan de fin de combat.** Une fois le dernier round joué : dégâts, meilleur combo,
  plus gros coup, ultimes dépensés et durée, pour chacun des deux, aux couleurs des
  persos.
- **Les coups font du bruit.** La tornade souffle, la corne de Wamuu siffle, la Tommy
  Gun crache, les veines d'Esidisi giclent, les câbles de Joseph cliquettent et les
  lames sonnent. Avant, seul le moment où ça touchait faisait un son.
- **Frapper avec ce qu'on porte.** En portant une caisse ou une jarre, la touche Lourd
  la balance : lent, large, et on la garde en main pour recommencer ou la lancer.
- **Bruford porte avec ses cheveux.** On voit les mèches s'enrouler autour de l'objet,
  tenu derrière lui, mains libres — et il le balance au bout de ses cheveux, trois fois
  plus loin qu'un bras. En échange il le **lance moins fort** : on ne met pas son
  corps derrière un jet tenu à bout de mèches. Hierophant Green fait pareil avec
  ses tentacules.
- **L'épée de Bruford est au bout de ses cheveux** : son coup lourd porte à 48 au lieu
  de 26.
### Corrigé

- **Une tornade n'est pas une rafale de poings.** Un coup multi-hit qui a son propre
  effet (tornade, veines, câbles) affichait quand même une rafale de poings par-dessus.
- **La Super Aja de Lisa Lisa** faisait tomber un bloc de béton : c'est maintenant une
  colonne de lumière qui descend sur l'adversaire.
- **Portées d'armes** : les cheveux et l'épée de Bruford, et la rapière de Silver
  Chariot, portaient moins loin qu'un direct.

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
