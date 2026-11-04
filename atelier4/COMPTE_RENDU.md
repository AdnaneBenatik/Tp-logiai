# Compte rendu : tester, sécuriser et appeler l'API LogiAI

**Noms :** BENATIK Adnane
**Groupe :** 5IAD/G3

## 1. Casser son API (activité 1)

Nous avons réalisé cinq tests de requêtes invalides pour vérifier la robustesse de l'API.

| Cas | Requête (corps ou URL) | Prévu | Obtenu |
|---|---|---|---|
| Champ manquant | Requête `/v1/predict` sans `poids_kg` | 422 | 422 |
| Valeur absurde | `poids_kg` avec une valeur très élevée | 422 | 422 |
| Texte au lieu d'un nombre | `distance_km` avec une chaîne non numérique | 422 | 422 |
| Champ en trop | Requête avec un champ supplémentaire non autorisé | 422 | 422 |
| Mauvaise route | Appel d'une route inexistante | 404 | 404 |

**Une requête acceptée alors qu'elle devait être refusée ?**

Oui. Lors des tests de limites, deux valeurs incorrectes étaient initialement acceptées : `heure_depart = 24` et `nb_arrets = -1`. Ces anomalies ont ensuite été corrigées.

Les cinq tests de requêtes invalides ont réussi.

## 2. Les 2 bugs (activité 2)

| Bug | Test qui l'a révélé | Comportement avant | Correction |
|---|---|---|---|
| 1 | Test avec `heure_depart = 24` | Réponse 200 au lieu de 422 | Ajouter `ge=0, le=23` dans `schemas.py` |
| 2 | Test avec `nb_arrets = -1` | Réponse 200 au lieu de 422 | Ajouter `ge=0, le=15` dans `schemas.py` |

**Sortie de `python -m pytest` à la fin de l'activité 2 :**

```text
43 passed, 1 warning
```

Après la réalisation de toutes les activités, le résultat final est :

```text
57 passed, 1 warning in 2.74s
```

La vérification de qualité du code donne :

```text
All checks passed!
```

## 3. La clé API (sprint 1)

Nous avons sécurisé l'API avec l'en-tête HTTP `X-API-Key`.

**Ma fonction `verify_api_key()` :**

```python
def verify_api_key(x_api_key: str | None = Header(default=None)) -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Clé API manquante",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if _egal(x_api_key, config.ADMIN_KEY):
        return "admin"

    if _egal(x_api_key, config.API_KEY):
        return "user"

    raise HTTPException(
        status_code=401,
        detail="Clé API invalide",
        headers={"WWW-Authenticate": "ApiKey"},
    )
```

La fonction `_egal()` utilise `secrets.compare_digest()` pour comparer les clés.

| Requête | Code obtenu |
|---|---|
| `/v1/predict` sans clé | 401 |
| `/v1/predict` fausse clé | 401 |
| `/v1/predict` clé utilisateur | 200 |
| `/v1/model-info` clé utilisateur | 403 |
| `/v1/model-info` clé administrateur | 200 |
| `/health` sans clé | 200 |

Les tests de sécurité ont confirmé ces comportements : **11 tests réussis**.

Nous avons également configuré les variables `LOGIAI_API_KEY` et `LOGIAI_ADMIN_KEY` dans un fichier `.env`.

La route `/health` a confirmé que la configuration était active :

```json
{
  "status": "ok",
  "model_loaded": true,
  "auth_configured": true
}
```

**Preuve que `.env` n'est pas dans Git :**

À compléter avec la sortie de `git status --short --untracked-files=all` et la vérification de `git check-ignore atelier4/.env`, exécutées depuis la racine du dépôt.

Le fichier `.env` ne doit pas être publié dans le dépôt GitHub.

## 4. Le client web (sprint 2)

Nous avons créé une interface HTML permettant de saisir les caractéristiques d'une livraison et d'obtenir une prédiction.

**Mon `fetch` :**

```javascript
async function appelerApi(livraison, cle) {
  const reponse = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": cle
    },
    body: JSON.stringify(livraison)
  });

  return {
    status: reponse.status,
    corps: await reponse.json()
  };
}
```

**Ce qui s'affiche :**

- **Livraison testée :** « Probabilité de retard : 73.2 %. Alerte : livraison à risque. »
- **Pluie de 500 mm :** à tester et à noter selon la réponse réelle de l'API.
- **Fausse clé API :** le client est conçu pour afficher « Clé API absente ou invalide. » lorsque le serveur répond 401. Test manuel à confirmer.

Le bouton « Évaluer » est désactivé pendant le calcul et réactivé ensuite. Les erreurs 401, 403, 422 et 503 sont gérées.

**Expérience CORS :**

La configuration autorise uniquement :

- `http://localhost:5500`
- `http://127.0.0.1:5500`

Les trois tests CORS automatisés ont réussi, y compris le refus de `http://localhost:5501`.

**Page servie sur le port 5501 :** expérience réelle et message de la console F12 à compléter.

`curl` fonctionne quand même, car CORS est une politique appliquée par les navigateurs. `curl` n'applique pas ces restrictions, mais doit toujours respecter l'authentification de l'API.

**Où voit-on la clé dans F12 ?**

Dans les outils de développement du navigateur, onglet **Network / Réseau**, en sélectionnant la requête `/v1/predict`, puis dans les en-têtes de la requête sous `X-API-Key`.

Cette information est sensible et ne doit pas apparaître dans une capture d'écran partagée sans être masquée.

## 5. Questions de compréhension

**1. Quelle différence entre 401, 403 et 422 ?**

- **401 Unauthorized :** la clé API est absente ou invalide.
- **403 Forbidden :** la clé est valide, mais l'utilisateur n'a pas les droits nécessaires.
- **422 Unprocessable Entity :** les données envoyées ne respectent pas le schéma attendu.

**2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ?**

Pour éviter de divulguer des informations secrètes. Les clés sont plac