# Prompt à coller dans Claude Code — Vague 0

Lis `CLAUDE.md` puis `docs/GDD.md` en entier. Ensuite, réalise la **Vague 0 (moteur)** du GDD.

## Objectif

Un prototype jouable en **J1 contre J2 en local** (clavier + manette) sur l'arène « Le Caire, rue de nuit », avec deux persos **placeholders génériques** (aucun perso JoJo dessiné), qui se lance avec `python -m jojo_arena` et se compile en `.exe`.

## À livrer

1. **Structure du repo** selon `CLAUDE.md` : `pyproject.toml` (pygame-ce, pytest, ruff, pyinstaller en dev), `README.md` en français (description, installation, lancement, mention fan game non officiel), `LICENSE` (MIT, au nom du propriétaire du repo), `.gitignore` Python.
2. **Rendu** : surface interne 480 × 270, agrandie sans lissage à l'échelle entière max, bandes noires sinon. Boucle 60 FPS à pas de temps fixe.
3. **Arène du Caire** : rectangle fermé aux coins arrondis, sol de pavés ternes en tuiles (généré en code), quelques étals cassables comme obstacles, cadre bleu nuit sombre autour.
4. **Deux persos placeholders 48 px** : un mannequin générique style A (contour noir #17121f, 2-3 tons, highlight), deux couleurs différentes, avec ombre portée elliptique. Animations minimales : idle, marche (8 directions), attaque légère, attaque lourde, dash, dégâts, KO.
5. **Combat** (valeurs dans un fichier de données) :
   - 1000 PV, rounds configurables (1, 3 ou 5 gagnants), timer 99 s ;
   - attaque légère, lourde, spéciale placeholder (un projectile simple) ;
   - garde (réduit 80 % des dégâts, jauge de garde, Guard Break = stun 1,5 s) ;
   - esquive/dash avec frames d'invincibilité, Stylish Evade (esquive au dernier moment = ralenti bref) ;
   - **clash** : deux attaques qui se touchent au même instant → les deux joueurs martèlent la touche d'attaque 3 s, barre de duel à l'écran, le perdant prend le coup et est éjecté ;
   - jauge Heart Heat à 3 barres (remplie en frappant et en encaissant), HHA à 1 barre en placeholder ;
   - knockback et wall bounce contre les bords de l'arène ;
   - touche Stand : pour l'instant, un simple toggle on/off qui change la couleur d'aura du placeholder et le moveset (2 sets d'attaques placeholder), pour poser l'architecture.
6. **HUD** : barres de vie, garde, HH, timer, compteur de rounds, écran de victoire de round et de match.
7. **Contrôles** : mapping par défaut du GDD pour J1 au clavier, J2 à la manette (et un 2e mapping clavier pour tester à deux sur un seul clavier). Fichier de config rebindable.
8. **Menu minimal** : écran titre → choix du nombre de rounds → combat → revanche ou retour.
9. **Tests pytest** sur la logique de combat (dégâts, garde, guard break, clash, rounds, timer).
10. **GitHub Action** `.github/workflows/release.yml` : sur un tag `v*`, build Windows avec PyInstaller (un seul .exe, assets inclus) et attache le .exe à une Release.

## Contraintes

- Respecte toutes les règles de `CLAUDE.md`, en particulier : **aucune ligne Co-Authored-By ni mention d'IA dans les commits**, et **aucun asset JoJo dessiné**.
- `engine/` et `combat/` ne contiennent aucune référence à JoJo.
- Commence par me proposer un plan (liste de fichiers + ordre), attends mon OK, puis code étape par étape avec un commit par étape.
- À la fin : explique-moi en français comment lancer le jeu, comment lancer les tests, et comment publier une release (créer le tag).
