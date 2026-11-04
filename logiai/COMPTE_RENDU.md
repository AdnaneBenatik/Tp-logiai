# Compte rendu : TP API LogiAI — Atelier 3

**Noms :** Adnane BENATIK
**Groupe :** 5IAD/G3

## 1. Environnement et premiers tests

Après l'installation des dépendances et l'entraînement du modèle avec :

```bash
python -m logiai.train
python -m pytest
```

Nous avons obtenu les résultats suivants avant de compléter `schemas.py` et `predict()` :

```text
FAILED tests/test_api.py::test_predict_valide_renvoie_200 - assert 422 == 200
FAILED tests/test_api.py::test_predict_forme_de_la_reponse
FAILED tests/test_api.py::test_predict_probabilite_entre_0_et_1
FAILED tests/test_api.py::test_predict_trajet_risque_plus_eleve_que_trajet_facile
FAILED tests/test_api.py::test_modele_absent_renvoie_503

5 failed, 8 passed
```

**Pourquoi certains tests qui attendent un 422 passent-ils déjà, alors que rien n'est écrit ?**

Le schéma de départ ne déclare que `distance_km` et utilise `extra="forbid"`.

Les requêtes contiennent pourtant d'autres champs comme `poids_kg`, `pluie_mm` et `type_vehicule`. Pydantic les considère donc comme inconnus et renvoie une erreur HTTP 422.

Certains tests passent ainsi pour la mauvaise raison : la requête est refusée parce que le schéma est incomplet, et non parce que les données sont incorrectes.

Après avoir complété le schéma et la fonction de prédiction, les 13 tests de l'Atelier 3 passent.

## 2. Mon schéma

| Variable | Minimum | Maximum | Justification |
|---|---|---|---|
| `distance_km` | 1 | 1000 | Une livraison planifiée couvre au moins 1 km. La limite supérieure reste adaptée au transport routier régional. |
| `poids_kg` | 0.1 | 5000 | Un colis doit avoir un poids positif. La limite laisse une marge pour les livraisons lourdes. |
| `heure_depart` | 0 | 23 | Une heure de départ doit être comprise entre 0 et 23. |
| `pluie_mm` | 0 | 100 | Une quantité de pluie ne peut pas être négative. |
| `trafic_index` | 0 | 10 | L'indice de trafic suit une échelle de 0 à 10. |
| `nb_arrets` | 0 | 30 | Le nombre d'arrêts doit être entier et positif ou nul. |
| `type_vehicule` | — | — | Seules les valeurs `moto`, `fourgon` et `camion` sont autorisées. |

Les validations sont définies dans `logiai/api/schemas.py` avec les contraintes Pydantic `Field()` et `Literal`.

## 3. Ma fonction `predict()`

```python
@app.post("/v1/predict", response_model=PredictionOut)
def predict(livraison: Livraison):
    predictor = state.get("predictor")

    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Modèle non chargé : lancez "
                "'python -m logiai.train' puis redémarrez l'API."
            ),
        )

    return PredictionOut(
        **predictor.predict(livraison.model_dump())
    )
```

Cette fonction reçoit une livraison validée par Pydantic.

Elle vérifie ensuite si le modèle est chargé. Si le modèle est absent, elle renvoie une erreur HTTP 503. Sinon, elle utilise le modèle pour calculer la probabilité de retard et retourne une réponse structurée.

## 4. Quatre requêtes

Les résultats suivants correspondent aux essais indiqués dans le compte rendu de l'Atelier 3.

| Requête | Code obtenu | Explication |
|---|---|---|
| Livraison normale | **200** | Les données sont valides et le modèle est chargé. |
| `distance_km = -5` | **422** | La distance ne respecte pas la borne minimale de 1 km. |
| `type_vehicule = "avion"` | **422** | Le véhicule n'appartient pas aux trois catégories autorisées. |
| Modèle absent | **503** | Le serveur ne dispose pas du modèle nécessaire à la prédiction. |

**Exemple de réponse pour une livraison normale :**

```json
{
  "probabilite_retard": 0.732,
  "alerte": true,
  "seuil": 0.4,
  "model_version": "1.0"
}
```

La probabilité de retard est de **73,2 %**. Comme elle dépasse le seuil de 40 %, l'API déclenche une alerte.

**Exemple pour une distance négative :**

```text
422 — distance_km : Input should be greater than or equal to 1
```

**Exemple pour un véhicule inconnu :**

```text
422 — type_vehicule : Input should be 'moto', 'fourgon' or 'camion'
```

**Exemple pour un modèle absent :**

```text
503 — Modèle non chargé.
```

Dans ce dernier cas, `/health` indique également `model_loaded: false`.

## 5. Questions de compréhension

**1. Pourquoi charge-t-on le modèle au démarrage et pas à chaque requête ?**

Le chargement du modèle depuis `model.joblib` prend du temps. En le chargeant une seule fois au démarrage avec `lifespan`, nous évitons de répéter cette opération pour chaque requête.

Cela améliore les performances et permet de réutiliser le modèle chargé en mémoire.

**2. Qui écrit le contrôle « pluie ≤ 100 », et où est-il écrit ?**

Nous définissons cette contrainte dans `logiai/api/schemas.py` avec Pydantic :

```python
pluie_mm: float = Field(ge=0, le=100)
```

FastAPI applique automatiquement cette validation avant d'exécuter la fonction `predict()`.

**3. Quelle différence entre 422 et 503 ?**

- **422 :** la requête contient des données invalides. Le problème vient du client.
- **503 :** la requête peut être correcte, mais le service n'est pas disponible pour la traiter, par exemple parce que le modèle est absent.

**4. Pourquoi `/v1/predict` plutôt que `/predict` ?**

Le préfixe `/v1` permet de versionner l'API.

Si le contrat change dans le futur, nous pourrons créer `/v2/predict` tout en conservant `/v1/predict` pour les anciens clients.

**5. Que se passerait-il si la distance était déclarée `int` ?**

Une distance décimale comme `12.5` serait refusée par la validation Pydantic.

Utiliser `float` est plus adapté, car les distances réelles peuvent comporter des décimales.

## 6. Décision : modèle absent

Nous avons étudié deux possibilités.

### Option A — Répondre HTTP 503 (choix retenu)

L'API démarre même si le modèle est absent.

La route `/health` indique que le modèle n'est pas chargé et `/v1/predict` renvoie HTTP 503.

**Avantages :**

- Le serveur reste accessible.
- L'état du modèle peut être vérifié.
- La documentation de l'API reste disponible.
- Le diagnostic du problème est plus simple.

**Inconvénient :**

Le serveur semble fonctionner alors que la prédiction n'est pas disponible.

### Option B — Refuser de démarrer

L'application s'arrête immédiatement si le modèle est absent.

**Avantages :**

- Le problème est détecté dès le démarrage.
- Aucun client ne peut utiliser une API sans modèle.

**Inconvénients :**

- Le service entier devient inaccessible.
- Les routes de diagnostic ne sont plus disponibles.
- Le déploiement peut provoquer des redémarrages répétés.

### Décision finale

Pour cet atelier, nous retenons **l'option A : retourner HTTP 503 et conserver `/health` accessible**.

Cette solution facilite le diagnostic et convient au contexte pédagogique du projet LogiAI.

## 7. Lien de la pull request

**Dépôt GitHub :** https://github.com/AdnaneBenatik/Tp-logiai

**Lien de la pull request :** À compléter après la publication de la branche et la création de la pull request.

## Conclusion

L'Atelier 3 nous a permis de comprendre comment exposer un modèle de machine learning à travers une API REST avec FastAPI.

Nous avons appris à valider les données avec Pydantic, gérer les erreurs HTTP, charger un modèle au démarrage et vérifier le comportement de l'API avec des tests automatisés.

**Résultat de l'Atelier 3 : 13 tests réussis après correction du schéma et de la fonction de prédiction.**