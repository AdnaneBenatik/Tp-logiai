import argparse
import json
from pathlib import Path

from logiai.predict import Predictor


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Prédire le risque de retard d'une livraison"
    )
    parser.add_argument("fichier", help="Fichier JSON de la livraison")
    args = parser.parse_args(argv)

    fichier = Path(args.fichier)

    if not fichier.exists():
        print(f"Erreur : fichier introuvable : {fichier}")
        return 1

    with fichier.open("r", encoding="utf-8") as f:
        donnees = json.load(f)

    predictor = Predictor()
    resultat = predictor.predict(donnees)

    probabilite = resultat["probabilite_retard"]
    statut = "ALERTE" if resultat["alerte"] else "OK"

    print(f"Probabilité de retard : {probabilite:.0%} ({statut})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())