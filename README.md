# JoJo Arena

Fan game **gratuit, open source et non commercial** : un arena fighter 1v1 en temps réel, en pixel art vu de dessus, avec un grand roster des 9 parties de JoJo's Bizarre Adventure.

> **Fan game non officiel.** Ce projet est gratuit, sans but lucratif, et n'est affilié ni à Hirohiko Araki, ni à Shueisha, ni à David Production, ni à CyberConnect2. JoJo's Bizarre Adventure et toutes les marques citées appartiennent à leurs propriétaires respectifs.

## État du projet

Prototype en cours (Vague 0 : moteur). Les personnages sont pour l'instant des mannequins génériques. Le game design complet est dans [docs/GDD.md](docs/GDD.md).

## Installation (développement)

Il faut Python 3.12 ou plus récent.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Lancer le jeu

```powershell
.\.venv\Scripts\python.exe -m jojo_arena
```

## Licence

Code sous licence [MIT](LICENSE).
