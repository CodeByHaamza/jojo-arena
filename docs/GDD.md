# JoJo Arena — Game Design Document

Oct 15, 2026 · @Hamza

## Vision

JoJo Arena est un fan game gratuit et open source : un arena fighter 1v1 en temps réel, en pixel art, vu de dessus, avec le plus de personnages possible des 9 parties. Chaque perso a une identité de gameplay forte et fidèle à l'œuvre, y compris les règles des Stands entre eux (time stop contre time stop, Tusk Act 4, etc.).

- **Références** : Pokémon Arena de Big Kid Nation (rendu, vue, arènes) ; All Star Battle R (sensation de combat, Stand on/off, jauges) ; Eyes of Heaven (arènes destructibles, ultimes spectaculaires).
- **Format** : 1v1 au lancement, en modes Arcade, contre l'IA et J1 contre J2 en local ; mode Histoire plus tard. 2v2 et free-for-all possibles plus tard, déjà prévus dans certains kits (Anasui, Giorno).
- **Technique** : Python + Pygame, livré en .exe (PyInstaller). Clavier et manette.
- **Rendu** : sprites de 48 px au contour noir, résolution interne de 480 × 270 agrandie sans lissage, sols ternes et persos saturés, ombres portées, glow additif sur les effets (Stands, Hamon, explosions).
- **Art** : persos et Stands en sprites. Placeholders géométriques d'abord ; les sprites finaux seront faits par toi ou des contributeurs.
- **Statut légal** : projet non commercial, non affilié à Araki, Shueisha ou David Production. Un retrait (DMCA) reste possible ; garder le code moteur séparé des assets pour pouvoir réutiliser le moteur.

## Règles globales

Un combat se gagne en vidant la barre de vie adverse, sur un nombre de rounds choisi à la création du match. Toutes les valeurs ci-dessous sont des valeurs de départ, à équilibrer en test.

| Élément | Règle proposée |
| --- | --- |
| Vie | 1000 PV par perso (les tanks jusqu'à 1150, les glass cannons vers 850) |
| Rounds | Choisis avant le match : 1, 3 ou 5 rounds gagnants. Timer 99 s, à zéro le plus de vie en % gagne |
| Jauge Heart Heat (HH) | 3 barres. Se remplit en frappant, en prenant des coups et en posant. 1 barre = attaque Heart Heat (HHA), 2 barres = Great Heat (GHA, l'ultime cinématique) |
| Garde | Bloquer réduit les dégâts de 80 %. Jauge de garde : vide = Guard Break (stun 1,5 s) |
| Esquive | Dash court avec frames d'invincibilité. Esquive au dernier moment = **Stylish Evade** : ralenti bref + petit gain de HH |
| Clash (Ora vs Muda) | Deux attaques qui se touchent au même instant (rush contre rush, coup contre coup) déclenchent un clash comme dans ASBR : les deux joueurs martellent la touche d'attaque pendant 5 s, une barre de duel bouge à l'écran, le perdant prend tout le rush et est éjecté ; égalité : rien |
| Flash Cancel | 1/2 barre de HH pour annuler une attaque en cours (combos et feintes) |
| Pose | Touche dédiée. Pose JoJo vulnérable qui recharge un peu de HH. Certains persos en tirent un effet unique |
| Résolution | Sous 25 % de vie : +15 % de dégâts et la garde ne prend plus de dégâts résiduels |
| Murs et décor | Les coups lourds envoient contre les murs (wall bounce). Le décor peut se casser, et certains persos l'utilisent |
| Stand touché | Quand le Stand est sorti, un coup sur le Stand blesse l'utilisateur (règle de l'œuvre) |
| Finish dramatique | Finir un round avec une GHA ou un élément d'arène déclenche un finish spécial (écran « To Be Continued ») |

## Contrôles

Onze touches suffisent pour tous les persos ; la touche Stand change le moveset des trois touches d'attaque. Mapping provisoire, rebindable dans les options.

| Action | Clavier | Manette |
| --- | --- | --- |
| Déplacement (8 directions) | ZQSD | Stick gauche |
| Visée libre (persos à projectiles) | Souris | Stick droit |
| Attaque légère | J | X / Carré |
| Attaque lourde | K | Y / Triangle |
| Spéciale (+ direction = variante) | L | B / Rond |
| Stand on/off (ou Hamon, posture, cheval…) | I | RB / R1 |
| Esquive / dash | Espace | A / Croix |
| Garde | Shift | LB / L1 |
| Heart Heat : HHA ; direction + Heart Heat : GHA (2 barres) | O | RT / R2 |
| Pose | P | Select / Touchpad |

Onzième touche, **Power Up** : U au clavier, LT / L2 à la manette (voir la section Power Up). Mode contrôle des Stands à longue portée : maintenir la touche Stand 0,5 s.

Par défaut, la visée suit l'adversaire le plus proche ; la visée libre sert aux persos à projectiles contrôlables (Hol Horse, Mista, Gyro).

## Styles de combat (ce que fait la touche Stand)

Chaque perso appartient à un style, qui décide de ce que fait sa touche Stand et de sa jauge propre. Coder ces styles une fois permet d'ajouter des persos vite.

| Style | Touche Stand | Jauge propre | Exemples |
| --- | --- | --- | --- |
| **Stand** | Sort ou rentre le Stand : moveset différent, plus fort mais le Stand peut être touché | Aucune (ou jauge spécifique au perso) | Jotaro, Josuke, Giorno |
| **Stand autonome** | Donne un ordre au Stand qui agit seul sur la carte | Selon le perso | Sheer Heart Attack, Sex Pistols, Doggy Style |
| **Hamon** | Maintenir = respiration : recharge le Hamon, immobile et vulnérable | Jauge de Hamon : les attaques boostées la consomment | Jonathan, Zeppeli, Joseph, Caesar, Lisa Lisa |
| **Vampire / Pillar Man** | Change de posture (corps, armes de chair, mode « mode ») | Jauge de sang : se remplit en drainant, se vide sous le soleil | Dio P1, Wamuu, Esidisi, Kars |
| **Rotation (Spin)** | Charge la rotation des projectiles | Jauge de rotation, débloque les Actes ou la Rotation Dorée | Gyro, Johnny |
| **Cheval** | Monte ou descend du cheval : vitesse énorme mais virages larges. Chevaux disponibles dans toutes les arènes | Endurance du cheval | Gyro, Johnny, Diego (option) |
| **Posture / forme** | Change de forme ou d'arme | Selon le perso | Kars, Diego (raptor), Pucci (évolution) |

**Hamon en détail.** La jauge de Hamon a 100 points. Une attaque boostée coûte 20 à 40 points ; sans Hamon, les coups restent normaux. Tenir la touche Stand recharge 25 points par seconde mais bloque les déplacements. Bonus : le Hamon fait double dégâts aux vampires et aux Pillar Men.

**Soleil.** Certaines arènes ont un cycle jour/nuit ou des zones ensoleillées (verrière cassée). Les vampires et Pillar Men y prennent des dégâts continus. Le Hamon y recharge plus vite.

## Power Up (éveil)

Certains persos ont une touche Power Up qui les fait évoluer en plein combat : nouvel Acte, nouveau Stand ou nouvelle forme, avec un moveset qui change. Elle utilise une **jauge d'Éveil** séparée de la jauge HH, qui se remplit selon une condition propre à chaque perso. Chaque éveil n'est utilisable qu'une fois par match et reste acquis jusqu'à la fin du match.

| Type | Animation | Vulnérabilité | Exemples |
| --- | --- | --- | --- |
| **Évolution courte** | \~0,6 s, courte pose + flash | Légère : peut être touché mais ne perd pas l'évolution | Passages d'Acte (Johnny Act 1→2→3, Koichi) |
| **Éveil majeur (game changer)** | 2,5 à 4 s, cinématique longue (zoom, fond qui s'assombrit, nom du Stand à l'écran) | Totale : +25 % de dégâts reçus. Si le joueur prend plus de 150 PV pendant l'animation, l'éveil est annulé et la jauge retombe à 50 % | GER, C-Moon, Made in Heaven, Go Beyond, Tusk Act 4, Kars Ultime |

L'adversaire voit toujours venir un éveil majeur : c'est volontaire, le moment de risque fait partie du gameplay (punir l'éveil, ou le protéger avec un piège ou un knockdown avant).

| Perso | Power Up | Remplir la jauge | Type | Ce qui change |
| --- | --- | --- | --- | --- |
| Johnny Joestar | Tusk Act 1 → 2 → 3 | Act 2 : ramasser une partie du Corps Saint. Act 3 : toucher avec les ongles | Courte | Act 2 : trou-projectile qui poursuit. Act 3 : se tire dans le trou pour se téléporter |
| Johnny Joestar | Act 3 → **Act 4** | Jauge pleine + avoir galopé (l'énergie du cheval, comme dans l'œuvre) | Majeure | Moveset Act 4 : coups en rotation infinie, ultime inbloquable |
| Koichi Hirose | Echoes Act 1 → 2 → 3 | Toucher et encaisser | Courte | Débloque l'Acte suivant ; ensuite la touche Stand passe d'un Acte débloqué à l'autre |
| Giorno Giovanna | Gold Experience → **Requiem** | Ramasser la Flèche dans l'arène | Majeure : la flèche transperce Gold Experience | Moveset GER + Return to Zero jusqu'à la fin du round |
| Enrico Pucci | Whitesnake → **C-Moon** | Voler 2 disques ou tenir 40 s | Majeure spéciale : les **14 mots** | Spammer Power Up : chaque appui dit un mot, au maximum 1 mot par seconde (marteler plus vite n'accélère pas). Les mots s'affichent à l'écran (« Escalier en colimaçon », « Scarabée rhinocéros », « Tarte aux figues »…). Pucci est vulnérable pendant les 14 s ; un coup reçu efface les 2 derniers mots. Au 14e mot : C-Moon, gravité inversée |
| Enrico Pucci | C-Moon → **Made in Heaven** | Jauge pleine à nouveau en phase C-Moon | Majeure, la plus longue (\~4 s) | Le temps accélère jusqu'à la fin du round (voir Interactions) |
| Josuke « Gappy » | Soft & Wet → **Go Beyond** | Bulles qui touchent | Majeure : longue mise en rotation | Toutes ses bulles deviennent Go Beyond (elles traversent tout, y compris Wonder of U) jusqu'à la fin du round |
| Kars | Forme normale → **Forme Ultime** | Sous 50 % de vie, jauge pleine | Majeure : masque de pierre + pierre d'Aja | Vol, plumes, tentacules, immunité au soleil |
| Jean Pierre Polnareff | Silver Chariot → **Chariot Requiem** | Ramasser la Flèche dans l'arène | Majeure : la flèche transperce Silver Chariot | Chariot Requiem devient un Stand autonome qui avance lentement. Quand il passe près des deux combattants, il échange leurs âmes : les joueurs échangent de perso pendant 6 s. Frapper la flèche dans son dos (coup par derrière) annule le Requiem |

## Mode contrôle (Stands à longue portée)

Les Stands à mi et longue portée ont un mode où l'on pilote le Stand seul, loin de son manieur, avec un moveset à part. Maintenir la touche Stand 0,5 s pour entrer en mode contrôle, appuyer de nouveau pour en sortir.

- Le manieur reste immobile et sans défense pendant ce temps.
- Au moindre coup sur le manieur, le Stand revient instantanément et le manieur est stun 0,8 s.
- Les coups reçus par le Stand blessent le manieur (règle de l'œuvre).
- Chaque Stand a une distance maximale ; au-delà, il ne peut plus avancer.

| Perso | Stand piloté | Moveset en mode contrôle |
| --- | --- | --- |
| Noriaki Kakyoin | Hierophant Green | Se dénoue en filaments et se faufile partout. Emerald Splash depuis n'importe quel angle. Peut entrer dans le corps de l'adversaire : contrôle de ses déplacements 1,5 s |
| Narancia Ghirga | Aerosmith | Pilotage d'avion en twin-stick : mitrailleuse, bombe, radar à CO2 qui montre l'adversaire même caché |
| Polpo | Black Sabbath | Ne voyage que dans les ombres de l'arène. Toucher l'ombre de l'adversaire = saisie et coup de flèche (gros dégâts) |
| Yasuho Hirose | Paisley Park | Saute d'appareil en appareil (écrans, téléphones), pose les lignes de « bon chemin », dérègle un appareil près de l'adversaire (étincelles, porte qui claque) |
| Shigekiyo Yangu | Harvest | Dirige l'essaim groupé : piqûres, injection d'alcool, vol d'objets au sol |
| Johngalli A. | Manhattan Transfer | Place le drone relais où il veut pour créer de nouveaux angles de tir |
| Keicho Nijimura | Bad Company | Commande l'armée : ordre d'avancer, de tirer, de se replier, appel des Apache |

## Objets de l'arène : Flèche et Corps Saint

Certains éveils ne passent pas par la jauge mais par un objet à ramasser dans l'arène, comme dans l'œuvre. N'importe quel perso peut ramasser l'objet pour en priver l'adversaire (petit soin à la clé) ; il réapparaît ailleurs 30 s plus tard.

| Objet | Quand il apparaît | Effet selon le perso |
| --- | --- | --- |
| **Flèche** | À 45 s dans un match avec Giorno ou Polnareff ; dès le début sur l'arène du Colisée | Giorno : la ramasser débloque le Power Up vers Gold Experience Requiem. Polnareff : débloque le Power Up vers Chariot Requiem (éveils majeurs) |
| **Corps Saint** (3 parties) | Dans un match avec Johnny, Gyro ou Valentine : une partie toutes les 20 s, à un endroit aléatoire | Gyro : 1re partie = **Scan** (voit à travers les murs, les camouflages et l'invisibilité) ; parties suivantes = rotation et dégâts boostés. Johnny : 1re partie = passage en **Act 2** ; parties suivantes = rotation, dégâts et temps de recharge boostés. Valentine : 3/3 parties = **Love Train** |

**Love Train en détail.** Actif tant que Valentine porte les 3 parties : les projectiles et les dégâts visés sur lui ne lui font rien et sont redirigés ailleurs. Seuls Tusk Act 4, Gold Experience Requiem et Go Beyond passent ; un coup de l'un des trois lui fait lâcher une partie (Love Train coupe). Un knockdown fait aussi lâcher une partie à Johnny ou Gyro.

## Altérations d'état (feu, gel, courant)

Un coup peut laisser quelque chose derrière lui. Trois altérations existent ; le moteur n'en
connaît pas d'autres tant que personne n'écrit leurs règles (`combat/status.py`, chiffres dans
`[status]` de `combat/rules.toml`, description joueur dans l'onglet **Règles du combat** du
glossaire).

| Altération | Durée max | Ce qu'elle fait | Qui la pose aujourd'hui |
| --- | --- | --- | --- |
| **burn** (feu) | 2,6 s | 26 PV/s, et **aucune plaie ne se referme** tant que ça brûle (régénération des vampires et des Hommes du Pilier coupée) | Esidisi (sang à 500 °C, Mode de la Flamme), Stroheim (lance-flammes) |
| **chill** (gel) | 2,2 s | marche à 60 %, **plus d'onde respirée ni de sang bu** | DIO, posture du gel vaporisant (après le gel net) |
| **shock** (courant) | 1,8 s | 10 PV/s, marche à 85 %, **plus un point de Heart Heat gagné**, jauge de garde qui se défait (18/s) | Lisa Lisa (l'écharpe de Satiporoja conduit l'onde comme un paratonnerre) |

**Règles communes.** Une altération ne prend que sur un coup qui touche vraiment : gardé, il ne
reste rien. Un second coup la **relance** jusqu'à son plafond, il ne l'empile pas. Le temps
arrêté suspend tout, y compris ce qui brûle. Un kit la pose avec `status` et `status_s`, sur un
coup ou sur un projectile (voir `docs/KITS.md`).

**Ce qui s'y branchera plus tard.** Les altérations ont été écrites génériques parce que la
suite du roster en vit :

| Perso | Stand | Altération attendue | Source |
| --- | --- | --- | --- |
| Avdol (partie 3) | Magician's Red | **burn** | JoJo Wiki : Stand de feu, manipule librement les flammes |
| Pet Shop (partie 3) | Horus | **chill** | JoJo Wiki : Stand de glace, stalactites et murs de glace |
| Akira Otoishi (partie 4) | Red Hot Chili Pepper | **shock** | JoJo Wiki : vit du courant électrique, circule dans les câbles |
| Ghiaccio (partie 5) | White Album | **chill** | à confirmer en ligne avant d'écrire le kit |
| Partie 8 | Speed King | chaud **et** froid | à confirmer en ligne avant d'écrire le kit |

Echoes Act 2 (le son écrit qui devient réel) et In a Silent Way (l'étouffement) ne rentrent dans
aucune des trois : ce sont des altérations à part, à décrire quand leur partie arrive, pas à
forcer dans une case existante.

## Interactions spéciales (fidèles à l'œuvre)

Ces règles passent avant les règles normales du combat. Elles se codent à part, dans un module « interactions », pour que chaque nouveau perso puisse s'y brancher.

| Situation | Règle en jeu |
| --- | --- |
| Time stop | Tout se fige sauf le lanceur. Les projectiles lancés s'arrêtent en l'air et repartent à la reprise. Écran en négatif, son coupé |
| Deux time stoppers lancent en même temps | Les deux bougent (ta règle). Time stoppers : Jotaro P3/P4/P6, DIO, Diego alternatif (The World) |
| Time stopper pris dans le time stop adverse | Il peut bouger 1 s au début, puis de plus en plus longtemps à chaque fois qu'il le subit dans le match (comme Jotaro qui « entre » peu à peu dans le temps arrêté de DIO) |
| Durée des time stops | DIO \~5 s, Diego alternatif \~5 s, Jotaro P3 \~3 s (monte à 5 s avec l'Ultime), Jotaro P4 \~2 s, Jotaro P6 \~1 s |
| Tusk Act 4 | Tir inbloquable qui ignore les invincibilités : King Crimson, Love Train, échanges de dimension de D4C, Return to Zero ne l'annulent pas. La blessure empêche toute régénération jusqu'à la fin du round |
| King Crimson (time erase) | Diavolo devient intangible et rapide ; l'adversaire continue l'action entamée en « pilote automatique » sans rien toucher. Impossible pendant un time stop (il est figé) |
| Gold Experience Requiem | Return to Zero : une fois par round, l'action qui allait toucher Giorno est annulée et l'attaquant revient à sa position de départ. Contre Diavolo : le time erase est annulé et Diavolo est stun |
| Love Train (D4C) | Les dégâts visés sur Valentine sont redirigés ailleurs (souvent vers l'attaquant). Actif avec les 3 parties du Corps Saint. Seuls Tusk Act 4, GER et Go Beyond passent à travers |
| Made in Heaven | Accélération du temps : Pucci bouge de plus en plus vite, l'adversaire non. Un time stop reste possible mais sa durée est divisée par deux |
| Wonder of U | Toute approche vers Toru avec intention de l'attaquer déclenche des calamités. Exception : la Go Beyond de Gappy (la bulle « qui n'existe pas ») passe |
| Hamon contre vampires et Pillar Men | Dégâts doublés, et le Hamon bloque leur régénération quelques secondes |
| The Hand | Peut effacer projectiles, pièges et bulles qu'il touche (sauf Act 4 et Go Beyond) |
| Visibilité des Stands | Les Stands sont visibles par tous les persos, y compris les utilisateurs de Hamon et de Rotation (sinon Jonathan contre Aerosmith serait injouable) |
| Stand rush contre Stand rush | Clash Ora/Muda/Dora/Ari : celui qui martelle le plus vite gagne |

## Roster — Partie 1 : Phantom Blood

Partie 1 = Hamon contre vampires : pas de Stands, tout se joue sur la jauge de Hamon et la jauge de sang.

| Perso | Style | Gameplay | Mécanique signature | Ultime (GHA) |
| --- | --- | --- | --- | --- |
| **Jonathan Joestar** | Hamon · Tank rushdown | Coups lourds et lents, grosse vie (1150). Hamon à courte portée | Rafale d'Overdrive (coup lourd) qui fait le duel contre les rafales de Stand (ORA, MUDA). Hamon dans son épée Luck & Pluck (HHA) pour plus de portée | Sunlight Yellow Overdrive : rafale de Hamon du soleil qui brûle les vampires |
| **Dio Brando** | Vampire · Bruiser | Agressif, vole de la vie sur les coups lourds | Gel vaporisant : le contact au corps à corps gèle l'adversaire (stun). Space Ripper Stingy Eyes : rayons oculaires pour zoner | Absorption : attrape et draine une grosse part de vie |
| **Will A. Zeppeli** | Hamon · Mobilité | Rapide, saute haut, très bon à mi-distance | Hamon à travers les liquides : lance du vin ou de l'eau qui transmet le Hamon (projectile tranchant). Peut marcher sur l'eau | Ondes de Hamon en rafale (Tornado Overdrive) |
| **Bruford** | Zombie chevalier · Contrôle | Portée moyenne, épée | Cheveux qui attrapent et percent : grab à distance qui draine | Danse des cheveux : zone de grabs multiples |
| **Tarkus** | Zombie · Grappler | Très lent, très résistant | Anneau de chaînes : enferme l'adversaire dans un ring de chaînes, lui et Tarkus ne peuvent plus sortir | Brise-nuque : grab massif |
| **Speedwagon** (bonus) | Sans pouvoir · Joke | Chapeau à lame (boomerang), coups de rue | Pose = cri d'encouragement : buff de soin léger | « Speedwagon se retire avec style » : esquive comique invincible |

## Roster — Partie 2 : Battle Tendency

Partie 2 = ruse et Pillar Men : les Joestar trichent, les Pillar Men ont chacun un « mode » élémentaire.

| Perso | Style | Gameplay | Mécanique signature | Ultime (GHA) |
| --- | --- | --- | --- | --- |
| **Joseph Joestar (jeune)** | Hamon · Trickster | Imprévisible, pièges partout | Clackers Hamon (projectile qui revient), grenades à retardement, fils de Hamon tendus au sol qui font trébucher. « Ta prochaine réplique sera… » : en Pose, il prédit la prochaine attaque adverse ; si c'est juste, contre gratuit | Un plan caché : explosion de tous les pièges posés |
| **Caesar Zeppeli** | Hamon · Zoner | Garde l'adversaire loin | Bubble Launcher (bulles à tête chercheuse), Bubble Cutter (bulles tranchantes en arc), Bubble Lens (bulle qui concentre la lumière en rayon) | Bubble Barrier : dôme de bulles qui explosent en chaîne |
| **Lisa Lisa** | Hamon · Contrôle | Élégante, contres | Écharpe Hamon : fouet à longue portée, peut se rigidifier en lance. Bonus de garde : parade Hamon qui renvoie | Piège de l'écharpe : immobilise et ensevelit de Hamon |
| **Rudol von Stroheim** | Cyborg · Artillerie | Lent, tanky, énorme puissance de feu | Mitrailleuse thoracique, canon UV (dégâts doublés sur Pillar Men et vampires), bras extensible | « La science allemande est la meilleure du monde ! » : tir laser UV continu |
| **Wamuu** | Pillar Man · Contrôle de zone | Grosse portée, repousse | Mode Vent : tornades stationnaires, Divine Sandstorm (rafale qui déchiquette en ligne). S'aveugle pour détecter par le vent : immunisé aux illusions | Divine Sandstorm portée maximale |
| **Esidisi** | Pillar Man · Ruse | Trompeur, dégâts de feu | Mode Chaleur : vaisseaux sanguins qui jaillissent et brûlent (fouets de sang bouillant). Peut « pleurer » (Pose) pour se calmer et se soigner un peu | Contrôle d'un corps : prend le contrôle de l'adversaire 2 s |
| **Kars** | Pillar Man · Stance switcher | Le boss de la partie | Posture Lames : lames lumineuses sur les bras (très agressif). Avec le masque et la pierre d'Aja : forme Ultime via Power Up, possible sous 50 % de vie (vol, plumes, tentacules, immunité au soleil) | Lumière Hamon de l'Ultime Lifeform : rayon de Hamon massif |
| **Straizo** | Vampire · Sniper | Rapide, à distance | Rayons oculaires sous pression (Space Ripper Stingy Eyes) très longue portée | Rafale d'yeux sur tout l'écran |
| **Santana** | Pillar Man · Infiltration | Rapide, insaisissable, fragile au soleil | Corps flexible : se glisse dans les murs, le sol ou par de petits trous. Au contact, entre dans le corps de l'adversaire et l'absorbe (dégâts sur la durée). Côtes qui jaillissent en lames de près | Fusion : entre entièrement dans l'adversaire et le ronge de l'intérieur |

## Roster — Partie 3 : Stardust Crusaders

Partie 3 = le cœur des Stands : c'est ici que se testent le Stand on/off et le time stop. Première vague de développement.

| Perso | Style | Gameplay | Mécanique signature | Ultime (GHA) |
| --- | --- | --- | --- | --- |
| **Jotaro Kujo** (Star Platinum) | Stand · Brawler burst | Très courte portée, dégâts et vitesse dévastateurs | Ora rush, Star Finger (doigt extensible à mi-distance). Time stop \~3 s en spéciale à longue recharge ; Power Up court : +1 s de time stop | Time stop prolongé + Ora Ora final |
| **DIO** (The World) | Stand · Hit & run | Couteaux à distance, frappe vite | Couteaux en éventail ; en time stop (\~5 s), les couteaux posés forment un piège autour de l'adversaire. Vol de sang sur grab | Road Roller : chute du rouleau compresseur en time stop |
| **Noriaki Kakyoin** (Hierophant Green) | Stand · Trapper | Mi-distance, préparation | Emerald Splash (salve d'émeraudes), fils invisibles posés dans l'arène (barrière de 20 mètres : touchée = rafale automatique), grappin sur les murs pour fuir | 20 Metre Radius Emerald Splash : tout l'écran devient piège |
| **Jean Pierre Polnareff** (Silver Chariot) | Stand · Glass cannon | Estocs ultra rapides, combos longs | Armor Off : sacrifie sa défense pour une vitesse monstrueuse et des images rémanentes (clones qui attaquent). Peut tirer la lame de la rapière (projectile, mais désarmé 2 s) | Rafale de clones Armor Off |
| **Muhammad Avdol** (Magician's Red) | Stand · Zoner feu | Mi-distance, contrôle de zone | Crossfire Hurricane (ankhs de feu), cordes de feu qui ligotent, détecteur de vie (révèle les persos invisibles) | Crossfire Hurricane Special : six ankhs à tête chercheuse |
| **Joseph Joestar (vieux)** (Hermit Purple + Hamon) | Stand + Hamon · Trickster | Grappin, Hamon dans les ronces | Ronces qui attrapent à distance et transmettent le Hamon. Vision : révèle la position de l'adversaire invisible | Hermit Purple + Overdrive : grab à travers l'arène |
| **Iggy** (The Fool) | Stand · Mobilité | Petit, dur à toucher | Ailes de sable (plane au-dessus des pièges), clones de sable leurres, mur de sable qui bloque les projectiles | Tempête de sable : brouillard qui cache Iggy |
| **Hol Horse** (Emperor) | Stand · Sniper mobile | Distance, dash | Balles guidées : la trajectoire suit le stick droit (ou la souris) pendant qu'il court. Pose = appelle J. Geil en renfort (assist ponctuel) | Rafale de 6 balles guidées |
| **Vanilla Ice** (Cream) | Stand · Assassin | Invisible, dégâts brutaux | Se cache dans la dimension de Cream : invisible et intouchable, mais aveugle ; il sort la tête pour voir (vulnérable). Tout ce qu'il traverse est effacé, décor compris | Balayage final : trace en ligne droite qui efface tout |
| **Mariah** (Bastet) | Stand · Piège | Fragile, dégâts sur la durée | Pose des prises électriques (Bastet) ; les toucher magnétise l'adversaire, qui attire ensuite tous les objets métalliques de l'arène | Magnétisme maximal : pluie de métal sur la cible |
| **N'Doul** (Geb) | Stand · Sniper aveugle | Très longue portée | Geb (eau) attaque à distance par le sol. Repère l'adversaire au bruit : s'arrêter de bouger rend invisible à ses attaques | Main d'eau géante qui jaillit sous la cible |
| **Pet Shop** (Horus) | Stand · Zoner glace | Vole, harcèle | Pics de glace, murs de glace, gèle le sol (glissant) | Pluie de stalactites |

## Roster — Partie 4 : Diamond is Unbreakable

Partie 4 = l'environnement : ces persos jouent avec le décor, donc les arènes doivent avoir des objets cassables et déplaçables.

| Perso | Style | Gameplay | Mécanique signature | Ultime (GHA) |
| --- | --- | --- | --- | --- |
| **Josuke Higashikata** (Crazy Diamond) | Stand · Brawler environnement | Frappe fort de près, Dora rush | Casse le décor en débris, puis les « répare » : ils volent vers leur point d'origine en écrasant ce qui est sur le trajet. Peut soigner… tout sauf lui-même. Cheveux insultés (Pose adverse proche) = mode rage | Fusion : répare l'adversaire dans un mur ou un objet |
| **Jotaro Kujo (P4)** (Star Platinum: The World) | Stand · Brawler | Plus posé, plus précis qu'en P3, couleurs de la Partie 4 | Time stop \~2 s. Lance des billes et des pièces d'une pichenette (projectiles). Star Finger plus long | Time stop + Ora final |
| **Okuyasu Nijimura** (The Hand) | Stand · Grappler spatial | Bourrin, coups lents | Efface l'espace : téléporte l'adversaire vers lui (ou lui vers un point). Efface les projectiles. Le coup qui efface fait de gros dégâts mais à long temps de récupération | Effacement en chaîne : aspire tout l'écran vers lui |
| **Koichi Hirose** (Echoes) | Stand · Switch d'Actes | 3 kits en un | Power Up débloque l'Acte suivant ; la touche Stand passe d'un Acte débloqué à l'autre. Act 1 : onomatopées collées qui harcèlent. Act 2 : pose des sons au sol (Boing = rebond, Sizzle = brûlure). Act 3 : 3 Freeze, alourdit l'adversaire à courte portée | Act 3 Freeze maximal : adversaire cloué au sol |
| **Rohan Kishibe** (Heaven's Door) | Stand · Debuffer | Faible au corps à corps | S'il touche avec son Stand, il « écrit » dans l'adversaire : désactive une touche au hasard 5 s, ou impose une règle (« ne peut pas avancer vers Rohan »). Peut aussi s'écrire lui-même pour se buffer | « Tu ne peux pas attaquer Rohan Kishibe » : 4 s sans attaque pour l'adversaire |
| **Yoshikage Kira** (Killer Queen) | Stand · Poseur de bombes | Prudent, contrôle | Transforme un objet de l'arène en bombe (une seule à la fois, au contact ou au déclencheur). Sheer Heart Attack : petit char indestructible qui traque la chaleur de l'adversaire. Stray Cat (option) : bulles d'air invisibles | Bites the Dust : enregistre l'état du combat ; 6 s plus tard tout revient en arrière, mais les explosions de Kira se répètent au même endroit (destin fixé) |
| **Yukako Yamagishi** (Love Deluxe) | Stand · Grappler cheveux | Longue portée, saisies | Cheveux qui attrapent, ligotent, ou la propulsent | Cocon de cheveux : ligote et étouffe |
| **Akira Otoishi** (Red Hot Chili Pepper) | Stand · Électrique | Rapide, se charge | Voyage dans les câbles et poteaux électriques de l'arène (téléportation). Se décharge avec le temps : doit se recharger aux prises | Surcharge : traverse l'écran en éclair |
| **Keicho Nijimura** (Bad Company) | Stand · Summoner armée | Distance, très fragile | Armée miniature : soldats, tanks, hélicos Apache qui tirent. Les petites unités peuvent être écrasées | Frappe aérienne : missiles sur toute une zone |
| **Shigekiyo Yangu** (Harvest) | Stand · Essaim | Très fragile, dur à contrer | 500 petits Harvest qui piquent (et peuvent injecter de l'alcool : contrôles inversés 2 s). Récupèrent les objets du sol | Nuée : l'essaim recouvre l'adversaire |
| **Mikitaka Hazekura** (Earth Wind and Fire) | Sans Stand visible · Joke métamorphe | Imite des objets | Se transforme en objet (dés, ballon, chaussure…) pour esquiver ou en arme. Très sensible au bruit (sirènes = stun) | Transformation en fusée |

## Roster — Partie 5 : Golden Wind

Partie 5 = Passione : chaque membre de la Squadra Esecuzioni est un « puzzle » à résoudre, très bon pour la variété.

| Perso | Style | Gameplay | Mécanique signature | Ultime (GHA) |
| --- | --- | --- | --- | --- |
| **Giorno Giovanna** (Gold Experience) | Stand · Summoner | Polyvalent | Donne vie aux objets : arbres qui bloquent les projectiles, grenouilles qui renvoient les dégâts, serpents qui mordent. Muda rush. Peut soigner en recréant des tissus (lent) | Rush Muda final ; via Power Up, la flèche le fait passer en **Gold Experience Requiem** jusqu'à la fin du round (Return to Zero, voir Interactions) |
| **Bruno Bucciarati** (Sticky Fingers) | Stand · Hit & run furtif | Pièges zippers | Fermetures éclair au sol ou sur les murs : s'enterre (invulnérable 2 s) et ressort ailleurs. Peut découper un membre adverse (désactive un type d'attaque 3 s). Arrivederci rush | Zipper Man : bras zippé à très longue portée + rush |
| **Guido Mista** (Sex Pistols) | Stand · Angles morts | 6 balles, recharge à gérer | Les 6 Pistols font rebondir les balles vers l'adversaire, même dans le dos. Il ne peut jamais avoir 4 balles : le chargeur saute de 3 à 5 (superstition, malus si on force) | Rafale Pistols : 6 balles redirigées en même temps |
| **Narancia Ghirga** (Aerosmith) | Stand · Drone | Pilote un avion | Aerosmith vole séparément et mitraille. Radar à CO2 : repère l'adversaire même caché ou invisible | Bombe d'Aerosmith : tapis de bombes |
| **Leone Abbacchio** (Moody Blues) | Stand · Replay | Stratégique | Enregistre les 5 dernières secondes de l'adversaire et les rejoue avec un clone fantôme : le clone refait ses coups et touche | Replay complet : clone de l'adversaire qui combat 6 s |
| **Pannacotta Fugo** (Purple Haze) | Stand · Zone de virus | Dangereux pour lui aussi | Capsules de virus : nuage mortel qui ronge la vie. Fugo y est sensible aussi (positionnement crucial). Le soleil tue le virus | Explosion des 6 capsules |
| **Trish Una** (Spice Girl) | Stand · Défensif | Rebond et contre | Ramollit ce qu'elle touche : sol en caoutchouc (rebondit), murs qui absorbent les coups, projectiles amortis | Wannabe : tout ramollir et renvoyer l'impact |
| **Diavolo** (King Crimson) | Stand · Counter absolu | Très dur à jouer | Epitaph : aperçu fantôme de la prochaine action adverse (0,5 s d'avance). Time erase : dash d'invincibilité totale (voir Interactions). Bascule Doppio (Pose) : forme faible mais Epitaph permanent | Time erase prolongé + coup au cœur |
| **Prosciutto & Pesci** (Grateful Dead + Beach Boy) | Duo · Contrôle | Deux persos en un | Prosciutto : gaz qui vieillit (ralentit l'adversaire ; la glace et le froid l'annulent). Pesci : canne à pêche qui traverse les murs et ferre de loin | Vieillissement accéléré de toute l'arène |
| **Ghiaccio** (White Album) | Stand · Tank glace | Armure, patins | Patine sur la glace qu'il crée (très rapide). Armure de glace : réduit les dégâts. White Album Gently Weeps : gèle l'air et renvoie les projectiles | Gel total de l'arène |
| **Risotto Nero** (Metallica) | Stand · Assassin fer | Distance moyenne, invisible | Fabrique des lames et rasoirs à partir du fer du sang adverse (dégâts sur la durée). Invisible en se fondant dans le décor métallique | Ciseaux et clous en masse |
| **Cioccolata** (Green Day) | Stand · Zone verticale | Contrôle du terrain | La moisissure ronge quiconque descend : les zones en contrebas de l'arène (escaliers, fosses, cratères) deviennent des zones de dégâts | Moisissure généralisée |
| **Polpo** (Black Sabbath) | Stand · Contrôle à distance | Énorme, presque immobile, tank | Black Sabbath se déplace dans les ombres de l'arène (mode contrôle). Toucher l'ombre de l'adversaire = coup de flèche. Les zones de lumière sont sûres pour l'adversaire | Tombée de la nuit : toute l'arène devient ombre quelques secondes |

## Roster — Partie 6 : Stone Ocean

Partie 6 = Stands étranges et évolution : Pucci est le seul perso qui change de Stand pendant le combat.

| Perso | Style | Gameplay | Mécanique signature | Ultime (GHA) |
| --- | --- | --- | --- | --- |
| **Jolyne Cujoh** (Stone Free) | Stand · Mid-range araignée | Fils partout | Se défait en fil : attrape de loin, se propulse d'un mur à l'autre, tisse des toiles ralentissantes, fil-détecteur. Ora rush | Möbius : boucle de fil qui renvoie l'attaque adverse sur elle-même |
| **Jotaro Kujo (P6)** (Star Platinum) | Stand · Brawler | Skin de Jotaro P4 probable (même kit), à confirmer | Time stop \~1 s seulement, mais récupération rapide | Time stop + coup unique à bout portant |
| **Ermes Costello** (Kiss) | Stand · Duplication | Combos par autocollants | Colle un autocollant sur un objet ou sur l'adversaire : il se dédouble. Arracher l'autocollant recolle les deux moitiés violemment (gros dégâts) | Autocollant sur l'adversaire puis arrachage |
| **F.F.** (Foo Fighters) | Stand · Plancton | Distance, régénération | Tire du plancton comme des balles. Boit l'eau de l'arène pour se soigner ; sèche si elle n'en trouve pas | Forme d'eau : se reforme après un coup fatal (une fois) |
| **Weather Report** | Stand · AoE météo | Contrôle de la carte | Nuages, foudre aléatoire, pluie de grenouilles empoisonnées, coussins d'air protecteurs, couche d'oxygène qui ralentit | Heavy Weather : arc-en-ciel subliminal qui transforme en escargots (adversaire très lent 5 s) |
| **Narciso Anasui** (Diver Down) | Stand · Tank piège | Contre et pièges | Plonge son Stand dans le sol ou un objet pour y stocker une attaque ; elle explose quand l'adversaire passe. Peut plonger dans l'adversaire pour déformer son corps. En 2v2 : protège un allié | Diver Down dans l'adversaire : coup interne massif |
| **Emporio Alnino** (Burning Down the House) | Stand · Fantômes d'objets | Faible, malin | Fait apparaître des objets fantômes (balle de baseball, radio…). Peut emprunter un disque de Stand une fois par round | Disque Weather Report : oxygène toxique |
| **Enrico Pucci** (Whitesnake → C-Moon → Made in Heaven) | Stand · Évolution | Faible au début, monstre à la fin | Phase 1 Whitesnake : vole un disque (supprime une spéciale adverse 8 s), illusions. Phase 2 C-Moon (Power Up des 14 mots) : inversion de gravité, coups qui retournent l'adversaire. Phase 3 Made in Heaven (Power Up) : accélération du temps | Selon la phase : vol de deux disques d'un coup, gravité inversée sur toute l'arène, ou frappe à vitesse infinie |
| **Johngalli A.** (Manhattan Transfer) | Stand · Sniper | Ne bouge presque pas | Drone relais qui redévie ses tirs de sniper sous tous les angles ; ressent les courants d'air (détecte les mouvements) | Tir parfait à travers tout l'écran |
| **Rikiel** (Sky High) | Stand · Débuff | Distance | Lâche des Rods (créatures volantes) qui volent la chaleur de l'adversaire : il est ralenti et prend des dégâts sur la durée | Nuée de Rods |
| **Donatello Versus** (Under World) | Stand · Replay de terrain | Contrôle | Fait « remonter » un événement passé du sol (un accident, une chute d'avion) qui frappe l'adversaire | Le crash de l'avion rejoué sur l'arène |

## Roster — Partie 7 : Steel Ball Run

Partie 7 = la Rotation et les chevaux : seule partie où certains persos peuvent monter à cheval dans l'arène.

| Perso | Style | Gameplay | Mécanique signature | Ultime (GHA) |
| --- | --- | --- | --- | --- |
| **Johnny Joestar** (Tusk) | Rotation · Artilleur à évolution | Lent au sol (rampe), rapide à cheval | Tire ses ongles en rotation. Chaque touche remplit la jauge d'Éveil ; Power Up fait monter l'Acte : Act 1 (ongles), Act 2 (trou qui poursuit l'adversaire), Act 3 (se tire dans le trou pour se téléporter), Act 4 | **Tusk Act 4** : rotation infinie, inbloquable (voir Interactions) |
| **Gyro Zeppeli** (Steel Balls) | Rotation · Zoner géométrique | Courir pour charger | Deux boules d'acier en boomerang, trajectoires courbes. Les boules qui touchent font des spasmes (contrôles perturbés). Courir ou galoper charge l'énergie. Avec une partie du Corps Saint : Scan | **Ball Breaker** : boule géante en Rotation Dorée |
| **Diego Brando** (Scary Monsters) | Transformation · Rushdown bête | Ultra agressif | Se transforme en raptor : vitesse, portée de morsure, vision du mouvement. Transforme les rochers ou animaux de l'arène en petits dinosaures kamikazes. Une morsure infecte : l'adversaire commence à devenir dinosaure (débuff) | Charge de raptor avec la meute |
| **Diego alternatif** (THE WORLD) | Stand · Time stopper | Couteaux et coups | Time stop \~5 s, couteaux en arc. Peut combattre en time stop contre DIO et Jotaro (règle des deux time stoppers) | Panneaux routiers en time stop (clin d'œil au Road Roller) |
| **Funny Valentine** (D4C) | Stand · Clonage | Stratège | Coincé entre deux objets (ou drapeau + mur), il passe dans une autre dimension et revient avec un clone en pleine forme. Invoque des doubles qui attaquent | **Love Train** : s'active avec les 3 parties du Corps Saint (voir Objets de l'arène) |
| **Hot Pants** (Cream Starter) | Stand · Soin et aveuglement | Support solo | Spray de chair : se soigne, bouche les yeux adverses (écran voilé), déguise | Spray massif : adversaire aveuglé et ralenti |
| **Sandman** (In a Silent Way) | Stand · Coureur piège | Très rapide à pied | Transforme ses sons en objets : les onomatopées qu'il pose coupent ou brûlent quand on les touche. Court presque aussi vite qu'un cheval | Mur de sons tranchants |
| **Ringo Roadagain** (Mandom) | Stand · Duel | Pistolet, rythme lent | Rembobine le temps de 6 s (une fois par round) : tout le monde revient en arrière, mais Ringo garde la mémoire et ses positions de tir | Duel : un tir à la seconde exacte, dégâts énormes si bien chronométré |
| **Blackmore** (Catch the Rainbow) | Stand · Pluie | Ne marche que sous la pluie | Fige les gouttes de pluie : marche dessus, les transforme en lames, se décompose en pluie pour esquiver. Sans pluie il est faible | Pluie de lames |
| **Mountain Tim** (Oh! Lonesome Me) | Stand · Lasso | Mid-range, cowboy | Lasso qui l'emmène le long de la corde, se décompose en morceaux sur la corde pour esquiver | Revolver et lasso en combo |
| **Wekapipo** (Rotation imparfaite) | Rotation · Bruiser | Boules à éclats | Boules de démolition qui se fragmentent en satellites ; le côté gauche de l'adversaire touché disparaît (contrôles gauche coupés 3 s) | Grappe de satellites |

## Roster — Partie 8 : JoJolion

Partie 8 = vol, débuffs et chaos : tes persos prioritaires sont ici (Rai, Karera, Yasuho, Mitsuba, Doctor Wu, Kira, Josefumi), marqués ★.

| Perso | Style | Gameplay | Mécanique signature | Ultime (GHA) |
| --- | --- | --- | --- | --- |
| **Josuke « Gappy »** (Soft & Wet) | Stand · Plunderer | Bulles et vol | Une bulle qui éclate sur l'adversaire vole quelque chose quelques secondes : vitesse, friction (il glisse), vue (écran flou), eau (soif = dégâts). Peut voler l'équilibre | **Go Beyond** : débloqué par Power Up ; la GHA tire une bulle en rotation infinie qui « n'existe pas » ; traverse tout, y compris Wonder of U |
| ★ **Josefumi Kujo** (Soft & Wet) | Stand · Plunderer agile | Plus mobile que Gappy, plus fragile | Mêmes bulles voleuses que Gappy (sans Go Beyond). Vole le son (adversaire sans effets sonores ni indicateurs audio) ou la lumière (zone sombre). Bulles qui portent Josefumi pour se déplacer | Vol de vision : l'adversaire ne voit plus Josefumi 4 s |
| ★ **Yoshikage Kira (JJL)** (Killer Queen) | Stand + Rotation · Bombardier | Distance, précis | Bulles explosives à rotation : elles suivent une trajectoire qu'il contrôle et explosent au contact. Maîtrise de la Rotation : bulles plus rapides que la moyenne | Barrage de bulles en spirale |
| ★ **Yasuho Hirose** (Paisley Park) | Stand · Navigatrice | Faible en dégâts, maîtresse du terrain | Paisley Park entre dans les écrans, panneaux et téléphones de l'arène (téléportation d'appareil en appareil). Trace « le bon chemin » : une ligne au sol vers l'angle mort de l'adversaire, suivre la ligne donne un bonus de vitesse et un coup critique | Guidance : pendant 6 s, toutes les attaques de Yasuho prennent le chemin parfait et ne ratent pas |
| ★ **Karera Sakunami** (Love Love Deluxe) | Stand · Arnaqueuse piège | Distance, ruse | Fait pousser des cheveux partout où l'adversaire a touché (sol, murs, objets) : les cheveux le ralentissent et l'agrippent. Corde de cheveux tendue vers l'adversaire, qu'elle enflamme au briquet (mèche de feu). Portée limitée (80 m dans l'œuvre = rayon max dans l'arène) | Mèche géante : tous les cheveux posés prennent feu en chaîne |
| ★ **Mitsuba Higashikata** (Awaking III Leaves) | Stand · Vecteurs | Contrôle de trajectoires | Pose des flèches : tout ce qui les touche part dans la direction indiquée (projectiles déviés, adversaire projeté contre un mur, ou elle-même propulsée). Plusieurs flèches s'additionnent (vecteurs) | Trois Feuilles : 3 flèches qui expulsent tout de la zone par le chemin le plus court (repousse et annule les projectiles) |
| ★ **Doctor Wu** (Wu Tomoki) | Stand · Poussière parasite | Insaisissable | Se décompose en gravier : immunisé aux coups physiques mais lent, et vulnérable au vent, à l'eau et aux vecteurs. Poussière allergène (dégâts sur la durée), poussière de somnifère (ralentit) | Possession : entre dans l'adversaire et le contrôle 2 s, en lui faisant même utiliser une de ses spéciales |
| ★ **Rai Mamezuku** (Doggy Style) | Stand · Câbles | Mid-range technique | « Épluche » son corps en fil : fouet tranchant longue portée, bras-arbalète qui tire des objets, doigt-pique. Se déroule totalement pour feindre la mort (invulnérable, puis contre). Initié à la Rotation : fil en spin plus coupant | Arbalète de fil en Rotation : tir perçant |
| **Norisuke Higashikata IV** (King Nothing) | Stand · Traqueur | Support solo | Puzzle qui suit l'odeur : marque l'adversaire, révèle sa position, poursuit et s'assemble autour de lui | Puzzle complet : piège l'adversaire |
| **Joshu Higashikata** (Nut King Call) | Stand · Démontage | Corps à corps | Pose des écrous sur l'adversaire ou les objets ; les dévisser détache la partie (bras = pas d'attaque, jambe = lent) | Démontage complet 3 s |
| **Tsurugi Higashikata** (Paper Moon King) | Stand · Illusion | Origami | Grenouilles en origami à distance. Le contact déclenche la confusion des visages : l'adversaire ne voit plus quel perso est Tsurugi parmi des leurres | Pluie d'origamis |
| **Daiya Higashikata** (California King Bed) | Stand · Règle | Piège mental | Impose une règle (« ne touche pas cette zone »). Si l'adversaire la brise, elle lui vole un souvenir : une de ses spéciales disparaît jusqu'à la fin du round | Vol de souvenir instantané |
| **Hato Higashikata** (Walking Heart) | Stand · Talons | Mobilité murale | Talons extensibles : marche sur les murs, perfore à distance | Talons géants depuis le plafond |
| **Jobin Higashikata** (Speed King) | Stand · DoT chaleur | Faible, puis mortel | Stocke de la chaleur dans l'adversaire ou les objets : plus le combat dure, plus la vie fond | Relâche toute la chaleur d'un coup |
| **Toru** (Wonder of U) | Stand · Anti-rushdown | Jouable mais atypique | Son Stand marche lentement vers l'adversaire. Toute approche vers Toru déclenche des calamités (débris, panneaux, pluie mortelle). Le but de l'adversaire est de survivre et de frapper sans « intention » | Calamité totale |
| **Dolomite** (Blue Hawaii) | Stand · Zombies | Distance | Tout ce qui est touché par son liquide (y compris l'adversaire) avance vers une cible choisie, quoi qu'il arrive : il pousse l'adversaire dans des pièges | Contrôle total 3 s |
| **Tamaki Damo** (Vitamin C) | Stand · Ramollissement | Piège | Ses empreintes digitales ramollissent quiconque les touche (adversaire qui s'étale, lent, sans défense) | Empreintes partout |
| **Yotsuyu Yagiyama** (I Am a Rock) | Stand · Aimant à objets | Distance | Marque l'adversaire : tous les objets d'un type (pierres, insectes) se ruent sur lui | Avalanche |
| **Aisho Dainenjiyama** (Doobie Wah!) | Stand · Tornade | Contrôle | Tornade qui suit la respiration de l'adversaire : l'adversaire doit « retenir son souffle » (rester immobile) pour qu'elle se perde | Tornade géante |

## Roster — Partie 9 : The JOJOLands

Partie 9 = le heist : la partie est toujours en cours de publication, donc ces kits seront mis à jour quand le manga révèle de nouvelles capacités.

| Perso | Style | Gameplay | Mécanique signature | Ultime (GHA) |
| --- | --- | --- | --- | --- |
| **Jodio Joestar** (November Rain) | Stand · Area denial | Contrôle de zone | Pluie lourde sur une zone choisie : écrase et ralentit l'adversaire, détruit les projectiles qui la traversent. Gouttes ciblées en tir rapide | Déluge : pluie écrasante sur la moitié de l'arène |
| **Dragona Joestar** (Smooth Operators) | Stand · Déplacement | Ruse, faible attaque | Quatre petits robots qui déplacent n'importe quoi le long d'une surface : glisser un mur, un objet, ou même les yeux de l'adversaire (écran décalé 2 s). Peut transférer une blessure qu'il reçoit sur un objet de l'arène, qui se brise (annule un coup) | Déplacement total : fait glisser l'adversaire à travers l'arène jusque dans un piège |
| **Paco Laburantes** (The Hustle) | Stand · Grappler vicieux | Mains nues | Muscles déformables : attrape sous n'importe quel angle, bloque les projectiles en contractant ses muscles (les balles restent coincées), vole de l'énergie (HH) en plein combo | Prise de muscles : étreinte qui broie |
| **Usagi Alohaoe** (THE MATTEKUDASAI) | Stand · Wildcard | Imprévisible | Son Stand se transforme en l'objet qu'un autre désire, jamais Usagi lui-même. En jeu : la touche Stand propose 3 objets tirés au hasard (filet, caméra leurre, câble d'acier…) et le joueur en choisit un. En 2v2, c'est l'allié qui choisit | Le vœu parfait : choix parmi 5 objets plus puissants |
| **Charming Man** (Big Mouth Strikes Again) | Stand · Camouflage | Assassin au couteau | Peau de sable : se fond dans le décor (invisible, mais le sable qui flotte le trahit), se déguise en l'adversaire, détache un œil pour voir à distance, fausse la perception de la profondeur | Illusion : 3 leurres de sable et un vrai coup de couteau |
| **Rohan Kishibe (P9)** (Heaven's Door) | Stand · Debuffer | Skin de Rohan P4 (même kit) | Mêmes bases que Rohan P4, plus rapide. Peut écrire des ordres plus longs mais doit lire l'adversaire avant (contact prolongé) | Ordre absolu |
| **Hacca Howler** (Eclipse Eight) | Stand · Boss mystère | Contrôle de brume | Brume visible seulement des Stand users : les objets qui y tombent foncent sur l'adversaire, Howler s'y téléporte. Capacité encore floue dans le manga : kit à compléter | À définir quand le manga l'expliquera |

Autres persos de la Partie 9 envisageables plus tard : Meryl Mei Qi (sans Stand connu), Lulu (Bags' Groove), Wild Cat Size (Cat Size), Bobby Jean (Glory Days).

## Arènes

Une ou deux arènes par partie, toutes en vue de dessus avec un sol terne et peu contrasté (règle de la référence Pokémon Arena). Chaque arène a au moins un élément interactif qui sert un perso précis.

| Arène | Partie | Sol et ambiance | Éléments interactifs | Avantage pour |
| --- | --- | --- | --- | --- |
| Manoir Joestar en flammes | 1 | Parquet, tapis, nuit | Lustres qui tombent, zones de feu, fenêtres qui laissent passer l'aube en fin de timer | Hamon (le soleil arrive) |
| Ruines de Windknight's Lot | 1 | Pavés, brume | Tombes, statues cassables, flaques (Hamon à travers l'eau) | Zeppeli, zombies |
| Château des Alpes suisses | 2 | Sable et pierre | Piliers cassables, cycle jour/nuit pendant le round | Pillar Men la nuit, Hamon le jour |
| Air Supplena Island | 2 | Dalles, eau autour | Bassins d'huile (Hamon conducteur), murs étroits | Lisa Lisa, Caesar |
| Le Caire, rue de nuit | 3 | Pavés, marché | Étals cassables (couteaux de DIO plantés), Road Roller garé, toits | DIO, Jotaro |
| Manoir de DIO | 3 | Couloirs sombres | Rideaux (soleil si on les arrache), escaliers, illusions de couloirs | Vanilla Ice, Hamon |
| Désert égyptien | 3 | Sable | Dunes, mirages, eau rare | N'Doul, Iggy |
| Morioh, quartier résidentiel | 4 | Bitume, trottoirs | Poteaux électriques (Red Hot Chili Pepper), poubelles et voitures à casser, objets à réparer | Josuke, Kira, Akira |
| Maison Kira | 4 | Tatamis, jardin | Plantes (Stray Cat), chat, objets-bombes | Kira |
| Naples, toits et port | 5 | Tuiles, quais | Bateaux, cordes à linge, zones de soleil (tue le virus de Fugo) | Bucciarati, Mista |
| Le Colisée de Rome (final P5) | 5 | Pierre antique | Flèche au centre (premier à la toucher passe en Requiem) | Giorno, Polnareff |
| Green Dolphin Street Prison | 6 | Béton, grillages | Grilles, égouts (eau pour F.F.), mur de la cour | Jolyne, F.F. |
| Cap Canaveral | 6 | Asphalte, ciel | Gravité qui s'inverse en phase C-Moon, temps qui accélère en Made in Heaven | Pucci |
| Désert de la course SBR | 7 | Terre craquelée | Rochers (dinosaures de Diego), pluie possible (Blackmore), chevaux en liberté | Gyro, Johnny, Diego |
| Maison Blanche, Philadelphie | 7 | Marbre | Drapeaux et fenêtres (deux objets pour D4C), lignes de rails dans le décor | Valentine |
| Wall Eyes de Morioh | 8 | Roche volcanique | Fissures, Locacaca (fruit qui soigne mais échange un organe), éboulements | Gappy, Josefumi |
| Hôpital universitaire TG | 8 | Carrelage blanc | Écrans et téléphones (Paisley Park), ascenseurs, tuyaux d'eau | Yasuho, Toru, Doctor Wu |
| Verger Higashikata | 8 | Herbe, arbres fruitiers | Arbres, outils de jardin, escalier de la maison | Famille Higashikata, Rai |
| Hawaï, villa de Rohan | 9 | Pelouse, piscine | Piscine, caméras de sécurité (Usagi), coffre-fort | Jodio, Usagi |
| Mégayacht de Howler | 9 | Pont en bois | Brume, embruns, bastingage | Howler, Charming Man |

Toutes les arènes partagent le même cadre : rectangle fermé, coins arrondis, marquages au sol discrets. On commence par une arène simple (la rue du Caire) pour le prototype.

## Priorités de développement

On code par vagues : chaque vague ajoute un nouveau type de mécanique au moteur, pour que les persos suivants deviennent rapides à faire. L'ordre exact des persos reste à ton choix.

1. **Vague 0 — Moteur** : déplacement, collisions, arène du Caire, vie, rounds, garde, esquive, jauge HH, placeholders géométriques, export .exe.
2. **Vague 1 — Stands de base** : Jotaro P3, DIO, Kakyoin, Polnareff. Débloque le Stand on/off, les projectiles, les pièges et le time stop (avec la règle des deux time stoppers).
3. **Vague 2 — Tes prioritaires de JoJolion** : Kira (JJL), Josefumi, Rai, Karera, Yasuho, Mitsuba, Doctor Wu. Débloque les bulles voleuses, les vecteurs, la possession, la téléportation par écrans.
4. **Vague 3 — Hamon** : Jonathan, Dio P1, Zeppeli, Joseph, Caesar. Débloque la jauge de Hamon, le soleil et la jauge de sang.
5. **Vague 4 — Icônes** : Josuke, Kira P4, Giorno, Diavolo, Jolyne, Pucci, Johnny, Gyro, Valentine, Gappy, Toru. Débloque les interactions spéciales (Requiem, Act 4, Love Train, Made in Heaven, Wonder of U).
6. **Vague 5 et plus** : le reste du roster, partie par partie, plus les arènes manquantes.

Un perso est « fini » quand il a : son kit codé et testé contre 3 autres persos, ses sprites (ou placeholders), ses sons, et sa fiche dans ce document mise à jour.

## Décisions prises

- Modes au lancement : Arcade, contre l'IA, J1 contre J2 en local. Mode Histoire plus tard.
- Chariot Requiem : oui, via la Flèche.
- Toru et Pucci (jusqu'à Made in Heaven) : jouables, à bien équilibrer.
- Stands visibles par tous les persos.
- Chevaux disponibles dans toutes les arènes.
- GER et Chariot Requiem passent par la Flèche ; Love Train, Scan et Tusk Act 2 par le Corps Saint.
- Versions : Jotaro P3 et P4 séparés (kits et couleurs différents), Jotaro P6 probablement en skin de P4, Rohan P9 en skin de Rohan P4. Joseph P2 et P3 séparés, Dio P1 et DIO P3 séparés.
- Persos bonus gardés : Speedwagon, Prosciutto & Pesci, Mikitaka.
- Éveils : une fois par match maximum, acquis jusqu'à la fin du match.
- Jotaro P3 : Power Up court qui allonge son time stop de 1 s.
- Sprites : persos d'environ 44 à 48 px de haut selon leur morphologie, dans des cases de 64 × 64, style A (contour noir, ombrage 2-3 tons, highlight). Résolution interne 480 × 270.
- Apparence des persos : générée à partir d'une fiche de données (morphologie, palette, pièces de costume) par `tools/make_sprites.py`, pour que toutes les animations restent cohérentes. Une planche dessinée à la main peut toujours la remplacer.
- Orientations des sprites : déplacement en 8 directions, mais 3 orientations dessinées par animation (bas, haut, droite) ; la gauche est le miroir de la droite. Le perso regarde où il marche ; attaques, garde et projectiles s'orientent vers l'adversaire.
- Égalité (double KO, ou timer à zéro avec le même % de vie) : les deux marquent le round. Si ça fait gagner les deux, **mort subite** façon Smash Bros : les deux à 1 PV, sans timer, le premier coup qui passe gagne.
- Vague 0 : inclut aussi le Flash Cancel, la Pose et la Résolution.
- Touches liées par position physique (ZQSD en AZERTY = WASD en QWERTY). Preset « deux joueurs sur un clavier » : J1 sur ZQSD + F G H R T Y C V B, J2 sur les flèches + pavé numérique. Tout reste rebindable.
- Prototype : l'arène tient entière dans l'écran, pas de caméra qui défile.
- Spéciale + une direction tenue = la variante de la spéciale (ex. Star Finger, couteaux en éventail, fils de Kakyoin, Armor Off).
- Touche Heart Heat seule : HHA (1 barre). Direction + Heart Heat : GHA (2 barres), ou la HHA s'il n'y a qu'une barre. (Avant : GHA dès 2 barres, ce qui rendait la HHA impossible avec une jauge pleine.)
- Kits Vague 1, Stand sorti : coup lourd = rafale (Ora, Muda, Hora) ; spéciale neutre = arrêt du temps pour Jotaro (3 s, recharge 20 s) et DIO (5 s, recharge 25 s).
- Temps arrêté : les coups reçus infligent leurs dégâts tout de suite, l'impact (recul, stun) arrive à la reprise ; un perso figé en garde reste en garde ; le timer du round s'arrête.
- Stand sorti : il a un corps qui peut être touché (derrière son manieur, devant lui quand il frappe) ; un coup sur le Stand blesse le manieur.
- Le Power Up de Jotaro (+1 s de time stop) attend la jauge d'Éveil (pas encore codée).
- Menu principal du prototype : Entraînement et Combat local jouables ; Histoire, Arcade, Contre l'IA et En ligne affichés « Bientôt ».
- Duel de rafales : l'écran quitte l'arène pour un face-à-face. Chaque moitié prend la couleur du perso et de son Stand (Jotaro violet, DIO jaune, Polnareff gris), les cris (ORA, MUDA…) fusent en arrière-plan. Une rafale qui touche un perso en train de lancer la sienne déclenche le duel, même un peu à contretemps. Polnareff fait ses rafales à l'épée seule (estocs) et crie aussi ORA.
- Enchaînements : la même touche, appuyée quand le coup touche, donne le coup suivant (léger, léger, léger : trois coups différents). Les longs combos font moins mal : à partir du 3e coup, −12 % par coup, jusqu'à 45 % (une rafale compte pour un coup). Les coups portés en temps arrêté font 80 % des dégâts, sauf les ultimes.
- Nouvelles mécaniques de coups, pour tous les kits : contre, bond (vers l'adversaire ou vers le point visé), coups blindés, casse-garde, coups qui attirent, Stand qui surgit le temps d'un coup.
- Visée libre : la souris pour le joueur au clavier (si elle a bougé dans les 3 dernières secondes), le stick droit à la manette ; sinon la direction tenue.
- Kits Vague 1, sans Stand, chaque perso a son identité :
  - Jotaro : direct, crochet, uppercut ; coup de tête casse-garde ; charge d'épaule blindée ; « Yare yare daze » (contre : Star Platinum surgit et frappe).
  - DIO : griffe, griffe croisée, coup de pied vampire ; saisie qui draine (plus lente : punie si elle rate) ; couteaux ; bond de vampire.
  - Kakyoin : coup de pied, pied retourné ; balayage circulaire ; émeraudes à tête chercheuse ; grappin vers le point visé.
  - Polnareff : savate, chassé, fouetté ; coup de pied sauté ; éclair de Chariot (estoc lointain) ; fierté (+20 % de dégâts 5 s).
- Avec le Stand : chaînes de trois coups (ORA, ORA ORA, ORAAA ; MUDA… ; estoc, taille, triple estoc), tentacule de Hierophant qui ramène l'adversaire.
- Ultimes (GHA) : un premier coup doit toucher (pas en garde) ; alors le combat se fige pour une cinématique avec caméra (zoom, travelling, bandes noires), puis le coup final tombe, imparable. Raté : rien de plus, les 2 barres sont perdues. Kakyoin fait exception : sa cinématique part tout de suite, puis ses fils couvrent l'arène 10 s.
- Road Roller : coup de The World, ZA WARUDO, DIO s'envole hors champ, revient avec le rouleau compresseur, l'écrase, martèle de MUDA, le temps reprend, explosion.
- Mode contrôle (Kakyoin) : maintenir Stand 0,5 s, HG va jusqu'à 150 px de Kakyoin ; fouet, Emerald Splash et fils depuis HG ; possession (coup lourd, imparable) : on dirige la marche de l'adversaire 1,5 s. Kakyoin ou HG touché : HG revient, Kakyoin sonné 0,8 s.
- Objets : Pose près d'une caisse ou d'une jarre : c'est le Stand qui la prend, même rangé, et la tient pendant que son manieur se bat normalement ; Pose de nouveau : le Stand la lance sur l'adversaire. La force du Stand (`strength` dans le kit) règle la vitesse, les dégâts et le recul : Star Platinum et The World (1,8) lancent ultra vite et fort, avec rebond contre les murs ; Silver Chariot 1,1 ; Hierophant Green 0,8. Touché, on la lâche. Cassée, elle revient à sa place (caisse 10 s, jarre 8 s).
- Gameplay nerveux : marche et dash plus rapides ; un coup qui touche peut s'annuler en dash ou en HHA/GHA (super cancel) ; direction + coup lourd = attaque en mouvement propre à chaque perso. Impact frames (2 images noir et blanc façon anime) puis coup de zoom sur les gros coups, contres, Guard Break et K.O.
- HHA de Kakyoin : les tentacules frappent d'en haut ; s'ils touchent, Hierophant entre par la bouche de l'adversaire et le détruit de l'intérieur (comme contre Death 13 et dans ASBR).
- Hamon (Vague 3) : jauge de 100, chaque round commence à 40 ; respirer (maintenir la touche Stand) recharge 25 par seconde, immobile. Un coup marqué Hamon dépense 15 à 30 points s'il y en a assez, et frappe 1,4 fois plus fort (certains, comme l'onde traversante de Jonathan, passent alors la garde) ; sinon il reste normal. Le Hamon fait double dégâts aux natures « vampire » et « Pillar Man » : DIO P3 compris.
- Jonathan : coup lourd = rafale d'Overdrive (duel contre ORA ORA, MUDA MUDA, HORA HORA) ; spéciale = Scarlet Overdrive ; spéciale + direction = onde traversante (la leçon de la grenouille) ; HHA = Luck & Pluck (estoc de Hamon à longue portée) ; GHA = Sunlight Yellow Overdrive en cinématique.
- Zeppeli : Zoom Punch, Hamon Cutter (jets de vin tranchants), bond du gentleman vers le point visé ; HHA = éventail de Hamon Cutters ; GHA = Tornado Overdrive en cinématique.
- Vampires (validé le 16/10/2026) : jauge de sang de 100, chaque round commence à 30. Elle se remplit en drainant (1 point par PV drainé) ; intact 1,5 s, le vampire cicatrise (14 PV par seconde, 0,5 sang par PV). La touche Stand passe en « gel vaporisant » (il faut 10 de sang, il en brûle 6 par seconde, retour à la normale à sec) : ses coups gèlent l'adversaire sur place. Les yeux laser (Space Ripper Stingy Eyes) coûtent 20 de sang. Un coup de Hamon bloque la cicatrisation 3 s. Les zombies prennent aussi double dégâts du Hamon.
- Soleil : certaines arènes ont des fenêtres ; à partir d'un moment du round (manoir Joestar : 60 s), le soleil entre. Un mort-vivant (vampire, zombie, Pillar Man) dans la lumière perd 25 de sang par seconde, puis 30 PV par seconde ; la respiration Hamon y est 1,5 fois plus rapide. DIO P3 brûle aussi.
- Aube (16/10/2026, correction) : le soleil **s'étale**. À l'aube, les rais tombent juste sous les fenêtres ; en 22 s ils s'allongent jusqu'au mur du fond et s'élargissent, jusqu'à ne laisser que des bandes d'ombre entre eux. Et la brûlure **monte** : un mort-vivant qui reste dans la lumière brûle jusqu'à 3,5 fois plus vite au bout de 5 s ; sortir de la lumière fait redescendre ce compteur (3 points par image). Avant, un vampire pouvait rester 30 s en plein soleil sans mourir : l'aube ne voulait rien dire. Maintenant elle décide du round, et le mort-vivant doit bouger.
- Speedwagon (16/10/2026) : il n'a pas de pouvoir, il a des amis. La touche Stand fait défiler trois postures (nouveau style `stance_cycle`) : Speedwagon seul, puis **Tattoo** et ses couteaux lancés, puis **Amato** le kempoïste. Aucun des deux n'est meilleur : Tattoo échange la puissance au corps à corps contre la portée, Amato échange la portée contre les plus gros coups du kit et une posture de contre. Le changement coûte 12 images.
- Jonathan (16/10/2026) : Luck & Pluck devient une **rafale de six estocs** de Hamon (le dernier projette) au lieu d'un estoc unique ; Scarlet Overdrive frappe le sol et envoie une **onde de Hamon** qui traverse l'arène, pour qu'il menace sans bouger.
- Bruford (16/10/2026) : ses cheveux ne servent plus seulement aux coups spéciaux. L'épée ne part jamais seule (nouvel effet `blade_hair`), et le deuxième coup de son enchaînement est un fouet de mèches qui porte plus loin que la lame.
- Dio Brando (P1) : griffe, doigts perçants, WRYYY ; doigts vampires (coup lourd qui vole beaucoup de vie) ; charge blindée ; yeux laser (spéciale) ; bond de vampire ; en gel vaporisant : toucher gelant, griffe de givre, étreinte gelée imparable. HHA = Space Ripper Stingy Eyes à pleine puissance sur toute l'arène ; GHA = Absorption en cinématique (il boit 60 % des dégâts).
- Zombies (Bruford, Tarkus) : nature « zombie » (Hamon ×2, le soleil les brûle tout de suite, sans sang à faire bouillir). Pas de style sur la touche Stand pour l'instant. Bruford : épée Luck à mi-distance, cheveux qui attrapent de loin, ramènent et boivent ; GHA = danse des cheveux. Tarkus (1150 PV, très lent, coups blindés) : anneau de chaînes (au contact, 6 s enfermés à deux dans un anneau de 74 px, recharge 14 s) ; GHA = brise-nuque.
- Speedwagon : chapeau à lames en boomerang (il revient dans la main, touche une fois), coups de rue, coup bas imparable ; la pose soigne 12 PV par seconde ; HHA = trois chapeaux en éventail ; GHA = « Speedwagon se retire avec style » : il recule, intouchable, et se soigne 5 s.
- IA (« Contre l'IA », Arcade, démo, bot d'équilibrage) : quatre niveaux, de FACILE à JOJO (temps de réaction de 20 à 4 images, garde, punitions, enchaînements, supers). Elle ne produit que des entrées de manette. La difficulté choisie est gardée dans `settings.json`.
- Arcade : six combats en 2 rounds gagnants, l'adversaire tiré au hasard, DIO en boss final (Dio Brando si le joueur est DIO) ; difficulté d'un cran plus facile au début, d'un cran plus dure à la fin ; défaite : continuer ou abandonner.
- Choix de l'arène sur l'écran VS (celle de la partie du J1 par défaut, ou au hasard) ; l'entraînement se joue dans l'arène de la partie du J1.
- Entraînement : pas d'IA. Mannequin immobile, en garde ou joué par J2 ; vie infinie (rechargée une fois le combo fini) et jauge Heart Heat infinie, désactivables ; un K.O. replace les deux persos sans score ; compteur de coups et de dégâts.
- Entraînement avancé (16/10/2026) : le mannequin peut répéter **une action choisie dans son propre kit** (ORA ORA ORA, Star Finger, HHA, GHA, dash, pose...), avec un **délai réglable** entre chaque répétition, compté à partir du moment où il redevient libre d'agir. Délai 0 = riposte à la frame près (le *reversal* des jeux de combat). Options : enchaîner la suite du coup, se rapprocher quand le coup ne porte pas, tenir la garde entre deux. Si le coup appartient à l'autre posture (Stand sorti), le mannequin sort son Stand tout seul. On peut aussi **enregistrer** une suite jouée par J2 et la faire rejouer en boucle. Une **frise des frames** montre image par image ce que faisaient les deux persos (démarrage, actif, récupération, garde, blocage, dégâts, gel) et **mesure** l'avantage réel du dernier échange.
- Joseph jeune (16/10/2026) : la prédiction « Ta prochaine réplique sera... » se joue en Pose. Après 0,33 s de pose, Joseph annonce le prochain coup de l'adversaire : la même touche que son dernier coup (affichée au-dessus de lui). Si l'adversaire frappe au corps à corps avec cette touche, le coup est attrapé et Joseph riposte gratuitement (coup de Hamon) ; sinon, il prend le coup. *Interprétation du « si c'est juste » du GDD, à confirmer.* Coup lourd = fil de Hamon posé au sol (3 max, fait trébucher) ; lourd + direction = technique secrète des Joestar (la fuite, invincible) ; spéciale = clackers boomerang ; spéciale + direction = grenade qui roule et explose au bout d'une seconde ; HHA = Tommy gun ; GHA = un plan caché : tous ses fils et grenades explosent, plus une grenade cachée sous l'adversaire.
- Caesar : Bubble Cutter (5 bulles en arc), Bubble Lens (rayon de Hamon longue portée), Bubble Launcher (3 bulles à tête chercheuse), salto arrière ; HHA = Bubble Cutter Glissade (3 vagues) ; GHA = Bubble Barrier : un anneau de 10 bulles se referme sur l'adversaire et éclate (on peut en sortir en dash).
- Lisa Lisa : élégante et acrobatique. Écharpe en fouet (enchaînement qui finit en pirouette), écharpe qui ramène l'adversaire, lance d'écharpe qui passe la garde avec du Hamon ; Snake Muffler (spéciale) : parade qui attrape un coup et riposte, et renvoie les projectiles à leur lanceur ; saut acrobatique (spéciale + direction) vers le point visé, intouchable en l'air, talon de Hamon à l'atterrissage ; HHA = lance de Hamon à pleine longueur ; GHA = piège de l'écharpe en cinématique.
- Straizo : vampire tireur d'élite. La touche Stand passe en « visée » (marche ralentie, brûle du sang) : tous ses coups deviennent des jets des yeux à très longue portée (tir rapide, tir chargé qui casse la garde, rafale). Hors visée : griffes, étreinte qui boit le sang, bond, Space Ripper Stingy Eyes. HHA = éventail de jets ; GHA = rafale d'yeux en cinématique.
- Hommes du Pilier (16/10/2026) : nature `pillar_man`, déjà reconnue par le Hamon (dégâts doublés) et par le soleil. Leur **Mode** (流法) est la touche Stand, une bascule entre deux movesets : sans Mode ils sont courts et rapides, en Mode leurs coups portent loin mais démarrent plus lentement. Wamuu a le vent, Esidisi la flamme, Kars la lumière ; **Santana n'a aucun Mode** (il ne l'a jamais maîtrisé) et n'a donc qu'une posture, compensée par la plus grosse vie du casting.
- Éveil sur la touche Power Up (16/10/2026) : un kit peut déclarer `[awakening]` — une posture où il bascule **une fois par round, sans retour**, contre des barres de Heart Heat, avec l'option `sun_immune`. La touche Stand ne peut plus l'en sortir et son aura reste allumée. Kars : 2 barres, il pose le masque de pierre et la Super Aja, devient la **forme de vie ultime** (le soleil ne lui fait plus rien, tout son moveset change, chaque coup lui rend de la vie). C'est la mécanique que le GDD appelait « jauge d'Éveil ».
- Éveil (correction 17/10/2026) : ce n'est plus un interrupteur. Le perso **reste immobile pendant `charge_s` secondes**, prend `vulnerable_mult` fois les dégâts et ne peut rien faire ; un coup qui inflige au moins `break_hitstun_f` images de stun le lui arrache et lui rend `refund` du coût. S'il tient, le combat s'arrête pour la cinématique. Kars : 5 s, dégâts doublés, cassé par 20 images de stun, moitié de la jauge rendue.
- Ressenti des Hommes du Pilier (17/10/2026) : ils ne frappent pas tous du poing. **Divine Sandstorm** n'est pas une rafale : les deux avant-bras de Wamuu tournent et ce sont **deux tornades** qui broient (nouvel effet `fx = "vortex"`). Le **Final Mode** aspire l'air de la salle dans son corps — ce qui le déchire — et le ressort **par sa corne**, pas par ses bras. **Esidisi** ne frappe pas non plus : ses **veines jaillissent** et fouettent à 54 de portée (`shape = "line"`, `fx = "tentacle"`), six coups longs au lieu de dix coups courts.
- Objets portés (17/10/2026) : un perso sans Stand **tient vraiment l'objet**, les deux mains au-dessus de la tête (nouvelle animation `carry` dans le générateur, pour tout le roster) ; avec un Stand, c'est le Stand qui le tient. Un objet **lancé en temps arrêté** reste suspendu en l'air et repart à la reprise, comme les couteaux de DIO — ce n'était pas le cas.
- Joseph (17/10/2026) : sa Tommy Gun est **dessinée dans ses mains** pendant tout le coup (`fx = "gun"`), au lieu de balles sorties de nulle part.
- Forme des ultimes (17/10/2026) : un ultime n'est plus déclenché par une hitbox de poing. Il prend la **forme de sa technique** — la règle est écrite dans `CLAUDE.md` et tenue par `tests/test_ultimates.py`. Rift Atmosphérique : rayon de vent **de la corne jusqu'à l'autre bout de l'arène** (`line`, portée 300, `fx = "wind_beam"`). Divine Sandstorm : `line`, portée 92, les avant-bras tournent pendant les 20 images de démarrage, et le coup **aspire** l'adversaire. HHA Divine Sandstorm Ultime : portée 150, aspiration sur 330. Les trucs du métier de Joseph : des **câbles** lancés sur 104 de long et 26 de large. Les Larmes d'Esidisi : un **jet de sang bouillant** à 140. Déluge de lumière de Kars : une **nappe de neuf lames** à 124. Bubble Barrier et Burn Black de Caesar : `at_target`, le dôme de bulles et le cercle de loupes se referment **là où l'adversaire se trouve**. Autodestruction de Stroheim : rayon 46 autour de lui. Road Roller : `at_target`, il tombe sur sa position. Tornado Overdrive : un plongeon de 150. Épée et cheveux de Bruford : 36 à 112 de portée. Rapière de Silver Chariot : 56 et 66.
- Aspiration (17/10/2026) : nouveau champ `pull` (vitesse) et `pull_range` (portée, par défaut `reach + radius`). Tant que le coup est actif, l'adversaire est tiré vers le perso avant que les hitboxes ne soient résolues — ce qui est aspiré est donc broyé. Contrecoup de la Tornade de Wamuu : 320 px/s sur 420 de portée, soit tout le terrain, comme dans ASBR.
- Barrage de poings (correction 17/10/2026) : un coup multi-hit ne dessine une rafale de poings **que si son `fx` est vide, `limb`, `blade` ou `blade_hair`**. Une tornade, des veines ou des câbles se dessinent eux-mêmes ; les poings étaient encore affichés par-dessus.
- Chaîne d'Onde de Lisa Lisa (17/10/2026) : nouveau champ `chains` — une **chaîne à embranchements**, une suite différente par touche. Elle est la seule du casting à l'avoir, comme dans ASBR : « Maîtresse du Hamon » ouvre, trois touches continuent (écharpe, salto-talons, pivot), trois touches finissent (envoi au mur, Snake Muffler, « Prépare-toi à mourir » imparable). Sa parade reprend son vrai nom, l'Esquive Stylée ; le Snake Muffler redevient une fin de chaîne.
- Caesar au corps à corps (17/10/2026) : son enchaînement générique (direct, coup de pied haut, talon) devient ses vraies techniques — **Uppercut d'une main** puis **Ripple Kick**, un vol plané pendant lequel il est intouchable. Ses Bubble Cutters sont des disques : ils **ricochent sur les murs** et partent en deux vagues.
- Équilibrage mesuré après la refonte des ultimes (17/10/2026, bot contre bot, 90 combats par perso) : **Kars 81 %**, DIO 81 %, Wamuu 62 %, Jotaro 62 %, Stroheim 51 %, Santana 41 %, Joseph 40 %, Lisa Lisa 38 %, **Caesar 21 %**, **Esidisi 18 %**. Deux passes ont ramené Kars à **69 %** (1000 PV au lieu de 1100 — il est le bretteur des trois, pas le mur ; lames de lumière moins fortes, jab plus lent à récupérer, déluge ramené à 100 de portée), Caesar à **30 %** (un maillon de son propre enchaînement lui coûtait du Hamon : erreur corrigée, Bubble Cutter moins cher) et Esidisi à **23 %** (il paie son sang moins cher, ses veines tapent plus fort). **DIO reste à 80 % volontairement** : c'est l'arrêt du temps, que le bot ne sait pas jouer contre — le nerfer sur ces chiffres abîmerait le perso pour un vrai joueur. Même réserve pour les zoneurs (Esidisi, Caesar, Joseph) : le bot ne tient pas la distance, il les sous-évalue.
- Objets ramassés (17/10/2026) : la touche Lourd, en portant un objet, le **balance** — un coup lent, large, qui ne casse pas l'objet (valeurs dans `[prop_swing]` des règles). Nouveau champ de kit `prop_hold` : `hands` (les deux mains au-dessus de la tête), `hair` (les **cheveux s'enroulent** autour de l'objet, tenu **derrière lui**, mains libres — Bruford, dont les cheveux sont un troisième bras) ou `tendrils` (les tentacules du Stand — Hierophant Green). Cheveux et tentacules portent plus loin qu'un bras : le coup passe de 16 à 46 de portée et de 17 à 26 de rayon — **en échange ils lancent à 70 %** de la force normale (`wrapped_throw`), parce qu'on ne met pas son corps derrière un jet tenu à bout de mèches.
- Son des coups (17/10/2026) : un coup qui a un effet à lui (`fx`) a maintenant **un bruit à lui**, joué à l'image où il devient actif — la tornade, le rayon de corne, la mitraillette, les veines, les câbles, les lames. Avant, seul l'impact faisait du bruit : un rayon qui traversait l'arène était muet. La table `FX_SOUNDS` vit dans `ui/sounds.py` (le son reste une affaire de vue, la simulation ne le connaît pas) et un test refuse tout `fx` sans voix.
- Passe sur tous les persos (17/10/2026, mesurée par `tools/audit_kits.py`) : l'outil compte ce qui se répète d'un perso à l'autre. Avant : **six persos ouvraient sur un coup appelé DIRECT**, quatre sur GRIFFE, quatre sur REVERS, et **sept coups étaient identiques au chiffre près** entre deux persos — dont tout l'enchaînement de Stand de Jotaro et de DIO, mêmes images et mêmes dégâts. Après : plus aucun coup identique entre deux persos, et les seuls noms encore partagés sont ceux que l'œuvre partage (Absorption, Zoom Punch, Overdrive, Space Ripper Stingy Eyes).
- Jotaro contre DIO (17/10/2026) : Star Platinum est **la main la plus rapide**, The World **la plus lourde**. Jotaro frappe plus souvent pour moins (barrage de 16 coups à 6, enchaînement en 4/5/7 images), DIO moins souvent pour plus (11 coups à 10, enchaînement en 5/6/9, projection au mur). Star Platinum **attrape ce qu'on lui jette** (son contre renvoie les projectiles, comme il attrape les balles).
- Ultimes qui ne montraient rien (17/10/2026) : cinq n'avaient ni cinématique, ni effet, ni projectile. Le poing de Jotaro et le coup de pied de The World frappent **trois fois** (le barrage se dessine tout seul), l'étreinte de Santana coule le long de son corps (`fx = "tentacle"`), l'écrasement de Tarkus fait **craquer le sol** (nouvel effet `fx = "shock"` : anneaux et fissures), et Speedwagon **lance son chapeau** en se retirant.
- Techniques retrouvées dans les fiches (17/10/2026) : Tarkus a **Enfer et Ciel : Tueur de Serpent** (il saute par-dessus, la chaîne remonte d'en dessous, puis il tire) ; Straizo a la **régénération instantanée** — il recolle sa chair après les grenades de Joseph, et en sort affaibli (+12 PV/s pendant 4 s, mais 40 % de dégâts en plus reçus) ;  Speedwagon n'a pas l'Onde mais un **marteau de forge**, avec lequel il tue un zombie en un coup.
- Bilan de fin de combat (17/10/2026) : `combat/stats.py` compte, pendant le combat et sans rien savoir des persos, ce que chacun a fait — dégâts infligés et subis, coups portés, **plus gros coup**, **meilleur combo** (coups × dégâts), ultimes dépensés, et la durée. L'écran de fin l'affiche au-dessus du menu de revanche, chaque colonne à la couleur de son perso. `Combo`, qui vivait dans `training.py`, est remonté là : le compteur de l'entraînement et le bilan s'en servent tous les deux.
- Outils d'entraînement (17/10/2026) : **F6** joue à 50 % puis 25 % de vitesse (des pas de simulation sautés, rien ne change dans la simulation), **F7** gèle le monde, **F8** avance d'exactement une image pendant qu'il est gelé. L'état est écrit en haut de l'écran. Avec la frise des frames, un coup se lit image par image.
- Réglage du mannequin gardé (17/10/2026) : en quittant la salle, son mode, son action (**par son nom**, `stance/slot`, pas par son numéro — il survit à un changement de perso ou de roster), son délai et ses options vont dans `settings.json`.
- Portée de Bruford (17/10/2026) : son épée est **au bout de ses cheveux**. Le coup lourd devient « Luck au bout des cheveux » : `shape = "line"`, 48 de portée au lieu de 26.
- Designs de la partie 2 refaits d'après les fiches de JoJo Wiki (16/10/2026) : Wamuu est **bronzé** avec **une seule corne** foreuse au milieu du front, une couronne de métal qui s'ouvre pour la laisser sortir, de grandes boucles d'oreilles et un **tatouage en barre** qui traverse son visage ; Esidisi a la **croix** sur le visage, des cheveux clairs qui débordent de sa coiffe et des pièces de cuir cousues aux épaules ; Kars a les **cheveux noirs ondulés** sous un bandeau sombre (pas une crête violette), la peau la plus pâle, des protège-bras et des bottes montantes ; Santana a **deux petites cornes**, des cheveux clairs ondulés jusqu'aux épaules et rien d'autre qu'un pagne ; Stroheim a une coupe en brosse large et le **monocle sur l'œil droit**, pas un demi-masque d'acier.
- Coups qui coûtent de la vie (16/10/2026) : nouveau champ `hp_cost`. Le coup ne sort que s'il reste **strictement plus** de vie que son coût, et la prend au départ — il ne peut donc jamais tuer son propre auteur. Final Mode de Wamuu (300), jets de sang d'Esidisi (25), veines en faisceau (30), autodestruction de Stroheim (280).
- Wamuu : Divine Sandstorm (deux tornades qui aspirent et broient, portée 92), canon à vent de sa corne, Armure de Vapeur (moitié des dégâts reçus 5 s), fils anti-onde du casque, et une **posture de contre** hors Mode — sa corne lit le vent. Final Mode : Rift Atmosphérique, 300 de dégâts pour 300 de sa propre vie.
- Esidisi : zoneur qui **paie ses projectiles avec son sang**. Jets à 500 degrés, veines en faisceau, flaque bouillante posée au sol, tourbillon de veines. GHA : Les Larmes d'Esidisi, déclenché par un jet de sang bouillant à 140.
- Kars : la plus grande portée du casting. Lames de lumière (`shape = "line"`), lame lancée qui **ricoche sur les murs** (nouveau champ `bounces`), masque de pierre posé en piège, éclat aveuglant. GHA : Ultimate Thing — ce n'est pas un coup mais un **éveil** de 12 s (+35 % de dégâts, −25 % reçus, 18 PV/s de régénération).
- Événements d'arène (18/10/2026) : nouveau module générique `combat/hazards.py`, décrit par les fichiers d'arène. `[[drops]]` : un objet qui tombe à intervalle régulier sur l'un des deux combattants, à tour de rôle (ombre au sol pendant `warning_s`, imparable) ; `[[trap_zones]]` : une zone qui se déclenche quand on y est projeté ; `[[surfaces]]` : un sol qui ne tient pas (`grip`, `slide`), avec `spare_style` pour épargner un style (l'Onde). L'écran des arènes règle le **soleil** (aucun, aube, plein jour) et les **événements** ; les replays enregistrent ces options. Le lustre du manoir Joestar n'est pas une scène du manoir dans le manga (le lustre qui tombe est au château de Dio, chapitre 39) : il est là à la demande du propriétaire. Nouvelle arène : **l'île d'Air Supplena** (huile au pied du pilier de l'Hell Climb, fosses à pics qui épargnent l'Onde comme dans Eyes of Heaven).
- Santana (refait le 18/10/2026, d'après JoJo Wiki et la liste de Diamond Records — il n'est jouable ni dans ASBR ni dans EoH) : 1250 PV, aucun Mode. Paume, coup de pied, **doigt de 975 kg** (ligne, portée 30) ; **Épée de côtes** qui encaisse un coup sans broncher (`armor = 1`) ; **Sous le sol** (`burrow`) : il coule dans le sol, invulnérable, et ressort sous l'adversaire ; **Infiltration** : nouveau mécanisme générique `infiltrate_s` — il entre **entièrement** dans le corps de l'adversaire (plus de hitbox, le soleil ne l'atteint plus), le dirige et le mange (`inside_dps`, `drain`) ; l'hôte **martèle n'importe quel bouton** pour le chasser, l'Onde le chasse **trois fois plus vite** et le brûle à la sortie (`[infiltration]` dans `rules.toml`) ; **Balles rendues** : il absorbe, les tirs repartent (`reflect`) et un coup reçu est puni par les balles de ses doigts (`counter`). HHA **Meat Invade** : sa chair part en morceaux qui poursuivent, mordent et le soignent. GHA inchangé. Avant cette refonte, l'infiltration ne marchait jamais : la possession n'existait que pour un Stand en mode contrôle.
- Stroheim : nature `human`, pas d'onde. Mitrailleuse, lance-flammes, et surtout ses **lampes à ultraviolets** : elles portent le marqueur `hamon`, qui dans ce jeu veut dire « lumière qui brûle les morts-vivants » — un Homme du Pilier y prend donc le double, exactement comme le dit le GDD. GHA : autodestruction, 290 de dégâts pour 280 de sa vie.

## Sources

- [Big Kid Nation — Pokémon Arena](https://www.bigkidnation.com)
- [JoJo Wiki — List of Stands](https://jojowiki.com/List_of_Stands)
- [JoJo Wiki — Love Love Deluxe](https://jojowiki.com/Love_Love_Deluxe)
- [JoJo Wiki — Awaking III Leaves](https://jojowiki.com/Awaking_III_Leaves)
- [JoJo Wiki — Doctor Wu](https://jojowiki.com/Doctor_Wu)
- [JoJo Wiki — Doggy Style](https://jojowiki.com/Doggy_Style)
- [JoJo Wiki — Smooth Operators](https://jojowiki.com/Smooth_Operators)
- [JoJo Wiki — THE MATTEKUDASAI](https://jojowiki.com/THE_MATTEKUDASAI)
- [JoJo Wiki — Big Mouth Strikes Again](https://jojowiki.com/Big_Mouth_Strikes_Again)
- [JoJo Wiki — Eclipse Eight](https://jojowiki.com/Eclipse_Eight)
- Ce que le bot d'équilibrage mesure mal (17/10/2026) : trois mesures de suite mettent **Kars en tête (81 %, 69 %, 78 %)** et **Speedwagon en dernier (24 %)**, et il faut savoir lire ces chiffres. Le bot ne sait pas : (1) **tenir la distance** — il sous-évalue tous les zoneurs (Caesar, Joseph, Esidisi, Straizo) ; (2) **jouer contre un arrêt du temps** — il surévalue DIO ; (3) **choisir une posture** — il fait défiler celles d'un `stance_cycle` au hasard environ une fois par seconde et demie, donc **toute l'identité de Speedwagon (appeler le bon compagnon) lui est invisible** ; (4) **attendre cinq secondes immobile** — l'éveil de Kars n'entre jamais dans ses chiffres, donc ses 78 % viennent de son **neutre**, pas de sa forme ultime. Conclusion appliquée : on corrige ce que la mesure montre vraiment (le neutre de Kars : ses longues lames récupèrent plus lentement, −6 et −7 en garde au lieu de presque rien), et on laisse ce qu'elle mesure mal au jugement du joueur.
- L'éveil dure tout le combat (17/10/2026) : la forme de vie ultime **ne retombe pas entre les rounds**. Kars a posé le masque de pierre et la Pierre Rouge : le round suivant commence avec l'Être Ultime (`Rounds.awakened` suit l'état d'un round à l'autre, comme la jauge Heart Heat). Sa cinématique de naissance passe de 4,6 à 5,5 s et se joue en quatre temps : la pierre se pose dans le masque, le masque se referme et les pointes s'enfoncent, la lumière déchire son corps, et il ouvre ses ailes.
- Forme de vie ultime (complétée 17/10/2026, d'après la liste ASBR) : éveillé, Kars n'est pas un Homme du Pilier avec de meilleurs chiffres. **Le soleil ne le touche plus** (`sun_immune`), il porte **sa propre Onde** (« Onde de Kars », 120 de portée, qui brûle les morts-vivants), il **tire ce qu'il a absorbé** (« Le pouvoir des gènes suprêmes » : une volée de plumes puis un piranha à tête chercheuse) et un **tentacule de poulpe** balaie devant lui et **ramène** l'adversaire à portée de griffes (`pull`). Tout ce qu'il touche le nourrit.
- Correction (17/10/2026) : l'écharpe de Satiporoja avait été donnée à Straizo. C'est l'objet de **Lisa Lisa**, et il conduit l'Onde — or Straizo a bu au masque de pierre : l'Onde le **brûle**. La seule Onde qu'un vampire peut porter est celle qu'il accumule en lui pour exploser. Remplacée par ce que sa fiche lui donne vraiment, la régénération.
