# Travailler avec des agents

Le projet est assez gros pour qu'une seule session d'IA perde le fil : 22 000 lignes, un
GDD de 400 lignes qui fait foi, 90 fichiers de données, et des règles d'architecture qui
ne se devinent pas. Ce document dit comment découper le travail pour que ça tienne.

## Le principe

**Un superviseur décide et vérifie, des agents spécialisés font.** Le superviseur ne
code pas : il lit le GDD, découpe en tranches jouables, distribue, puis **exige des
preuves** avant de croire que c'est fait.

Chaque agent a un périmètre de fichiers. Deux agents ne touchent jamais au même fichier
en même temps — c'est la seule règle qui empêche le chaos quand ils tournent en parallèle.

## L'équipe

Les définitions sont dans `.claude/agents/`.

| Agent | Périmètre | Ce qu'il ne fait jamais |
| --- | --- | --- |
| **jojo-lead** | aucun fichier : il découpe, lance, vérifie, rapporte | écrire du code de jeu |
| **jojo-kit** | `characters/*.toml`, `looks/`, `roster.toml`, `lore/` | toucher à `combat/` ou `engine/` |
| **jojo-engine** | `engine/`, `combat/` | citer JoJo, importer pygame dans `combat/`, mettre une valeur en dur |
| **jojo-ui** | `ui/` | modifier la simulation, écrire un nom de touche en dur |
| **jojo-balance** | `rules.toml`, `characters/*.toml` (valeurs) | changer une valeur dans le code |
| **jojo-art** | `looks/`, `assets/`, `tools/icons/` | dessiner à la main par-dessus le générateur |
| **jojo-lore** | `docs/GDD.md`, `lore/` | inventer un fait ; copier un asset sous licence |
| **jojo-qa** | rien : il mesure et il rapporte | corriger autre chose qu'une faute évidente |

### Pourquoi ce découpage

Il suit les frontières **déjà présentes dans le code**, pas une organisation inventée :
`engine/` ne connaît pas JoJo, `combat/` ne connaît pas pygame, `ui/` lit la simulation
sans l'écrire, les persos sont des données. Un agent par frontière, et les règles
d'architecture deviennent des règles d'agents — donc elles tiennent toutes seules.

## Les tranches

Une tranche est quelque chose que tu peux **jouer** à la fin, jamais une couche. « Le
kit de Wamuu » est une tranche. « Les fichiers TOML de la partie 2 » n'en est pas une.

Exemple, ajouter Wamuu :

```
jojo-lore   -> ce qu'est Wamuu, ses techniques, ses stats, ses répliques  (docs/GDD.md)
                                   |
         +-------------------------+-------------------------+
         v                                                   v
jojo-kit  -> kit, roster, glossaire, test            jojo-art -> silhouette, planche
         +-------------------------+-------------------------+
                                   v
jojo-balance -> mesure et ajuste        jojo-qa -> make check, captures, démo
                                   v
jojo-lead   -> vérifie les preuves, commit, rapporte
```

`jojo-kit` et `jojo-art` tournent **en parallèle** (fichiers différents).
`jojo-balance` attend, parce qu'il mesure ce que les deux ont produit.

## Les preuves exigées

Le superviseur ne croit pas un agent sur parole. Pour chaque type de travail :

| Type | Preuve |
| --- | --- |
| Mécanique de jeu | un test qui **échoue** sans le changement |
| Perso | `make training P2=<id>`, une capture, et le test du kit |
| Écran | la capture, regardée (`make screens`) |
| Équilibrage | les taux de victoire avant / après |
| Correction de bug | le replay ou le test qui reproduisait, maintenant vert |

Sans preuve, le travail repart une fois, en nommant exactement ce qui manque.

## Les skills

Les skills sont les procédures que **tout le monde** suit, agents ou humain. Elles sont
dans `.claude/skills/` et s'invoquent par leur nom.

| Skill | Quand |
| --- | --- |
| `new-fighter` | ajouter un perso : les 9 fichiers, dans l'ordre qui évite de tout refaire |
| `balance-pass` | « X est trop fort », « ce coup est imparable » : mesurer avant de toucher |
| `repro-replay` | un bug signalé : transformer un replay en test qui échoue |
| `cut-release` | publier une version : vérifications, versions, tag, ce que fait la CI |

Une skill vaut mieux qu'une explication répétée : elle est lue au bon moment, par celui
qui fait le travail, et elle vieillit avec le projet.

### Skills à écrire ensuite

- **`new-stage`** : une arène (données, rendu, objets, cycle jour/nuit, musique).
- **`new-cutscene`** : un ultime en cinématique (caméra, découpage, retour au combat).
- **`sound-design`** : les bruitages sont synthétisés dans le code — comment en ajouter.
- **`playtest-report`** : faire jouer quelqu'un et en tirer des changements utiles.

## Ce que l'humain garde pour lui

Trois choses qu'aucun agent ne peut faire à ta place :

1. **Décider ce que le jeu est.** Le GDD fait foi parce que c'est toi qui l'écris.
2. **Juger le ressenti.** Un coup peut passer tous les tests et être mou. Seules des
   mains le savent.
3. **Dire quand c'est assez bien.** Un agent polira indéfiniment.
