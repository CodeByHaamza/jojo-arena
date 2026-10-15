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
| Clash (Ora vs Muda) | Deux attaques qui se touchent au même instant (rush contre rush, coup contre coup) déclenchent un clash comme dans ASBR : les deux joueurs martellent la touche d'attaque pendant 3 s, une barre de duel bouge à l'écran, le perdant prend tout le rush et est éjecté |
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
| Heart Heat (HHA, ou GHA avec 2 barres) | O | RT / R2 |
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
| **Jonathan Joestar** | Hamon · Tank rushdown | Coups lourds et lents, grosse vie (1150). Hamon à courte portée | Sunlight Yellow Overdrive : rush Hamon qui brûle les vampires. Peut charger le Hamon dans son épée (Luck & Pluck) pour plus de portée | Luck & Pluck : coup d'épée Hamon géant |
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
- Sprites : 48 px, style A (contour noir, ombrage 2-3 tons, highlight). Résolution interne 480 × 270.

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
