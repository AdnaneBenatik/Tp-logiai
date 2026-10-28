# Compte rendu : TP API LogiAI

**Noms :** ............................  **Groupe :** ........

## 1. Environnement et premiers tests
- Sortie de `python -m pytest` au départ (après `python -m logiai.train`, avant d'écrire `schemas.py` et `predict()`) :

```
FAILED tests/test_api.py::test_predict_valide_renvoie_200 - assert 422 == 200
FAILED tests/test_api.py::test_predict_forme_de_la_reponse - AssertionError: ...
FAILED tests/test_api.py::test_predict_probabilite_entre_0_et_1 - KeyError: 'probabilite_retard'
FAILED tests/test_api.py::test_predict_trajet_risque_plus_eleve_que_trajet_facile
FAILED tests/test_api.py::test_modele_absent_renvoie_503 - assert 422 == 503
5 failed, 8 passed
```

- Pourquoi certains tests qui attendent un 422 passent-ils déjà, alors que rien n'est écrit ?

  Le schéma de départ ne déclare que `distance_km` et il est configuré avec `extra="forbid"`. Toute requête de test contient aussi `poids_kg`, `pluie_mm`, `type_vehicule`, etc. : ce sont des champs inconnus pour le schéma, donc Pydantic renvoie 422 pour tous. Les tests « pluie impossible », « véhicule inconnu » ou « champ manquant » passent donc **pour la mauvaise raison** : la requête est refusée parce que le schéma est incomplet, pas parce que la valeur est invalide. Seul le test de la distance négative passe pour la bonne raison (`ge=1`). Après avoir écrit le schéma, les 13 tests passent et les 422 sont désormais dus aux vraies bornes.

## 2. Mon schéma
| Variable | Min | Max | Pourquoi |
|---|---|---|---|
| distance_km | 1 | 1000 | Donné. Moins de 1 km n'est pas une livraison planifiée ; au-delà de 1000 km on sort du transport routier régional (le jeu de données va jusqu'à 800 km). |
| poids_kg | 0.1 | 5000 | Un colis a un poids strictement positif (100 g minimum). 5000 kg couvre largement un camion de livraison (max 3000 kg dans les données) avec une marge. |
| heure_depart | 0 | 23 | Heure d'une journée : entier de 0 à 23. |
| pluie_mm | 0 | 100 | Pas de pluie négative. 100 mm est un cumul extrême (orage exceptionnel) ; 500 mm est physiquement irréaliste. |
| trafic_index | 0 | 10 | Échelle définie par le contrat : 0 = fluide, 10 = saturé. |
| nb_arrets | 0 | 30 | Entier positif ou nul. 30 est très au-dessus des 12 arrêts maximum observés, sans accepter de valeurs absurdes. |
| type_vehicule | — | — | `Literal["moto", "fourgon", "camion"]` : seules les trois valeurs connues du modèle. |

## 3. Ma fonction predict()
```python
@app.post("/v1/predict", response_model=PredictionOut)
def predict(livraison: Livraison):
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé : lancez `python -m logiai.train` puis redémarrez l'API.",
        )
    return PredictionOut(**predictor.predict(livraison.model_dump()))
```

## 4. Quatre requêtes
(Résultats obtenus avec le client de test FastAPI, mêmes appels que `/docs`.)

| Requête | Code obtenu | Pourquoi |
|---|---|---|
| livraison normale | **200** — `{"probabilite_retard": 0.732, "alerte": true, "seuil": 0.4, "model_version": "1.0"}` | Les données respectent le schéma, le modèle est chargé. 0.732 ≥ 0.4, donc alerte. |
| distance_km = -5 | **422** — `distance_km : Input should be greater than or equal to 1` | Pydantic refuse la valeur avant que `predict()` ne s'exécute (borne `ge=1`). |
| type_vehicule = "avion" | **422** — `type_vehicule : Input should be 'moto', 'fourgon' or 'camion'` | Valeur hors du `Literal` autorisé. |
| modèle absent (dossier `models/` supprimé, API relancée) | **503** — `{"detail": "Modèle non chargé : lancez python -m logiai.train puis redémarrez l'API."}` ; `/health` renvoie `model_loaded: false` | La requête est valide mais le serveur ne peut pas y répondre : `state` ne contient pas de predictor. |

## 5. Questions de compréhension
1. **Pourquoi charge-t-on le modèle au démarrage et pas à chaque requête ?** Lire et désérialiser `model.joblib` coûte du temps (disque + reconstruction de l'objet). Le faire une fois dans `lifespan` garde chaque requête rapide, et le modèle est partagé en mémoire par toutes les requêtes. Cela permet aussi de détecter un modèle manquant dès le démarrage.
2. **Qui écrit le contrôle « pluie <= 100 », et où est-il écrit ?** C'est nous, dans le schéma Pydantic (`logiai/api/schemas.py`), avec `Field(ge=0, le=100)`. FastAPI l'applique automatiquement avant d'appeler `predict()` ; la logique métier n'a pas à le refaire.
3. **Différence entre 422 et 503 ?** 422 : la requête du client est mal formée ou invalide (erreur côté client, inutile de réessayer telle quelle). 503 : la requête est correcte mais le service n'est pas en état de la traiter (ici, modèle absent) ; c'est une erreur côté serveur, qui peut disparaître après correction ou redémarrage.
4. **Pourquoi `/v1/predict` plutôt que `/predict` ?** Pour versionner le contrat. Si on change les champs ou la réponse, on publie `/v2/predict` et les clients existants continuent d'utiliser `/v1` sans casser.
5. **Que se passerait-il si la distance était déclarée `int` ?** Une distance décimale comme `12.5` serait refusée en 422 (nombre avec partie fractionnaire), alors que c'est une valeur réaliste (le jeu de données contient des distances à une décimale). Seules des valeurs entières ou comme `120.0` passeraient.

## 6. Décision : modèle absent
**Option A — répondre 503 (choix actuel).** L'API démarre, `/health` signale `model_loaded: false` et `/v1/predict` répond 503 avec un message explicite. On y gagne : le service reste observable (documentation, santé), un déploiement partiel est diagnostiquable, et on peut corriger sans arrêter les autres routes. On y perd : le service a l'air « vivant » alors qu'il ne sert à rien ; si personne ne surveille `/health`, l'erreur n'apparaît qu'à la première requête d'un utilisateur.

**Option B — refuser de démarrer.** Le problème est visible immédiatement au déploiement (échec rapide), et aucun client n'est jamais servi par une API sans modèle. On y perd : tout le service tombe, y compris `/health` et la documentation, ce qui complique le diagnostic et peut provoquer des redémarrages en boucle dans un orchestrateur.

Dans ce TP, 503 + `/health` reste le compromis le plus pratique ; en production, on peut combiner les deux (échec au démarrage et sonde de santé).

## 7. Lien de la pull request
(à compléter après votre `git push` et l'ouverture de la PR : ......................................)
