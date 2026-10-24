# Partie 3 : notes et idées pour la suite

Notes du 24/10/2026. **Ce sont des propositions, pas des décisions** : le [GDD](GDD.md) fait foi. Chaque idée de perso part des fiches JoJo Wiki et des listes de coups d'ASBR et d'EoH (sources en bas). Quand une source manque ou se contredit, c'est marqué **à vérifier** ; on ne comble pas le trou.

## Où on en est

- **Jouables** : Jotaro, Kakyoin, Polnareff, DIO (vague 1).
- **Arène** : Le Caire, rue de nuit.
- **Glossaire** : Stand, tarot, temps arrêté, les quatre persos et leurs Stands.
- **Prévus au GDD, pas faits** : Avdol, Joseph âgé, Iggy, Hol Horse, Vanilla Ice, Mariah, N'Doul, Pet Shop ; le manoir de DIO et le désert égyptien.

Le moteur sait déjà faire : Stand on/off, mode contrôle, temps arrêté, pièges, projectiles, visée libre, saisies inbloquables, Hamon, vampire et soleil, `stance_cycle` (amis appelés), éveil, objets à lancer.
Il ne sait pas encore faire : **l'invisibilité**, **le vol**, **les états qui s'accumulent** (magnétisme, brûlure), **le décor effacé**, **un Stand et du Hamon en même temps**.

C'est ce qui décide l'ordre proposé plus bas.

---

## 1. Personnages

### Vague 3A : finir l'équipe des Croisés

Une mécanique moteur chacun, et un vrai trou dans le roster sans eux.

#### Muhammad Avdol (Magician's Red) : zoner de feu

- **Ce que disent les jeux** (ASBR) :
  - **Red Bind** : des cordes de flammes sortent de sa main après un court démarrage, puis Magician's Red fait exploser l'adversaire.
  - **Crossfire Hurricane Variation** : un piège au sol qu'on charge ; plus on tient la touche, plus loin l'ankh explose.
- **Forme des coups** :
  - Red Bind → `shape = "line"`, `radius` large, saisie qui ligote (règle « fil, câble, corde »).
  - Crossfire Hurricane (l'ankh) → projectile.
  - Variation → piège posé à distance réglable par la charge.
- **Ultime** : Crossfire Hurricane Special, les ankhs qui se referment sur la cible → `projectile` avec `count` et `ring`.
  **À vérifier** : JoJo Wiki ne donne pas le même nom selon la page (Special ou Variation). Il faut trancher avec la fiche ASBR avant d'écrire le kit.
- **Mécanique nouvelle** : la **brûlure**, des dégâts sur la durée. Elle sert aussi à Esidisi et plus tard à Red Hot Chili Pepper.
- **Détecteur de vie** (GDD) : il révèle les persos invisibles. C'est le contre naturel de Vanilla Ice (voir les interactions).

#### Joseph Joestar âgé (Hermit Purple + Hamon) : grappler longue portée

- **Ce que dit ASBR** : un grappler à longue portée, centré sur Hermit Purple, avec une saisie à mi et longue distance. Il a aussi un mode Hamon tiré de la jauge Heart Heat.
  - **Hermit Purple!** : les ronces tirent l'adversaire vers lui, et la suite dépend de la touche entrée.
  - **Coal Tar** : Hermit Purple apporte un bidon de goudron qu'il renverse, un piège au sol.
- **Mécanique nouvelle** : un style **Stand + Hamon**. On compose les deux composants qui existent déjà (`stance_toggle` et `hamon`) au lieu d'écrire un style à part. Les ronces transmettent le Hamon : double dégâts sur DIO et Vanilla Ice.
- **Clin d'œil à reprendre** : « Ta prochaine réplique sera... » existe déjà chez Joseph jeune ; le vieux Joseph peut garder la même mécanique.
- **Ultime** : le GDD propose « Hermit Purple + Overdrive, grab à travers l'arène » → `shape = "line"`, très grande `reach`, saisie.
  **À vérifier** : la recherche n'a pas trouvé la HHA ni la GHA d'ASBR. L'Overdrive par le sol vient de *Diamond Records*, un autre jeu. Il faut lire la fiche ASBR avant de fixer l'ultime.

#### Iggy (The Fool) : petit, rapide, dans les airs

- **Ce que dit ASBR** :
  - **Sand Dome** : un dôme de sable qui bloque tout (même l'inbloquable) sauf les saisies, contre de la Heart Heat.
  - **Hang Glider** : des ailes de sable. Stand rentré, il descend lentement ; Stand sorti, il reste en l'air à hauteur fixe jusqu'à l'adversaire ou au mur.
- **Ultime** (« Serves you right! ») : une énorme vague de sable devant lui, l'adversaire projeté, The Fool qui le roue de coups, et Iggy qui finit en le mordant au nez → gros `radius` en cône devant lui.
  **À vérifier** : ce détail vient de l'*Animated Character Database*, pas de JoJo Wiki.
- **Mécanique nouvelle** : le **vol**, une couche « en l'air » au-dessus des pièges et des fils au sol. Elle resservira pour Pet Shop, Kars ultime et Aerosmith.
- **Hitbox** : il est petit, donc une boîte de corps plus petite. C'est son identité : dur à toucher.

### Vague 3B : les méchants iconiques

#### Vanilla Ice (Cream) : l'assassin invisible

- **Ce que dit ASBR** :
  - En vide, Cream disparaît et réapparaît à des points d'ancrage de l'arène.
  - Ice **ne verrouille jamais** l'adversaire : on dirige le Stand à la main (la visée libre existe déjà).
  - Tout ce qui passe par le vide est **inbloquable**, HHA et GHA comprises.
  - **Faiblesse** : ses spéciales sont lentes et en ligne droite, donc on les voit venir.
  - **« Once and for all! »** : la seule spéciale Stand sorti. Elle coûte de la jauge de Stand et fait des dégâts proches d'un GHA.
- **Mécaniques nouvelles** :
  - **Invisibilité** : intouchable mais aveugle ; il sort la tête pour voir et devient touchable.
  - **Décor effacé** : un trou dans le décor là où il passe. Les objets de l'arène savent déjà casser ; il manque le « disparu pour le round ».
- **Ultime** : la trace en ligne droite qui efface tout → `shape = "line"`, `reach` qui traverse l'arène, inbloquable.
- **Fidélité** : DIO l'a fait vampire, et c'est le soleil qui l'achève face à Polnareff. Nature `vampire` : le Hamon et le soleil le blessent.

#### Hol Horse (Emperor) : tireur qui court

- **Ce que disent les jeux** :
  - ASB : la skill **« You're up, J. Geil! »** et la super **« Hol Horse is gonna kill ya! »**.
  - EoH : une DHA où il lance une bouteille et la fait éclater d'une balle ; Hanged Man surgit dans les éclats de verre, poignarde l'adversaire à l'épaule et l'immobilise, puis Hol Horse tire.
- **Dans notre moteur** :
  - balles guidées à la visée libre (déjà là, c'est même l'exemple du GDD) ;
  - J. Geil en assist qui n'agit **que dans les reflets** : flaques, éclats de verre, et l'arène de Calcutta (voir les arènes).
- **Ultime** : la rafale de balles guidées → `projectile` avec `count`. Pas un cercle de poing.
- **À vérifier** : la page JoJo Wiki ASBR de Hol Horse n'est pas sortie dans la recherche, seulement ASB et EoH.

#### Pet Shop (Horus) : un faucon qui ne se pose pas

- **Ce que dit ASBR** :
  - 800 PV.
  - Horus est **toujours sorti**. La touche Stand fait passer du **sol** à **l'air** et change le moveset. Ça colle exactement à notre `stance_toggle`.
  - Au sol, le coup lourd tire trois pics de glace devant lui, et le lourd accroupi fait jaillir un pic de glace du sol.
  - En l'air, le lourd tire trois pics de glace vers le sol, en diagonale.
- **Ce que dit EoH** : un énorme missile de glace inbloquable se forme au-dessus de sa tête ; la cible touchée est paralysée.
- **Mécanique** : le vol d'Iggy, réutilisé. Le gel existe déjà chez DIO P1.
- **Rivalité** : avec Iggy (voir les interactions).

#### Mariah (Bastet) : la pose de prises

- **Ce que dit EoH** :
  - Pas de vrai combo au corps à corps : son coup normal est un fil de métal qui paralyse.
  - Bastet se pose d'un claquement de doigts, au sol ou **sur un mur**. C'est un piège fixe et inbloquable ; le toucher électrocute et magnétise.
  - Le magnétisme monte par niveaux : Lv 1, Lv 2, puis Lv MAX.
- **Mécanique nouvelle** : un **état qui s'accumule**, une jauge de magnétisme sur l'adversaire. À chaque niveau, le métal de l'arène vient plus fort à lui. Le même système servira à la brûlure d'Avdol.
- **Ultime** (GDD) : la pluie de métal sur la cible → gros `radius` centré sur la cible magnétisée.

#### N'Doul (Geb) : le sniper aveugle

- **Ce que dit EoH** :
  - Aveugle : il ne verrouille personne et ses coups sont faibles.
  - **Mode debout** : sa canne, avec un estoc qui repousse et un coup de pommeau qu'on charge.
  - **Mode assis** : Geb attaque à sa place.
  - Pas de dash à tête chercheuse : il envoie Geb devant lui, jusqu'à quatre fois, et ses skills partent là où est Geb.
- **Dans notre moteur** : le mode assis, c'est notre **mode contrôle**, déjà écrit pour Hierophant Green.
- **Mécanique nouvelle** : **l'ouïe**. Bouger, courir ou frapper fait du bruit ; un adversaire immobile ne peut pas être visé par Geb (règle du GDD). C'est une petite règle, mais elle change tout le duel.
- **Arène** : le désert lui revient (voir les arènes).

### Vague 3C : bonus et persos secondaires (à sourcer avant tout)

Les persos de cette vague ne sont ni dans le roster d'ASBR ni dans celui d'EoH, d'après la recherche (sauf Hol Horse & Boingo, **à vérifier**). Sans liste de coups officielle, il faut **tout** prendre dans le manga, et JoJo Wiki d'abord.

**Proposition** : en faire des **événements d'arène** plutôt que des persos jouables, comme Nukesaku dans ASBR (voir plus bas). Ça coûte moins cher et ça donne vie aux arènes.

| Perso | Idée | Pourquoi |
| --- | --- | --- |
| **Hol Horse & Boingo** (EoH) | Duo : les prédictions de Thoth s'affichent comme une case de BD (« dans 3 s, tu tires ici »). | Mécanique unique, et cousine de « Ta prochaine réplique sera » |
| **J. Geil** (Hanged Man) | Assist de Hol Horse, ou piège de l'arène de Calcutta : il n'existe que dans les reflets | Les flaques et les éclats sont un vrai jeu de vue de dessus |
| **D'Arby l'aîné** (Osiris) | Le pari avant le combat : on mise sur le vainqueur du round, et le perdant perd une barre de HH | Mode fun, sans moteur nouveau |
| **Alessi** (Sethan) | Son ombre qui rajeunit : la cible touchée passe en « enfant », coups plus faibles, quelques secondes | État temporaire, réutilisable |
| **Nukesaku** | Événement du manoir de DIO (repris d'ASBR) | Déjà dans ASBR, voir plus bas |

---

## 2. Interactions spéciales (`combat/interactions.py`)

Fidèles à l'œuvre, à ajouter avec les persos qui les déclenchent.

| Situation | Règle proposée | Sources à relire |
| --- | --- | --- |
| Avdol contre un perso invisible | Le détecteur de vie (flamme qui montre la direction) révèle Vanilla Ice dans le vide pendant 2 s | GDD, fiche Magician's Red |
| Vanilla Ice au soleil | Nature `vampire` : le soleil et le Hamon le blessent. Au manoir, arracher un rideau peut l'achever | Fiche Vanilla Ice (sa mort) |
| Joseph âgé contre DIO | Ronces de Hamon : double dégâts, et la régénération de DIO est bloquée (règle Hamon qui existe) | GDD, interactions |
| **DIO boit le sang de Joseph** | Éveil de DIO : sa saisie réussie sur un Joestar (Joseph, Jotaro) remplit sa jauge d'éveil ; éveillé, +1 à 2 s de temps arrêté. C'est le DIO de la fin de la partie 3 | Fiche DIO, fin de partie 3 : **à vérifier** pour la durée exacte |
| Jotaro éveillé | +1 s de temps arrêté (déjà noté dans la roadmap, reste à brancher sur `[awakening]`) | GDD, Power Up |
| Kakyoin, la toile contre le temps arrêté | Si DIO arrête le temps alors que la toile de 20 m est posée, tous les fils cassent d'un coup | Le combat de Kakyoin contre DIO |
| Iggy contre Pet Shop | Rivalité : intro dédiée, Iggy fait +10 % de dégâts à Pet Shop | Leur combat au manoir |
| Polnareff contre J. Geil | Il venge sa sœur : intro dédiée (si J. Geil devient jouable ou événement) | Fiche Polnareff |
| Vol contre pièges au sol | Un perso en l'air (Iggy en planeur, Pet Shop) passe au-dessus des fils de Kakyoin et du goudron de Joseph, mais pas des projectiles | Règle moteur |

---

## 3. Arènes

Le GDD prévoit le **manoir de DIO** et le **désert égyptien**. En plus, quatre idées, chacune avec un perso qui en profite (règle du GDD).

| Arène | Sol | Éléments interactifs | Pour qui |
| --- | --- | --- | --- |
| **Manoir de DIO** (GDD) | Couloirs sombres, tapis rouge | Rideaux à arracher (rai de soleil), escalier, faux couloirs. **Nukesaku** saute d'en haut et frappe, sans limite (le gimmick d'ASBR). Sortie de ring par le trou du mur : soleil pour les vampires, chute pour les autres (le Situation Finish d'ASBR) | Vanilla Ice, Iggy, Pet Shop, DIO |
| **Désert égyptien** (GDD) | Sable, dunes | Mirages, point d'eau rare (Geb y frappe plus fort), sable mou qui ralentit, tempête qui réduit la vue | N'Doul, Iggy |
| **Pont du Caire** (dans ASBR) | Pierre, eau en dessous | Garde-corps qui casse, bord qui fait tomber | Duels finaux Jotaro / DIO |
| **Ruelle de Calcutta** | Pavés mouillés | **Flaques et vitrines** : les reflets où J. Geil peut agir ; les casser coupe Hanged Man | Hol Horse, Polnareff |
| **Pont du cargo** (Strength) | Bois et métal | Conteneurs à lancer, cordages, mâts | Avdol, Joseph |
| **Casino / bar de D'Arby** | Moquette | Tables à renverser, le pari d'avant combat (voir les modes) | Mode fun |

La rue du Caire peut gagner un événement : **la voiture qui traverse** dans ASB.
**À vérifier** : seul Giant Bomb le mentionne, pas JoJo Wiki.

---

## 4. Événements de combat

Des moments qui arrivent pendant un round et changent la lecture du combat. Un événement par arène, pas plus.

- **Nukesaku** (manoir, repris d'ASBR) : il tombe du plafond et frappe le plus proche. On peut le frapper pour le renvoyer.
- **Le soleil se lève sur le manoir** : comme l'aube du manoir Joestar, mais rideau par rideau, arrachés par les coups lourds.
- **Tempête de sable** (désert) : 10 s de vue réduite. Bonne pour Iggy et N'Doul, mauvaise pour les zoners.
- **Le chrono de Holly** (mode Histoire) : 50 jours, comptés en combats. Chaque défaite coûte un « jour ». C'est la vraie pression de la partie 3 (**à vérifier** dans la fiche Holly Kujo).
- **Les cartes de tarot** : chaque Stand vaincu donne sa carte. Elle s'affiche dans le glossaire, qui a déjà une entrée « Les arcanes du tarot ».

---

## 5. Modes et gameplay

- **Arcade partie 3 : le voyage vers l'Égypte**. Les combats suivent la route (Japon, Hong Kong, Singapour, Inde, Pakistan, Égypte) et finissent au manoir contre DIO. L'arcade existe déjà, il ne faut que l'ordre des adversaires et des arènes.
- **Défis par perso** (déjà dans les idées du 16/10) : « fais exploser un ankh piégé », « attrape avec Hermit Purple puis Hamon », « sors du vide et touche avec Cream ».
- **Le pari de D'Arby** : avant le match, chaque joueur mise une barre de HH sur un round. Mode local fun, aucun moteur nouveau.
- **2v2 « Croisés »** : le GDD le garde pour plus tard ; la partie 3 est l'équipe idéale pour le tester (Jotaro + Avdol contre DIO + Vanilla Ice).

---

## 6. Ordre proposé

Chaque étape apporte **une** mécanique moteur, réutilisée ensuite.

1. **Avdol** : brûlure (état sur la durée) et piège à distance chargée. Peu de moteur, gros manque dans le roster.
2. **Joseph âgé** : style Stand + Hamon composé. Débloque l'interaction Hamon contre DIO dans la partie 3.
3. **Manoir de DIO** avec Nukesaku et les rideaux : l'arène du boss.
4. **Iggy** : le vol (couche aérienne).
5. **Pet Shop** : le vol réutilisé, presque gratuit.
6. **Vanilla Ice** : invisibilité et décor effacé. Le plus gros morceau, mais Avdol est déjà là pour le contrer.
7. **Hol Horse** (+ J. Geil dans les reflets), puis **Mariah** (état cumulé), puis **N'Doul** (ouïe) avec le **désert**.
8. **Éveils de Jotaro et de DIO** (temps arrêté plus long), une fois le roster en place.

Pour chaque perso : la liste du CLAUDE.md (fiche wiki, Stand, ASBR, EoH, choix écrit, ce qui ne rentre pas), puis `jojo-balance`.

---

## 7. Questions pour toi

1. **Persos secondaires** (D'Arby, Alessi, J. Geil, Boingo) : jouables, ou événements d'arène ?
2. **Vanilla Ice** : l'effacement du décor reste pour le round, ou il revient comme les caisses ?
3. **Le vol** : on s'autorise une vraie « hauteur » (ombre qui s'éloigne du sprite), ou juste un état « en l'air » sans hauteur ?
4. **L'éveil de DIO par le sang de Joseph** : ça te plaît comme règle, ou trop fort ?
5. **L'ordre** : on commence bien par Avdol, ou tu veux un méchant d'abord ?

---

## Sources

- JoJo Wiki : [ASBR Muhammad Avdol](https://jojowiki.com/ASBR/Muhammad_Avdol), [Magician's Red / Crossfire Hurricane Special](https://jojowiki.com/Crossfire_Hurricane_Special), [ASBR Old Joseph Joestar](https://jojowiki.com/ASBR/Old_Joseph_Joestar), [EoH Old Joseph Joestar](https://jojowiki.com/Eyes_of_Heaven/Old_Joseph_Joestar), [Diamond Records Old Joseph](https://jojowiki.com/Diamond_Records/Old_Joseph_Joestar), [ASBR Iggy](https://jojowiki.com/ASBR/Iggy), [ASBR Vanilla Ice](https://jojowiki.com/All-Star_Battle_R/Vanilla_Ice), [EoH Vanilla Ice](https://jojowiki.com/Eyes_of_Heaven/Vanilla_Ice), [EoH Hol Horse](https://jojowiki.com/Eyes_of_Heaven/Hol_Horse), [ASBR Pet Shop](https://jojowiki.com/All-Star_Battle_R/Pet_Shop), [EoH Pet Shop](https://jojowiki.com/Eyes_of_Heaven/Pet_Shop), [EoH Mariah](https://jojowiki.com/Eyes_of_Heaven/Mariah), [EoH N'Doul](https://jojowiki.com/Eyes_of_Heaven/N%27Doul), [Manoir de DIO](https://jojowiki.com/DIO%27s_Mansion).
- Autres : [StrategyWiki, ASB Hol Horse](https://strategywiki.org/wiki/JoJo%27s_Bizarre_Adventure:_All_Star_Battle/Hol_Horse), [Animated Character Database (Iggy)](https://xianb.fandom.com/wiki/File:Scene_105774.png), [Giant Bomb, ASB](https://www.giantbomb.com/games/3030-38897/), [Gematsu, roster d'EoH](https://gematsu.com/2015/07/jojos-bizarre-adventure-eyes-heaven-adds-shigekiyo-akira-yoshikage), [OneEsports, roster d'ASBR](https://www.oneesports.gg/gaming/jojos-bizarre-adventure-all-star-battle-r).
- Lu à travers les résultats de recherche : jojowiki.com ne répondait pas en direct depuis l'environnement. **Tout chiffre ou nom marqué « à vérifier » doit être relu sur la fiche** avant d'écrire un kit.
