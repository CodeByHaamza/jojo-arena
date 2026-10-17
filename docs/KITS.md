# Écrire un kit

Le kit d'un perso est un fichier `jojo_arena/characters/<id>.toml`. Tout ce qui touche à l'équilibrage (dégâts, durées, vitesses) est ici, jamais dans le code. Ce document liste tous les champs ; un test vérifie que chaque champ utilisé dans un kit y figure.

Unités : les durées en `_f` sont en images (60 par seconde) ; celles en `_s` en secondes. Les distances sont en pixels du jeu (l'écran fait 480 × 270), les vitesses en pixels par seconde.

## Le perso

| Champ | Effet |
| --- | --- |
| `name` | Nom affiché |
| `max_hp` | Vie (1000 par défaut ; tanks jusqu'à 1150, glass cannons vers 850) |
| `walk_speed` | Vitesse de marche |
| `strength` | Force physique du Stand (1 = normale). Multiplie la vitesse, les dégâts et le recul des objets qu'il lance ; à partir de 1,5 l'objet fait rebondir sur les murs (Star Platinum, The World : 1,8) |
| `style` | Ce que fait la touche Stand. `{ type = "stance_toggle", off = "base", on = "stand", stand_body = true }` : bascule entre deux postures, et `stand_body` donne au Stand un corps qui peut être touché |
| `awakening` | Table `[awakening]`, la touche Power Up : `stance` (la posture où il bascule), `bars` (coût en barres de Heart Heat), `sun_immune` (le soleil ne le brûle plus), `label`/`label_en` (nom affiché). Une fois par round, sans retour possible : la touche Stand ne peut plus l'en sortir |
| `style` (suite) | `{ type = "stance_cycle", stances = ["base", "tattoo", "amato"] }` : la touche fait défiler plusieurs postures l'une après l'autre, pour un perso qui appelle plusieurs alliés ou un Homme du Pilier à plusieurs Modes |
| `remote`, `remote_range`, `remote_speed` | Dans `style` : maintenir la touche Stand envoie le Stand seul, dans cette posture, jusqu'à cette distance, à cette vitesse (mode contrôle) |
| `style = { type = "hamon" }` | Style Hamon : maintenir la touche Stand fait respirer (la jauge de Hamon se remplit, immobile et vulnérable) ; les coups à `hamon_cost` la dépensent. Réglages dans `[hamon]` de `combat/rules.toml` |
| `style = { type = "vampire", off = "base", on = "freeze" }` | Style vampire : la touche Stand passe dans la posture `on` (gel vaporisant), qui demande un peu de sang, en brûle tant qu'elle dure et s'arrête quand il n'y en a plus. Le sang se remplit en drainant ; intact un moment, le vampire cicatrise en dépensant du sang. Réglages dans `[vampire]` des règles |
| `pose_heal_per_s` | La pose soigne autant de vie par seconde (le cri de Speedwagon) |
| `pose_counter`, `pose_counter_ready_s` | Après avoir posé ce nombre de secondes (0,33 par défaut), le perso prédit que l'adversaire refera son dernier coup (la même touche) : s'il a raison, ce coup est attrapé et il répond avec ce coup du kit (« Ta prochaine réplique sera... » de Joseph) ; s'il a tort, il prend le coup |
| `nature` | `human` par défaut ; `vampire`, `zombie` ou `pillar_man` : le Hamon fait double dégâts et bloque leur régénération, le soleil les brûle |

## Les postures

`[stances.<nom>]`, par exemple `base` (sans Stand) et `stand` (Stand sorti).

| Champ | Effet |
| --- | --- |
| `label` | Titre de la page dans la liste des coups |
| `tag` (et `tag_en`) | Nom court affiché dans le HUD quand cette posture est active (sinon « STAND ») |
| `walk_speed_mult` | Multiplie la vitesse de marche dans cette posture |

Les coups d'une posture : `[stances.<nom>.moves.<touche>]`, où la touche est `light`, `heavy`, `heavy_alt` (coup lourd avec une direction tenue : attaque en mouvement), `special` ou `special_alt` (spéciale avec une direction tenue). Les coups partagés par toutes les postures vont dans `[moves.<nom>]` : `hha` (Heart Heat Attack, 1 barre) et `gha` (Great Heat Attack, 2 barres).

## Un coup

### Présentation

| Champ | Effet |
| --- | --- |
| `label` | Nom dans la liste des coups |
| `info` | Explication d'une ligne dans la liste des coups |
| `anim` | Animation à jouer (par défaut, le nom de la touche). Une variante `famille_nom` (`special_splash`) se dessine dans la fiche de look ; une planche qui ne l'a pas (le Stand) joue la famille (`special`) |
| `shout` | Cri écrit à l'écran quand le coup sort ; pour une rafale, à chaque coup (`ORA`, `MUDA`) |
| `stand_flash` | Le Stand apparaît le temps de ce coup, même rangé |
| `fx` | Dessin pendant la phase active : `limb` (doigt, bras), `tentacle`, `blade`, `hair` (mèches), `chain` (chaîne), `beam` (jets des yeux), `lens` (rayon à travers une bulle), `scarf` (écharpe ondulante) ou `scarf_spear` (écharpe rigide), `blade_hair` (la lame et les mèches ensemble), `vortex` (deux tornades devant lui, Divine Sandstorm), `wind_beam` (le rayon d'air qui sort de la corne), `cables` (des câbles lancés en éventail), `blood_jet` (du sang bouillant pompé dans une veine), `blade_fan` (une nappe de lames de lumière) ou `gun` (une mitraillette tenue à la hanche), jusqu'à `reach`. `vortex`, `cables` et `gun` sont dessinés pendant tout le coup, pas seulement quand il peut toucher. Avec `at_target` : `beam` (une colonne de lumière qui tombe sur place), `lenses` (des loupes qui se referment en cercle puis tirent), `bubbles` (un dôme de bulles qui gonfle et éclate), `tentacle`/`hair` (qui jaillissent du sol) ; sans `fx`, un objet lourd qui tombe du ciel |

Traductions : `label_en`, `info_en` et `shout_en` donnent le texte anglais (de même `label_en` pour une posture, et `role_en`, `blurb_en`, `name_en` dans le roster). Sans traduction, le texte français s'affiche.

### Timing

| Champ | Effet |
| --- | --- |
| `startup_f` | Images avant de pouvoir toucher |
| `active_f` | Images pendant lesquelles le coup touche |
| `recovery_f` | Images de récupération après |
| `invincible_f` | Premières images où l'on ne peut pas être touché |
| `cooldown_s` | Délai avant de pouvoir réutiliser le coup |
| `cancel_on_hit` | Touches qui annulent ce coup quand il a touché (enchaînements) |
| `chains` | Chaîne à embranchements : `{ light = "...", heavy = "..." }`, une suite différente par touche, une fois que le coup a porté (la Chaîne d'Onde de Lisa Lisa) |
| `chain` | Nom du coup suivant quand on réappuie sur la même touche après avoir touché (ex. `light` → `light2` → `light3` : trois coups différents). La touche doit être dans `cancel_on_hit` |

### Zone de frappe

| Champ | Effet |
| --- | --- |
| `reach` | Distance du centre de la zone devant le perso |
| `radius` | Rayon de la zone (0 = pas de coup au corps à corps) |
| `shape` | `circle` (un cercle à `reach`) ou `line` (une ligne du corps jusqu'à `reach`, sans angle mort de près) |
| `at_target` | La zone tombe là où se trouvait l'adversaire au début du coup ; `reach` sert alors de **distance maximale** de largage (0 = sans limite) |
| `leap` | Bond pendant le démarrage, jusqu'à cette distance |
| `leap_to` | Vers l'adversaire (`target`, s'arrête à côté de lui) ou vers le point visé (`cursor` : souris, sinon stick droit, sinon direction tenue) |
| `leap_height` | Hauteur du saut à l'écran (0 = glisse au sol, comme un grappin) |
| `pull` | Aspire l'adversaire vers le perso à chaque image active (vitesse) : tornade, veines autour de la cheville |
| `pull_range` | Portée de l'aspiration (0 = `reach` + `radius`) |
| `lunge` | Avance pendant le démarrage et la phase active (vitesse) ; une rafale continue d'avancer à chaque coup ; négatif : recule |

### Effet sur l'adversaire

| Champ | Effet |
| --- | --- |
| `damage` | Dégâts |
| `hitstun_f` | Durée pendant laquelle l'adversaire est sonné |
| `blockstun_f` | Pareil en garde (0 = calculé depuis `hitstun_f`) |
| `knockback` | Force du recul |
| `hitstop_f` | Petit gel des deux persos à l'impact |
| `wall_bounce` | L'adversaire rebondit sur les murs |
| `unblockable` | Imparable (saisies) |
| `drain` | Part des dégâts rendue en vie à l'attaquant |
| `hamon_cost` | Style Hamon : s'il y a assez de Hamon, le coup le dépense et frappe plus fort (sinon il reste normal) ; ses projectiles portent aussi le Hamon |
| `hamon_mult` | Dégâts du coup boosté (par défaut `boost_mult` des règles) |
| `hamon_unblockable` | Boosté, le coup traverse la garde (l'onde passe à travers) |
| `hamon` | Le coup est toujours du Hamon (les supers d'un manieur du Hamon), sans rien dépenser |
| `blood_cost` | Style vampire : le coup ne sort qu'avec assez de sang, et le dépense |
| `hp_cost` | Le coup s'arrache à son auteur : il ne sort que s'il reste plus de vie que ça, et la prend au départ (Final Mode de Wamuu) |
| `freeze_f` | Touché net, l'adversaire est gelé sur place ce nombre d'images (gel vaporisant) |
| `finish_drain` | Part des dégâts du coup final d'une cinématique rendue en vie |
| `detonate` | Au premier tir de son projectile, tous les pièges du perso explosent (avec ce même projectile) et ses grenades encore au sol sautent aussitôt (le plan caché de Joseph) |
| `cage_s`, `cage_radius` | Touché net : un anneau de chaînes de ce rayon se ferme autour des deux combattants, ce nombre de secondes ; personne n'en sort (Tarkus) |
| `guard_damage` | Multiplie l'usure de la jauge de garde quand le coup est bloqué (casse-garde) |
| `clashable` | Peut déclencher un clash contre un autre coup (vrai par défaut pour les coups au corps à corps) |

### Défense

| Champ | Effet |
| --- | --- |
| `counter` | Coup de contre : un coup au corps à corps reçu pendant la phase active est annulé, et ce coup-ci (le nom d'un autre coup) part aussitôt |
| `reflect` | Tant que le coup est actif, un projectile qui atteint le perso repart en sens inverse et devient le sien (le Snake Muffler de Lisa Lisa) |
| `possess_s` | Coup du Stand piloté : s'il touche, tu diriges la marche de l'adversaire pendant cette durée |
| `armor` | Nombre de coups encaissés sans broncher pendant le démarrage et la phase active (on prend les dégâts) |

### Rafales

| Champ | Effet |
| --- | --- |
| `hits` | Nombre de coups de la rafale |
| `hit_every_f` | Un coup toutes les N images |
| `last_damage` | Dégâts du dernier coup (le coup final) |
| `last_knockback` | Recul du dernier coup |
| `last_wall_bounce` | Le dernier coup fait rebondir sur les murs |

### Pouvoirs

| Champ | Effet |
| --- | --- |
| `time_stop_s` | Arrête le temps pendant cette durée |
| `time_stop_at` | À partir de la phase `active` (par défaut) ou dès le `start` du coup |
| `disarm_s` | Les coups du Stand sont indisponibles pendant cette durée ensuite |
| `buff` | Nom d'un bonus de la section `[buffs]`, lancé par ce coup |

### Ultimes en cinématique

| Champ | Effet |
| --- | --- |
| `cinematic` | Nom de la cinématique jouée par l'affichage (`road_roller`, `star_finish`, `chariot_clones`, `hierophant_web`, `hierophant_inside`) |
| `cinematic_s` | Durée de la cinématique ; le combat est figé pendant ce temps |
| `cinematic_at` | `hit` : seulement si le coup touche (pas en garde) ; `start` : dès que le coup part |
| `finish_damage`, `finish_hitstun_f`, `finish_knockback`, `finish_wall_bounce` | Le coup final qui tombe à la fin de la cinématique (imparable) |
| `web` | Fils tendus sur toute l'arène à la fin de la cinématique (voir plus bas) |

## Projectiles

`[<coup>.projectile]`

| Champ | Effet |
| --- | --- |
| `speed`, `radius`, `damage`, `lifetime_s` | Vitesse, taille, dégâts, durée de vie |
| `hitstun_f`, `blockstun_f`, `knockback`, `hitstop_f` | Comme pour un coup |
| `count`, `spread_deg` | Plusieurs projectiles en éventail sur cet angle |
| `origin`, `ring_radius` | `self` (depuis le perso) ou `ring` (en cercle autour de la cible, vers elle) |
| `waves`, `wave_every_f` | Plusieurs salves, à N images d'écart (chaque salve comble les trous de la précédente) |
| `homing_deg_s` | Tête chercheuse : degrés par seconde dont il tourne vers la cible |
| `returns` | Boomerang : à mi-course (ou contre un mur, ou après avoir touché) il revient dans la main de son lanceur |
| `explode_radius` | Grenade : ne touche pas au contact, roule, s'arrête contre les murs et les objets, et explose en fin de vie ; l'adversaire à ce rayon (plus son corps) est touché |
| `drag` | Part de sa vitesse gardée à chaque image (sous 1 : il ralentit jusqu'à s'arrêter) |
| `wall_bounce` | Ce qu'il touche rebondit contre les murs |
| `bounces` | Ricochet : le tir lui-même repart du mur, ce nombre de fois (lame lancée de Kars) |
| `look` | Dessin : `orb`, `knife`, `gem`, `blade`, `wine`, `hat`, `clacker`, `grenade`, `bubble`, `bullet`, `spark`, `jet` |

## Pièges

`[<coup>.trap]` : posé devant le perso, il tire tout seul quand l'adversaire passe dessus.

| Champ | Effet |
| --- | --- |
| `distance` | Distance devant le perso |
| `radius` | Rayon de détection |
| `lifetime_s` | Durée de vie |
| `max_count` | Nombre maximum ; le plus ancien disparaît |
| `projectile` | Ce qu'il tire (comme un projectile) |

## Toile

`[<coup>.web]` : des fils tendus sur toute l'arène ; les toucher fait tirer les deux points d'ancrage les plus proches.

| Champ | Effet |
| --- | --- |
| `columns`, `rows` | Points d'ancrage en largeur et en hauteur |
| `margin` | Distance gardée par rapport aux murs |
| `lifetime_s` | Durée de vie |
| `rearm_s` | Après un tir, délai avant de pouvoir tirer de nouveau |
| `touch_radius` | Distance à un fil qui compte comme le toucher |
| `projectile` | Ce que tirent les points d'ancrage |

## Bonus

`[buffs.<nom>]`, lancés par le champ `buff` d'un coup.

| Champ | Effet |
| --- | --- |
| `duration_s` | Durée |
| `speed_mult` | Multiplie la vitesse |
| `damage_dealt_mult`, `damage_taken_mult` | Multiplie les dégâts infligés et reçus |
| `afterimages` | Images rémanentes derrière le perso |
| `heal_per_s` | Vie regagnée par seconde tant que l'état dure |
