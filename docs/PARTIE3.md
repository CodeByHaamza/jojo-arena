# Partie 3 : notes et idées pour la suite

Notes du 24/10/2026. **Ce sont des propositions** ; le [GDD](GDD.md) fait foi. Les coups et les designs viennent des fiches JoJo Wiki et des listes de coups d'ASBR et d'EoH (sources en bas).

Ce qui n'est pas sûr est marqué **à vérifier**. Une source manque, se contredit, ou n'a été lue qu'à travers un résumé de recherche : jojowiki.com est bloqué par le réseau de l'environnement. On ne comble pas le trou, on relit la fiche avant d'écrire le kit.

## Décisions du 24/10/2026

| Question | Décision |
| --- | --- |
| Persos secondaires (D'Arby, Alessi, J. Geil, Boingo, Nukesaku) | **Événements d'arène**, pas jouables |
| Décor effacé par Vanilla Ice | **Pas tranché**. Proposition : il revient, mais deux fois plus lentement que les caisses, pour que l'arène reste jouable sur un long round |
| Le vol | **Une hauteur fixe** : le sprite monte de quelques pixels, l'ombre reste au sol et rétrécit. C'est ce qui se lit le mieux en vue de dessus et ça ne demande pas de physique en 3D (détail dans « Mécaniques ») |
| DIO boit le sang de Joseph | **Oui, en cinématique** : un éveil majeur (voir « Interactions ») |
| Par qui on commence | **Avdol** |

## Où on en est

- **Jouables** : Jotaro, Kakyoin, Polnareff, DIO.
- **Arène** : Le Caire, rue de nuit.
- Le moteur **sait déjà** faire : Stand on/off, mode contrôle, temps arrêté, pièges, projectiles (`count`, `ring`), visée libre, saisies inbloquables, Hamon, vampire et soleil, `stance_cycle`, éveil, objets à lancer.
- Il **ne sait pas encore** faire : brûlure, vol, invisibilité, états qui s'accumulent, décor effacé, et Stand + Hamon ensemble.

---

## 1. Le design de la partie 3 : les règles

1. **Silhouette d'abord.** Araki a donné une tête d'oiseau à Magician's Red pour que les silhouettes des héros côte à côte ne se ressemblent pas (fiche Magician's Red). On suit la même règle : à 48 px, chaque perso et chaque Stand se reconnaît à sa forme avant ses couleurs.
2. **Les couleurs de l'anime**, comme pour les quatre premiers persos redessinés. Les couleurs changent d'un média à l'autre : on prend la section « Color Schemes » de la fiche, ligne anime, et on la cite dans `looks/`.
3. **Les motifs qui racontent.** Le camp de DIO porte des cœurs : la ceinture de DIO et de Vanilla Ice, les motifs de The World et de Cream. Ça se lit à l'écran et c'est fidèle.
4. **Style A** : contour #17121f, 2 à 3 tons, petit highlight, environ 48 px de haut pour un humain.
   - **Iggy** et **Pet Shop** sont des animaux : leur taille réelle doit se voir. Proposition : Iggy dans une case 64 × 64, mais environ 22 px de haut.
5. **Chaque fiche `looks/` commence par ses sources**, la section « Apparence » du wiki, comme le veut le CLAUDE.md.

---

## 2. Personnages : design et moveset

Les movesets suivent nos touches :

- **léger** : trois coups qui s'enchaînent ;
- **lourd**, et lourd avec une direction ;
- **spécial**, et spécial avec une direction ;
- **contre** ;
- les mêmes emplacements **Stand sorti** ;
- **HHA** (1 barre) et **GHA** (2 barres, en cinématique).

Le nom officiel du coup est entre guillemets. La forme de la hitbox suit la règle du CLAUDE.md.

### Muhammad Avdol (Magician's Red) : le premier à faire

**Rôle** : zoner de feu, mi-distance, contrôle de zone.

**Design** (JoJo Wiki, « Apparence ») :

- Avdol :
  - grand, peau foncée, carrure moyenne à lourde ;
  - sourcils épais, menton large, deux cicatrices identiques sur les joues ;
  - long manteau ou robe, avec des manches au poignet puis au coude selon les moments, et une écharpe autour du cou.
  - **À vérifier** : sa coiffure et sa coiffe. La recherche ne les a pas sorties, et on ne les dessine pas de mémoire.
- Magician's Red :
  - tête de phénix, haut du corps très musclé ;
  - jambes à plumes parfois prises dans les flammes ;
  - mains à griffes, bracelets sombres aux deux poignets ;
  - inspiré de l'Horus de la trilogie Nikopol d'Enki Bilal.
- **Silhouette** : un grand manteau qui tombe droit, à côté d'un Stand à tête d'oiseau. Personne d'autre dans le roster n'a cette paire.

**Moveset** (ASBR, sauf mention) :

| Emplacement | Coup | Forme proposée |
| --- | --- | --- |
| Léger ×3 | Coups normaux d'Avdol (les lourds d'ASBR font déjà sortir Magician's Red) | `circle`, petite `reach` |
| Lourd | Magician's Red frappe le temps d'un coup (« Stand qui surgit », mécanique existante) | `circle`, `reach` moyenne, brûlure |
| Spécial | **« Crossfire Hurricane »** : un ankh de feu qui vole tout droit | `projectile`, brûlure |
| Spécial + direction | **« Crossfire Hurricane Variation »** : l'ankh piégé. Plus on tient, plus il éclate loin (ASBR : 30 l'ankh, 65 l'éruption) | piège posé à distance réglable |
| Saisie | **« Red Bind! »** : des cordes de feu sortent de sa main, puis Magician's Red fait exploser l'adversaire | `shape = "line"`, `radius` large, saisie |
| Stand : spécial | **« I'll burn you to cinders! »** (skill Stand d'ASBR ; **à vérifier** : ce qu'elle fait exactement) | à fixer après lecture |
| Stand : spécial + direction | **« Flaming Detector »** : le détecteur de vie, des flammes qui montrent où est l'adversaire | pas de dégâts, révèle l'invisible 2 s |
| Stand : lourd | **« HELL 2 U! »** (skill Stand d'ASBR ; **à vérifier**) | à fixer après lecture |
| Contre | **« Now's my chance! »** (skill Stand d'ASBR ; **à vérifier** : est-ce bien un contre ?) | contre |
| **HHA** | **« Give me four wishes instead! »** : Magician's Red donne un coup de pied devant lui | `circle`, `reach` moyenne |
| **GHA** | **Crossfire Hurricane Special** : un anneau d'ankhs de feu, puis une rafale | `projectile` avec `count` et `ring` qui se referme, puis rafale |

- **Mécanique nouvelle** : la **brûlure**, des dégâts sur la durée. Elle s'accumule (voir « Mécaniques »).
- **À vérifier** : le nom de la GHA. Une page ASBR l'appelle *Special*, une autre range le coup à 3 boutons sous *Variation*.

### Joseph Joestar âgé (Hermit Purple + Hamon)

**Rôle** : grappler longue portée, trickster.

**Design** :

- Joseph :
  - main gauche **prothèse mécanique**, faite par Stroheim après que Kars la lui a coupée ;
  - chapeau ajouté par rapport à la fin de la partie 2 ;
  - tenue de l'anime : chemise à col sous un pull col V, pantalon kaki, gants.
  - **À vérifier** : les couleurs exactes (section « Color Schemes »), et la barbe.
- Hermit Purple :
  - plusieurs ronces violettes couvertes d'épines, qui sortent de ses mains ;
  - violettes dans tous les médias, d'où son nom.
- **Silhouette** : le seul Croisé avec un chapeau et un Stand qui n'a pas de corps. Les ronces suffisent à le reconnaître.

**Moveset** (ASBR) :

| Emplacement | Coup | Forme proposée |
| --- | --- | --- |
| Léger ×3 | Coups normaux, Hamon si la jauge en a | `circle` |
| Lourd | **« Hamon Overdrive! »** | `circle`, `reach` 15-25 : c'est vraiment un coup de poing |
| Spécial | **« Hermit Purple! »** : les ronces attrapent et tirent l'adversaire vers lui, puis la suite dépend de la touche | `line` longue, attire |
| Spécial + direction | **Coal Tar** : Hermit Purple apporte un bidon de goudron et le renverse, un piège au sol (**à vérifier** : le nom exact de la skill) | piège en flaque, ralentit |
| Stand : spécial | Hamon dans les ronces : la saisie à distance devient Hamon (double dégâts sur DIO et Vanilla Ice) | `line`, `hamon` |
| Contre | **HHA** ci-dessous | — |
| **HHA** | Contre : il charge son Hamon ; s'il est frappé, il met l'adversaire au sol, saute et l'écrase avec Hermit Purple. **À vérifier** : le nom, « Battle Apprenticeship » ou « Age of Fighting » selon la source | contre |
| **GHA** | Hermit Purple ligote l'adversaire, puis un coup de tranchant chargé de Hamon. **À vérifier** : le nom, « Hermit Purple and Hamon! » ou une variante | `line`, saisie, `hamon` |

- **Mécanique** : le style Stand + Hamon, en composant `stance_toggle` et `hamon` (rien de neuf à inventer).
- **Clin d'œil** : « Ta prochaine réplique sera... » existe déjà chez Joseph jeune, à reprendre.
- On garde les clackers pour Joseph jeune : dans ASBR, ce sont ses coups, pas ceux du vieux Joseph.

### Iggy (The Fool)

**Rôle** : mobilité, petit et dur à toucher.

**Design** :

- Iggy :
  - Boston Terrier noir et blanc, avec du blanc sur le front, le museau, le ventre et les pattes ;
  - Araki a choisi cette race pour son noir et blanc, simple à dessiner.
- The Fool :
  - fait de sable, donc visible par tout le monde ;
  - plumes sur la tête, câbles sur les bras, dents pointues ;
  - pattes de chien à l'avant, **roues** à l'arrière ;
  - tête et mains argentées, corps gris foncé.
  - **À vérifier** : ce dernier détail vient de l'annonce d'une figurine Medicos, pas du wiki.
- **Silhouette** : minuscule à côté d'un gros Stand à roues. Le contraste de taille *est* le perso.

**Moveset** (ASBR) :

| Emplacement | Coup | Forme proposée |
| --- | --- | --- |
| Léger ×3 | Morsures et coups de pattes | `circle`, petite `reach` |
| Lourd + direction | **Sand Dome** : un dôme qui bloque tout, même l'inbloquable, sauf les saisies. Il dure tant qu'on tient, contre de la Heart Heat | garde spéciale |
| Spécial | **Hang Glider** : des ailes de sable. Stand rentré, il descend lentement ; Stand sorti, il reste à hauteur fixe jusqu'à l'adversaire ou au mur | vol |
| Spécial + direction | **« DIO Doppelganger »** : un leurre de sable, sa riposte Stand rentré | leurre |
| Saisie | **« Get your ass in gear! »** : The Fool tient l'adversaire, Iggy prend appui dessus et le repousse des quatre pattes | saisie |
| Stand : spécial | **« Get outta here! »** : anti-air qui **renvoie les projectiles** | `circle` devant, renvoie |
| Stand : spécial + direction | **« Too easy! »** (**à vérifier** : son effet) | à fixer |
| Stand : lourd | **« Aerial Chain Beat »** (**à vérifier**) | à fixer |
| **HHA** | **À vérifier** : la recherche ne l'a pas trouvée | — |
| **GHA** | **« Serves you right! »** : une immense vague de sable devant lui. The Fool roue l'adversaire de coups, et Iggy finit en le mordant au nez. Stand rentré seulement | gros `radius` en cône devant lui |

### Vanilla Ice (Cream)

**Rôle** : assassin, invisible, inbloquable, lent à viser.

**Design** :

- Vanilla Ice :
  - grand, musclé, cheveux longs et ondulés aux épaules ;
  - un **diadème à médaillon en cœur** sur le front, des boucles d'oreilles en cœur ;
  - un justaucorps sous un gilet de cuir sombre ouvert et sans manches ;
  - une **ceinture au cœur comme DIO** ;
  - un pan de tissu dans le dos jusqu'aux mollets, comme une cape.
- Cream :
  - très grand, visage de crâne, masque en cagoule de bourreau avec deux cornes ;
  - motifs de cœur, comme The World ;
  - pas de lèvres, les dents toujours visibles (fiche française) ;
  - quand il s'avale lui-même, il devient une **sphère de vide**.
- **Silhouette** : la cape longue et le diadème. Cream est le plus grand Stand de la partie.

**Moveset** (ASBR) :

| Emplacement | Coup | Forme proposée |
| --- | --- | --- |
| Léger ×3 | Coups normaux (Stand rentré) | `circle` |
| Spécial | Le vide : Cream s'avale avec Ice et devient une sphère, invisible et intouchable. **Pas de verrouillage** : on la dirige à la main (visée libre). Il sort la tête pour voir | invisibilité, déplacement guidé |
| Spécial + direction | Cream plonge dans le sol au-dessus de lui et ressort pour attaquer (sa skill depuis le sol dans ASBR, environ 1/5 de jauge) | `circle`, inbloquable |
| Stand : spécial | **« Once and for all! »** : sa seule spéciale Stand sorti. Elle coûte de la jauge de Stand et frappe aussi fort qu'une GHA | `line` courte, inbloquable |
| **HHA** | **« The great void rises! »** | inbloquable (ASBR) |
| **GHA** | **« Miasma of the Void »** (ASBR ; « Spirit of Emptiness » dans ASB) : la trace qui efface tout | `shape = "line"`, `reach` qui traverse l'arène, inbloquable |

- **Faiblesse fidèle à ASBR** : ses spéciales sont lentes et en ligne droite. Il faut les garder lisibles.
- **Nature `vampire`** : DIO l'a fait vampire, et le soleil l'achève face à Polnareff.

### Hol Horse (Emperor)

**Rôle** : tireur qui bouge, buffe ses tirs.

**Design** :

- Hol Horse :
  - grand, athlétique, fossettes, menton à fossette ;
  - cheveux clairs aux épaules et longs favoris (la fiche française parle de mulet) ;
  - **chapeau de cow-boy à large bord**, avec deux longues lanières fines qui pendent ;
  - vêtements clairs sur un maillot sombre ;
  - un long haut sans manches fendu sur les côtés, comme un poncho ;
  - jambières de cuir (chaps) sur le pantalon, bottes d'équitation à éperons ;
  - une cigarette.
- Emperor :
  - un revolver compliqué, un peu futuriste ;
  - un cadre métallique sur un long canon, et un barillet en dessous qui n'est relié à rien ;
  - argenté dans l'anime (doré dans l'OVA).
- **Silhouette** : le chapeau et le poncho. Le seul cow-boy de la partie.

**Moveset** (ASBR) :

| Emplacement | Coup | Forme proposée |
| --- | --- | --- |
| Léger ×3 | Coups de crosse et de pied | `circle` |
| Spécial | Tir d'Emperor : la balle **se pilote pendant qu'elle vole**. Elle tourne en l'air et suit la visée libre (souris ou stick droit), comme le pouvoir d'Emperor dans la fiche. Hol Horse peut continuer à courir pendant ce temps (décidé le 24/10) | `projectile` piloté |
| Spécial + direction | **« Gun beats sword »** : il fait tourner Emperor, et sa prochaine skill marquée ☆ fait plus de coups et de dégâts | buff |
| Lourd | **« You lose, loser! »** | à fixer après lecture |
| Lourd + direction | **« Even my bullets are part of my Stand! »** | à fixer après lecture |
| Contre | **« Come get us! »** (**à vérifier** : est-ce un contre ?) | à fixer |
| Assist | **« You're up, J. Geil! »** : il **lance une bouteille d'eau n'importe où dans l'arène** (au curseur). Elle éclate en flaque, et la flaque devient un piège de J. Geil : Hanged Man frappe depuis le reflet quand l'adversaire passe dessus. Dans ASBR, la skill se pose aussi dans une flaque d'eau ; la bouteille vient de sa DHA d'EoH (décidé le 24/10) | bouteille lancée → piège-flaque |
| Passif | **« Hol Horse loves the ladies! »** : passif contre les adversaires femmes (**à vérifier** : son effet exact) | règle de match |
| **HHA** | **« Eat this! »** | rafale guidée |
| **GHA** | **« Hol Horse is gonna kill ya! »**, avec la mise en scène de la DHA d'EoH : il lance une bouteille et la fait éclater d'une balle ; Hanged Man surgit dans les éclats, poignarde l'adversaire à l'épaule et l'immobilise ; Hol Horse tire la balle finale | `projectile`, cinématique |

### Mariah (Bastet)

**Rôle** : piégeuse, fragile, gagne avec le temps.

**Design** :

- Mariah :
  - belle femme à la peau foncée, cheveux courts clairs ;
  - un **blouson à capuche à manches courtes**, façon Chaperon rouge ;
  - un haut décolleté, une mini-jupe taille haute, des bas sombres satinés.
  - Selon une autre fiche : yeux jaunes, cheveux gris, haut court jaune, chaussures rouges à nœuds, gants marron, lunettes de soleil, capuche rouge.
  - **À vérifier** dans « Color Schemes » : la variante bordeaux et rose existe aussi.
- Bastet :
  - une **prise électrique** avec un câble visible en dessous, posable sur n'importe quelle surface ;
  - dans le manga : blanche à bord doré, fil rouge.
- **Silhouette** : la capuche rouge. Le Stand est un objet au sol, pas un corps.

**Moveset** (ASBR et EoH) :

| Emplacement | Coup | Forme proposée |
| --- | --- | --- |
| Léger ×3 | EoH : pas de vrai combo de corps à corps, un **fil de métal qui paralyse** | `line` courte, paralyse |
| Spécial | **Bastet** : posée d'un claquement de doigts devant elle, au sol ou **sur un mur**. Piège fixe et inbloquable, qui électrocute et magnétise | piège |
| Spécial + direction | Trois couteaux qui suivent la cible et traversent toute l'arène sans disparaître (ASBR) | `projectile` `count = 3`, guidé, attiré par le magnétisme |
| Saisie | Bastet tient l'adversaire, puis un tonneau vole et le frappe. La jauge de magnétisme se remplit de moitié environ | saisie |
| Lourd | Le fil électrique : il tombe, file vers l'adversaire, l'électrocute et le repousse (EoH) | `line`, attiré vers la cible |
| **HHA** | Ses dégâts montent avec le niveau de magnétisme (**à vérifier** : le nom) | dépend du niveau |
| **GHA** | La pluie de métal sur la cible magnétisée (GDD). **À vérifier** : le nom et la mise en scène d'ASBR | gros `radius` sur la cible |

- **Mécanique nouvelle** : la jauge de magnétisme sur l'adversaire, Lv 1, Lv 2, puis Lv MAX. Ses coups et sa HHA gagnent en force à chaque niveau.

### Pet Shop (Horus)

**Rôle** : zoner de glace qui vole.

**Design** :

- Pet Shop :
  - un faucon, bec puissant, serres acérées, très bonne vue ;
  - **un chaperon de fauconnerie orné et une écharpe**.
  - **À vérifier** : ce détail vient de la fiche polonaise.
- Horus : la glace.
  - **À vérifier** : sa forme propre, que la recherche n'a pas sortie.
- **Silhouette** : un oiseau en l'air, son ombre loin dessous.

**Moveset** (ASBR) :

- 800 PV, Horus toujours sorti.
- La touche Stand fait passer du **sol** au **vol**. En vol, pas de garde, pas de saisie, pas de pose.
- Il retombe s'il est touché, ou quand il réussit sa HHA ou sa GHA.

| Emplacement | Coup | Forme proposée |
| --- | --- | --- |
| Léger ×3 | Pics de glace sous des angles différents | `projectile` court |
| Lourd | Trois pics de glace devant lui (au sol), ou trois vers le sol en diagonale (en vol) | `projectile` `count = 3` |
| Lourd + direction | Horus fait jaillir un grand pic de glace du sol devant lui | `circle` au sol |
| Spécial | Glace tenue, puis lancée (L/M/H, aussi en vol) | `projectile` |
| Spécial + direction | Le piqué (dive), puis le stalactite | `line` en piqué, puis piège |
| Skills (noms ASBR) | **« Ca-Caw! »**, **« Cawww! »**, **« Caw caw! »**, **« Screech! »**, **« Nee gee gee gee! »** (**à vérifier** : quel nom va avec quel coup) | — |
| **HHA** | Il cloue l'adversaire au sol sous un gros bloc de glace, puis en lâche un second | gros `radius` sur la cible |
| **GHA** | Perché sur Horus, il enferme l'adversaire dans la glace (**à vérifier** : la suite de la cinématique) | saisie, gel |
| Bonus EoH | Le missile de glace énorme et inbloquable au-dessus de sa tête ; la cible est paralysée | `projectile` lent, inbloquable |

### N'Doul (Geb)

**Rôle** : sniper aveugle. Il n'est que dans EoH.

**Design** :

- N'Doul :
  - aveugle, athlétique, taille moyenne ;
  - cheveux sombres en bataille, yeux vides presque fermés ;
  - **gilet rayé** sur un débardeur, brassards ;
  - un **drap** contre le soleil du Sahara, un bandeau, deux créoles ;
  - une **canne segmentée avec trois joyaux sur la poignée**.
- Geb :
  - de l'eau qu'il façonne à distance, un jet qui tranche ;
  - une main à griffes dans *Diamond Records*.
- **Silhouette** : assis, la canne plantée devant lui. Son Stand est une flaque.

**Moveset** (EoH) :

- Il ne verrouille jamais.
- Pas de dash à tête chercheuse : il envoie Geb devant lui, jusqu'à 4 fois, et ses skills partent de là où est Geb.

| Emplacement | Coup | Forme proposée |
| --- | --- | --- |
| Léger ×2 | Debout : deux coups de canne, le second met au sol | `circle` |
| Lourd | Estoc de canne à deux mains qui repousse | `line` courte |
| Lourd + direction | Coup de pommeau qu'on charge, qui fait s'écrouler | `circle`, charge |
| Stand (assis = **mode contrôle**) : léger ×5 | Geb : estoc, fouet à l'horizontale, fouet en diagonale vers le haut, griffe en main, griffe qui repousse | `line` et `circle` depuis Geb |
| Stand : spécial | Geb glisse et frappe d'estoc (son dash) | `line` |
| Stand : lourd | Geb en main qui frappe et fait voler l'adversaire | `circle`, gros recul |
| **HHA / GHA** | **À vérifier** : la DHA d'EoH n'est pas décrite dans les résultats. Le GDD propose une main d'eau géante qui jaillit sous la cible | gros `radius` sous la cible |

- **Mécanique nouvelle** : **l'ouïe** (voir « Mécaniques »).

---

## 3. Mécaniques nouvelles

| Mécanique | Qui s'en sert | Règle proposée |
| --- | --- | --- |
| **Brûlure** | Avdol, puis Esidisi, Red Hot Chili Pepper | Des piles de brûlure, avec des dégâts par seconde qui s'éteignent. Une esquive en éteint une pile |
| **État qui s'accumule** | Mariah (magnétisme), Avdol (brûlure) | Un composant générique dans `combat/` : niveau, durée, plafond. Rien de JoJo dedans |
| **Vol** | Iggy, Pet Shop, Kars ultime, Aerosmith | Une hauteur fixe (sprite levé, ombre au sol plus petite). En l'air : au-dessus des pièges au sol et des flaques, touché par les projectiles et par les coups marqués « anti-air ». Pas de garde en vol (règle de Pet Shop dans ASBR) |
| **Invisibilité** | Vanilla Ice, Wamuu (Wind Suit) | Le sprite disparaît, seule une légère distorsion trahit le perso. Intouchable dans le vide. Révélé par le Flaming Detector, Hermit Purple, et le radar d'Aerosmith plus tard |
| **Décor effacé** | Vanilla Ice | Un objet effacé disparaît : pas de débris, pas d'objet à lancer. Retour plus lent que les caisses (en attente de ta décision) |
| **Ouïe** | N'Doul | Courir, frapper et dasher font du bruit et le montrent à N'Doul ; marcher en fait peu ; rester immobile rend invisible pour Geb |
| **Stand + Hamon** | Joseph âgé, et peut-être Jonathan dans d'autres jeux | Composer `stance_toggle` et `hamon`, pas de nouveau style |

---

## 4. Interactions spéciales (`combat/interactions.py`)

| Situation | Règle proposée |
| --- | --- |
| **DIO boit le sang de Joseph** (décidé) | Un éveil majeur en **cinématique**. Le Power Up de DIO se remplit en drainant un Joestar avec sa saisie, et à fond face à Joseph âgé. Éveillé : temps arrêté plus long et régénération. **À vérifier** : les durées, dans la fiche DIO et la fin de la partie 3 |
| Avdol ou Joseph contre un invisible | Flaming Detector ou Hermit Purple : Vanilla Ice révélé 2 s |
| Vanilla Ice au soleil | Nature `vampire` : le soleil et le Hamon le blessent |
| Hamon de Joseph contre DIO | Double dégâts, régénération bloquée (règle Hamon qui existe) |
| Jotaro éveillé | +1 s de temps arrêté (déjà prévu, à brancher sur `[awakening]`) |
| Toile de Kakyoin contre temps arrêté | Si DIO arrête le temps alors que la toile de 20 m est posée, tous les fils cassent |
| Iggy contre Pet Shop | Rivalité : une intro à eux, et un petit bonus de dégâts pour Iggy (chiffre à mesurer avec `jojo-balance`) |
| Vol contre pièges au sol | Iggy en planeur et Pet Shop passent au-dessus des fils, du goudron et de Bastet au sol (pas de Bastet sur un mur) |
| Geb contre l'immobile | Un adversaire qui ne bouge pas n'est pas visé par Geb ; c'est ce qui rend le combat contre N'Doul unique |

---

## 5. Arènes et leurs événements

Les persos secondaires deviennent **des événements d'arène** (décidé).

| Arène | Éléments interactifs | Événement (perso secondaire) | Pour qui |
| --- | --- | --- | --- |
| **Manoir de DIO** (GDD) | Rideaux à arracher (soleil), escalier, faux couloirs. Sortie de ring par le trou du mur : brûlé pour les vampires, chute pour les autres (le Situation Finish d'ASBR) | **Nukesaku** tombe du plafond et frappe, sans limite (le gimmick d'ASBR) ; **Kenny G**, des faux couloirs (**à vérifier** dans la fiche Tenore Sax) | Vanilla Ice, Iggy, Pet Shop, DIO |
| **Désert égyptien** (GDD) | Sable mou qui ralentit, mirages, point d'eau rare | **Tempête de sable** : 10 s de vue réduite | N'Doul, Iggy |
| **Pont du Caire** (ASBR) | Garde-corps qui casse, bord qui fait tomber | — | Jotaro contre DIO |
| **Ruelle de Calcutta** | Flaques et vitrines à casser | **J. Geil** frappe depuis les reflets | Hol Horse, Polnareff |
| **Pont du cargo** | Conteneurs à lancer, cordages | **Forever**, l'orang-outan, plie le décor (**à vérifier** dans la fiche Strength) | Avdol, Joseph |
| **Casino de D'Arby** | Tables à renverser | **D'Arby** : le pari d'âme avant le round, une barre de HH en jeu | Mode fun |
| **Le Caire, rue de nuit** (existe) | — | **Boingo** : une case de BD prédit un endroit, et une caisse y tombe 3 s plus tard (**à vérifier** dans la fiche Thoth) ; **Alessi**, son ombre qui rajeunit celui qu'elle touche pendant quelques secondes | Tout le monde |

Chaque événement suit sa fiche JoJo Wiki **avant** d'être codé, comme un perso.

---

## 6. Modes

- **Arcade partie 3 : le voyage vers l'Égypte**. Japon, Hong Kong, Singapour, Inde, Pakistan, Égypte, puis le manoir contre DIO. L'arcade existe déjà, il faut l'ordre.
- **Défis** : « fais exploser un ankh piégé », « attrape avec Hermit Purple puis Hamon », « sors du vide et touche avec Cream ».
- **Cartes de tarot** : chaque Stand vaincu donne sa carte au glossaire.
- **2v2 des Croisés** plus tard (GDD).

---

## 7. Ordre

1. **Avdol** : brûlure et état qui s'accumule, ankh piégé. ← on commence ici
2. **Joseph âgé** : Stand + Hamon.
3. **Manoir de DIO**, avec Nukesaku et les rideaux.
4. **Iggy** : le vol.
5. **Pet Shop** : le vol réutilisé.
6. **Vanilla Ice** : invisibilité, décor effacé.
7. **Hol Horse** (J. Geil à Calcutta), **Mariah**, **N'Doul** avec le désert.
8. **Éveils** de Jotaro et de DIO (la cinématique du sang).

Pour chaque perso : la liste du CLAUDE.md, une **fiche `looks/` écrite depuis l'« Apparence »** et relue avant les sprites, puis `jojo-balance`.

---

## Sources

JoJo Wiki (lu à travers les résultats de recherche, le site étant bloqué ici) :

- Avdol : [ASBR Avdol](https://jojowiki.com/All-Star_Battle_R/Muhammad_Avdol), [Avdol](https://jojowiki.com/Mohammed_Avdol), [Magician's Red](https://jojowiki.com/Magician's_Red), [Crossfire Hurricane Special](https://jojowiki.com/Crossfire_Hurricane_Special).
- Joseph âgé : [ASBR Old Joseph](https://jojowiki.com/ASBR/Old_Joseph_Joestar), [EoH Old Joseph](https://jojowiki.com/Eyes_of_Heaven/Old_Joseph_Joestar), [Joseph Joestar](https://jojowiki.com/Joseph_Joestar), [Hermit Purple (fr)](https://jojowiki.com/Hermit_Purple/fr), [Hermit Purple (pt)](https://jojowiki.com/Hermit_Purple/pt-br).
- Iggy : [Iggy](https://jojowiki.com/Iggy), [The Fool](https://jojowiki.com/The_Fool), [ASBR Iggy](https://jojowiki.com/All-Star_Battle_R/Iggy).
- Vanilla Ice : [Vanilla Ice](https://jojowiki.com/Iced), [Cream](https://jojowiki.com/Cream), [ASBR Vanilla Ice](https://jojowiki.com/All-Star_Battle_R/Vanilla_Ice).
- Hol Horse : [Hol Horse (fr)](https://jojowiki.com/Hol_Horse/fr), [Emperor (fr)](https://jojowiki.com/Emperor/fr), [ASBR Hol Horse](https://jojowiki.com/All-Star_Battle_R/Hol_Horse), [EoH Hol Horse](https://jojowiki.com/Eyes_of_Heaven/Hol_Horse).
- Mariah : [Mariah](https://jojowiki.com/Mariah), [Bastet](https://jojowiki.com/Bastet), [ASBR Mariah](https://jojowiki.com/All-Star_Battle_R/Mariah), [EoH Mariah](https://jojowiki.com/Eyes_of_Heaven/Mariah).
- Pet Shop : [Pet Shop](https://jojowiki.com/Pet_Shop), [Pet Shop (pl)](https://jojowiki.com/Pet_Shop/pl), [ASBR Pet Shop](https://jojowiki.com/All-Star_Battle_R/Pet_Shop), [EoH Pet Shop](https://jojowiki.com/Eyes_of_Heaven/Pet_Shop).
- N'Doul : [N'Doul](https://jojowiki.com/N'Doul), [EoH N'Doul](https://jojowiki.com/Eyes_of_Heaven/N'Doul), [Diamond Records N'Doul](https://Jojowiki.com/Diamond_Records/N%27Doul).
- Arène : [Manoir de DIO](https://jojowiki.com/DIO%27s_Mansion).

Listes de coups :

- [StrategyWiki, ASBR Moves](https://strategywiki.org/wiki/JoJo%27s_Bizarre_Adventure:_All_Star_Battle_R/Moves), [StrategyWiki, ASB Hol Horse](https://strategywiki.org/wiki/JoJo%27s_Bizarre_Adventure:_All_Star_Battle/Hol_Horse).
- Mizuumi : [Avdol](https://mizuumi.wiki/w/JoJo's_Bizarre_Adventure:_All-Star_Battle_R/Muhammad_Avdol), [Old Joseph](https://mizuumi.wiki/w/JoJo's_Bizarre_Adventure:_All-Star_Battle_R/Old_Joseph_Joestar), [Iggy](https://mizuumi.wiki/w/JoJo's_Bizarre_Adventure:_All-Star_Battle_R/Iggy), [Mariah](https://mizuumi.wiki/w/JoJo's_Bizarre_Adventure:_All-Star_Battle_R/Mariah), [combos de Pet Shop](https://mizuumi.wiki/w/JoJo's_Bizarre_Adventure:_All-Star_Battle_R/Pet_Shop/Combos).
- Fandom : [All-Star Battle, Old Joseph](https://jojos-all-star-battle.fandom.com/wiki/Old_Joseph), [EoH, N'Doul](https://eyes-of-heaven-jjba.fandom.com/wiki/N'Doul).
- NamuWiki, noms traduits automatiquement, à prendre avec prudence : [Old Joseph ASBR](https://en.namu.wiki/w/%EC%A3%A0%EC%85%89%20%EC%A3%A0%EC%8A%A4%ED%83%80(3%EB%B6%80)/%EC%A3%A0%EC%A3%A0%EC%9D%98%20%EA%B8%B0%EB%AC%98%ED%95%9C%20%EB%AA%A8%ED%97%98%20%EC%98%AC%20%EC%8A%A4%ED%83%80%20%EB%B0%B0%ED%8B%80%20R).

Autres :

- [Animated Character Database, Iggy](https://animated-character-database.fandom.com/wiki/Iggy) ;
- [Toy People, figurine The Fool](https://www.toy-people.com/en/?p=114507) ;
- [Breezewiki, Mariah](https://breezewiki.discard.no/villains/wiki/Mariah) ;
- [Giant Bomb, ASB](https://www.giantbomb.com/games/3030-38897/) ;
- rosters : [Gematsu, EoH](https://gematsu.com/2015/07/jojos-bizarre-adventure-eyes-heaven-adds-shigekiyo-akira-yoshikage), [OneEsports, ASBR](https://www.oneesports.gg/gaming/jojos-bizarre-adventure-all-star-battle-r).
