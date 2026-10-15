# Roadmap

Ce qui est fait, ce qui est en cours et ce qui vient ensuite. Le détail du game design est dans [GDD.md](GDD.md) ; ce fichier dit **dans quel ordre** on le construit. On coche au fur et à mesure.

## Fait

- [x] **Vague 0, le moteur** : boucle à 60 Hz déterministe, arène du Caire, garde, esquive, Heart Heat, clash, rounds, mort subite.
- [x] **Vague 1, les kits** : Jotaro, DIO, Kakyoin et Polnareff, avec Stand visible et touchable, et le temps arrêté (avec la règle des deux time stoppers).
- [x] **Apparences générées** depuis les fiches `characters/looks/`.
- [x] **Menus** : écran titre, menu principal (modes « Bientôt »), sélection des persos, écran VS, pause, options, liste des coups.
- [x] **Entraînement** : mannequin immobile, en garde ou joué par J2 ; vie et jauge infinies ; compteur de combo.
- [x] Couteaux, émeraudes et lame dessinés en vrai ; Star Finger qui s'allonge jusqu'à mi-distance.
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
6. [ ] **Mode contrôle de Hierophant Green**, comme dans le GDD :
   - piloter HG loin de Kakyoin ;
   - fouet, Emerald Splash et fils depuis HG ;
   - possession de l'adversaire pendant 1,5 s ;
   - retour immédiat de HG, et Kakyoin sonné, s'il est touché.
7. [ ] **Objets de l'arène** : ramasser (touche Pose près d'un objet) et lancer une caisse ou une jarre ; elle réapparaît à sa place plus tard.
8. [ ] **Ultimes (GHA) en cinématique**, avec caméra (zoom, travelling, tremblement). L'ultime commence par un coup : s'il touche, la cinématique se lance et les dégâts tombent à la fin ; s'il rate, temps de récupération.
   - **DIO, Road Roller** : il frappe et le temps s'arrête. Il part hors champ, revient par les airs avec le rouleau compresseur et écrase l'adversaire. Il martèle le rouleau de MUDA, puis le temps reprend et tout explose.
   - **Kakyoin, Emerald Splash 20 mètres** : courte cinématique où HG parcourt l'arène en posant ses fils. Les tentacules couvrent ensuite toute l'arène comme une toile d'araignée : la toucher déclenche des Emerald Splash automatiques, pendant que Kakyoin continue de se battre.
   - **Jotaro** : temps arrêté, ORA en gros plan, et le temps reprend sur l'impact.
   - **Polnareff** : les clones d'Armor Off frappent de tous les côtés.
9. [x] **Équilibrage, premier passage** :
   - baisse des dégâts sur les longs combos ;
   - dégâts réduits pendant le temps arrêté ;
   - saisie de DIO moins abusive.

## Ensuite

- [ ] **Sons** : bruitages synthétisés (impacts, whoosh, temps arrêté), et musique libre de droits.
- [ ] **Contre l'IA** : une vraie IA par niveau de difficulté (le mode est déjà affiché « Bientôt »).
- [ ] **Arcade** : une suite de combats contre l'IA.
- [ ] **Entraînement avancé** : enregistrer puis rejouer une action du mannequin, affichage des hitboxes, données de frames.
- [ ] **Réglage des touches dans le jeu** (aujourd'hui dans `controls.json`).
- [ ] **Power Up et jauge d'Éveil** (Jotaro : +1 s de temps arrêté).
- [ ] **Flèche** et Chariot Requiem.
- [ ] **Vague 2** (JoJolion), **Vague 3** (Hamon), **Vague 4** (icônes) : voir les priorités du GDD.
- [ ] **Histoire**, puis **en ligne** (la simulation déterministe le prépare).

## Outillage

- `make check` avant de pousser ; `make hooks` une fois pour que ça se fasse tout seul à chaque commit.
- La CI de GitHub lance le lint, tous les tests (y compris les combats aléatoires) et la tournée de captures (artefact `screenshots`). Sur `main`, elle construit aussi un `.exe` de test (artefact `JoJoArena-test-exe`).
- Une Release avec le `.exe` se crée en poussant un tag `v*` (voir le README).
