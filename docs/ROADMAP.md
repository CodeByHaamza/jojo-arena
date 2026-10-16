# Roadmap

Ce qui est fait, ce qui est en cours et ce qui vient ensuite. Le détail du game design est dans [GDD.md](GDD.md) ; ce fichier dit **dans quel ordre** on le construit. On coche au fur et à mesure.

## Fait

- [x] **Vague 0, le moteur** : boucle à 60 Hz déterministe, arène du Caire, garde, esquive, Heart Heat, clash, rounds, mort subite.
- [x] **Vague 1, les kits** : Jotaro, DIO, Kakyoin et Polnareff, avec Stand visible et touchable, et le temps arrêté (avec la règle des deux time stoppers).
- [x] **Apparences générées** depuis les fiches `characters/looks/`.
- [x] **Menus** : écran titre, menu principal (modes « Bientôt »), sélection des persos, écran VS, pause, options, liste des coups.
- [x] **Entraînement** : mannequin immobile, en garde ou joué par J2 ; vie et jauge infinies ; compteur de combo.
- [x] Couteaux, émeraudes et lame dessinés en vrai ; Star Finger qui s'allonge jusqu'à mi-distance.
- [x] Entraînement : affichage des touches en direct, zones de frappe avec F3.
- [x] The World et Silver Chariot redessinés d'après des références.
- [x] Duel de rafales : écran de face-à-face aux couleurs des persos, 5 s à marteler.
- [x] Onomatopées façon JoJo (ゴゴゴ, ドン, バーン…), cris des persos (ORA, MUDA, ZA WARUDO…), éclairs, ondes de choc, poussière.
- [x] Outillage : Makefile, hook avant commit, CI (lint, tests, combats aléatoires, captures de tous les écrans), `.exe` de test à chaque push sur `main`, Release sur tag.

## En cours : sensations et identité des persos (retours du 15/10/2026)

Chaque perso doit avoir un ressenti unique, et chaque coup qui touche doit être satisfaisant.

1. [x] **Rafales spectaculaires** : nuée de poings, le Stand avance en poussant, dernier coup qui projette. Rafale contre rafale : duel à marteler (QTE) mis en scène.
2. [x] **Poses iconiques** propres à chaque perso, avec les ゴゴゴゴ.
3. [x] **Nouvelles mécaniques de coups**, réutilisables par tous les kits :
   - enchaînements (léger, léger, léger donnent trois coups différents) ;
   - contre ;
   - bond sur l'adversaire ;
   - coups blindés ;
   - casse-garde ;
   - coups qui attirent ;
   - Stand qui surgit le temps d'un coup.
4. [x] **Nouveaux kits** pour les quatre persos (détail dans les décisions du GDD).
5. [x] **Visée libre** (souris pour le clavier, stick droit pour la manette) : le **grappin** de Kakyoin vise un point choisi au curseur.
6. [x] **Mode contrôle de Hierophant Green**, comme dans le GDD :
   - piloter HG loin de Kakyoin ;
   - fouet, Emerald Splash et fils depuis HG ;
   - possession de l'adversaire pendant 1,5 s ;
   - retour immédiat de HG, et Kakyoin sonné, s'il est touché.
7. [x] **Objets de l'arène** : ramasser (touche Pose près d'un objet) et lancer une caisse ou une jarre ; elle réapparaît à sa place plus tard.
8. [x] **Ultimes (GHA) en cinématique**, avec caméra (zoom, travelling, tremblement). L'ultime commence par un coup : s'il touche, la cinématique se lance et les dégâts tombent à la fin ; s'il rate, temps de récupération.
   - **DIO, Road Roller** : il frappe et le temps s'arrête. Il part hors champ, revient par les airs avec le rouleau compresseur et écrase l'adversaire. Il martèle le rouleau de MUDA, puis le temps reprend et tout explose.
   - **Kakyoin, Emerald Splash 20 mètres** : courte cinématique où HG parcourt l'arène en posant ses fils. Les tentacules couvrent ensuite toute l'arène comme une toile d'araignée : la toucher déclenche des Emerald Splash automatiques, pendant que Kakyoin continue de se battre.
   - **Jotaro** : temps arrêté, ORA en gros plan, et le temps reprend sur l'impact.
   - **Polnareff** : les clones d'Armor Off frappent de tous les côtés.
9. [x] **Équilibrage, premier passage** :
   - baisse des dégâts sur les longs combos ;
   - dégâts réduits pendant le temps arrêté ;
   - saisie de DIO moins abusive.

## Prochaines idées pour la base

- [x] **Relecture de combat** : les entrées sont enregistrées (en quittant, ou F9) et `--replay` rejoue exactement le même combat.
- [x] **Données de frames en entraînement** : démarrage, actif, récupération et avantage du dernier coup.
- [x] **Animations par images-clés dans les fiches** : `[anims.<nom>]` pose par pose, avec images intermédiaires (voir CONTRIBUTING). Premiers coups : Yare yare daze, couteaux de DIO, Emerald Splash.
- [x] **Bot d'équilibrage** : `make balance` fait combattre les bots sur chaque duel et donne les taux de victoire.
  Le bot ne joue ni le zoning ni le contrôle à distance : ses chiffres mesurent la force brute, pas plus.

## En cours : tout JoJo, pas seulement la partie 3 (retours du 16/10/2026)

- [x] **Persos de la partie 3 redessinés** d'après l'anime : crinière et épaulières de Star Platinum, Hierophant vert et blanc, cheveux dressés de DIO, ceintures de Jotaro.
- [x] **Français et anglais** : langue dans Options (gardée dans `settings.json`), `--lang en`, traductions des coups dans les kits.
- [x] **Écrans pour tout JoJo** : fond des menus aux couleurs des 9 parties (trame manga, ゴゴゴ), écran titre partie par partie avec les 9 emblèmes, sélection des persos en onglets par partie, emblème de la partie sur chaque case (masque de pierre, Super Aja, plaque de Jotaro...).
- [x] **Glossaire** : termes du lore (masque de pierre, onde, Hommes du Pilier, Super Aja, Stand, tarot, temps arrêté, flèche, Requiem, rotation, Rokakaka), personnages et Stands de la partie 3 (description, famille, origine du nom, statistiques), par partie, avec icônes en pixel art. À compléter avec chaque nouveau perso.
- [x] **Partie 1** : styles Hamon et vampire faits (jauges, respiration, sang, cicatrisation, gel vaporisant, soleil). Jonathan, Zeppeli, Dio Brando (yeux laser, Absorption), Bruford et Tarkus (zombies, anneau de chaînes) et Speedwagon (chapeau boomerang) jouables, avec le manoir Joestar en flammes et son aube.

- [x] **Partie 2, première vague** : Joseph jeune (clackers boomerang, grenades, fils de Hamon, « Ta prochaine réplique sera... », la fuite, Tommy gun, plan caché), Caesar (Bubble Launcher, Bubble Cutter, Bubble Lens, Bubble Barrier), Lisa Lisa (écharpe fouet et lance, Snake Muffler qui renvoie les projectiles, saut acrobatique, piège de l'écharpe en cinématique) et Straizo (vampire tireur d'élite, posture de visée, rafale d'yeux en cinématique).
- [ ] **Partie 2, deuxième vague** : Wamuu, Esidisi, Kars, Santana (Hommes du Pilier, modes), Stroheim, le château suisse et son cycle jour/nuit. Détail préparé ci-dessous.

### Hommes du Pilier : ce qui est prêt à construire

Un **nouveau style réutilisable**, `pillar_man` (composant dans `combat/styles.py`, comme `hamon` et `vampire`), plutôt qu'un cas particulier par perso :

- nature `pillar_man` : déjà reconnue par le Hamon (dégâts doublés) et par le soleil ;
- la touche Stand passe en **Mode** (流法) : une jauge qui se vide, des coups transformés ;
- chacun a le sien, ce qui donne quatre persos très différents avec un seul composant.

| Perso | Mode | Coups | Ultime |
| --- | --- | --- | --- |
| **Wamuu** | Mode du Vent | Divine Sandstorm (神砂嵐, tourbillon qui traverse), corne-canon à vent, fils anti-Hamon du casque, Wind Suit (invisible, renvoie la lumière) | **Final Mode : Atmospheric Rift** (最終流法・渾楔颯) : immense, et il s'abîme lui-même — parfait pour un ultime qui coûte de la vie |
| **Esidisi** | Mode de la Flamme | sang bouillant à 500 °C projeté par les veines, mode « Rumble » automatique sous 30 % de vie | les larmes et le sang en pluie sur toute l'arène |
| **Kars** | Mode de la Lumière | Light Blades (輝彩滑刀) des bras et des jambes, lames qui ricochent sur les murs | **Ultimate Thing** : il gagne du Hamon et une régénération — un éveil en fin de combat, pas un coup |
| **Santana** | aucun (il ne l'a pas maîtrisé) | se faufile dans le corps de l'adversaire, lames de côtes, corps qui se déforme | absorption complète |

Sources : [JoJo Wiki — Wamuu](https://jojowiki.com/Wamuu), [Kars](https://jojowiki.com/Kars), [Pillar Men](https://jojowiki.com/Pillar_Men), [ASBR Wamuu](https://jojowiki.com/ASBR/Wamuu), [ASBR Kars](https://jojowiki.com/ASBR/Kars).

Ce que ça apporte au jeu, au-delà du roster : le Hamon et le soleil **servent enfin à quelque chose contre un adversaire qui frappe fort**, et le trio Wamuu / Esidisi / Kars donne trois façons de jouer qui n'existent pas encore (lutteur d'honneur, zoneur dégueulasse, caméléon qui s'éveille).

## Ensuite

- [x] **Bruitages** synthétisés dans le code (coups, garde, clash, temps arrêté, K.O., Hamon, gel, soleil, chaînes, yeux laser, menus), volume dans Options.
- [x] **Musique** : boucles chiptune originales générées dans le code (menus, le Caire, le manoir Joestar), volume à part dans Options.
- [x] **Contre l'IA** : une IA à quatre niveaux (facile, normal, difficile, JoJo) qui garde la distance de son kit, se défend, punit et enchaîne.
- [x] **Arcade** : six combats contre l'IA, de plus en plus durs, chacun dans l'arène de l'adversaire, jusqu'à DIO ; on peut continuer après une défaite.
- [x] **Entraînement avancé** : action du mannequin choisie dans son kit avec délai réglable entre chaque répétition (0 = riposte à la frame près), enchaînement, rapprochement, garde entre deux ; enregistrer une action jouée par J2 et la rejouer en boucle ; frise des frames des deux persos avec l'avantage mesuré ; données de frames des deux côtés.
- [x] **Réglage des touches dans le jeu** : Options, « Changer les touches » (échange si la touche est déjà prise, retour aux touches par défaut).
- [x] **Vibration et barre lumineuse** de la manette, par événement de combat ; couleur du perso sur DualShock 4 / DualSense ; réglage de 0 à 10 dans Options.
- [ ] **Power Up et jauge d'Éveil** (Jotaro : +1 s de temps arrêté).
- [ ] **Flèche** et Chariot Requiem.
- [ ] **Vague 2** (JoJolion), **Vague 3** (Hamon), **Vague 4** (icônes) : voir les priorités du GDD.
- [ ] **Histoire**, puis **en ligne** (la simulation déterministe le prépare).

## Idées proposées le 16/10/2026

Classées par ce qu'elles apportent pour ce qu'elles coûtent.

### Rapides et qui se sentent tout de suite

- [ ] **Défis d'entraînement** : « fais 5 coups d'affilée avec Jotaro », « punis le coup de tête », « sors le Star Finger après une garde ». Le mode entraînement sait déjà tout mesurer (combo, frise, avantage) ; il ne manque qu'une liste d'objectifs en TOML et un écran de validation. C'est ce qui apprend le jeu à un joueur sans tutoriel.
- [ ] **Sauver un réglage d'entraînement** : l'action du mannequin, le délai et les options dans `settings.json`, pour retrouver sa situation de travail en relançant.
- [ ] **Vitesse d'entraînement** : jouer à 50 % ou 25 % de vitesse pour voir un enchaînement se dérouler. Le pas fixe le permet sans toucher à la simulation.
- [ ] **Arrêt sur image et avance image par image** en entraînement (F7 / F8) : la frise devient un outil d'analyse complet.

### Le jeu lui-même

- [ ] **Power Up et jauge d'Éveil** (déjà dans la roadmap) : la touche existe, elle ne sert à rien ; c'est la mécanique manquante la plus visible.
- [ ] **Partie 4** (Josuke, Crazy Diamond qui répare le décor et renvoie les projectiles) : le décor destructible existe déjà, Crazy Diamond lui donnerait un sens.
- [ ] **Deuxième arène par partie** : le château de Wamuu (piliers à casser), la grotte de Santana. Les arènes font autant pour l'identité d'une partie que les persos.
- [ ] **Écran de fin de combat** : meilleur combo, dégâts totaux, temps — lu directement du combat, sans nouvelle mécanique.

### Plus gros, mais c'est là que le jeu devient un jeu

- [ ] **Mode Histoire** partie par partie, avec les cinématiques déjà écrites et des conditions de victoire spéciales (« gagne sans être touché », « finis par un Hamon »).
- [ ] **En ligne en rollback** : la simulation est déterministe et les entrées sont déjà sérialisées pour les replays — les deux prérequis sont faits. C'est le plus gros chantier du projet, et le seul qui change ce qu'est le jeu.

## Outillage

- `make check` avant de pousser ; `make hooks` une fois pour que ça se fasse tout seul à chaque commit.
- La CI de GitHub lance le lint, tous les tests (y compris les combats aléatoires) et la tournée de captures (artefact `screenshots`). Sur `main`, elle construit aussi un `.exe` de test (artefact `JoJoArena-test-exe`).
- Une Release avec le `.exe` se crée en poussant un tag `v*` (voir le README).
