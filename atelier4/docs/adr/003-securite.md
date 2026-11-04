# ADR 003 : sécurité de l'API LogiAI

## Décision 1 : où transmettre la clé (en-tête, URL ou corps) ?

- **Votre choix :** Nous avons choisi de transmettre la clé API dans l'en-tête HTTP `X-API-Key`. Cette méthode permet de séparer les informations d'authentification des données de livraison. La clé est vérifiée par la fonction `verify_api_key()` avant d'autoriser l'accès aux routes protégées.

- **Ce que l'autre option ferait perdre :** Transmettre la clé dans l'URL risquerait de l'exposer dans l'historique du navigateur, les journaux du serveur ou les liens partagés. La transmettre dans le corps de la requête mélangerait les données métier avec l'authentification et compliquerait sa réutilisation sur plusieurs routes.

- **Résultat :** Une clé absente ou invalide provoque une réponse HTTP `401`. La route `/v1/predict` accepte les clés utilisateur et administrateur. La route `/v1/model-info` est réservée à l'administrateur et renvoie `403` pour un utilisateur non autorisé. La route `/health` reste publique.

## Décision 2 : quelles origines autoriser (CORS) ? Une liste précise ou « * » ?

- **Votre choix :** Nous avons choisi une liste précise d'origines autorisées : `http://localhost:5500` et `http://127.0.0.1:5500`. La configuration utilise `CORSMiddleware` de FastAPI et autorise les méthodes `GET`, `POST`, `OPTIONS` ainsi que les en-têtes `Content-Type` et `X-API-Key`.

- **Ce que l'autre option ferait perdre :** Utiliser `*` autoriserait les pages de toutes les origines à lire les réponses de l'API dans les conditions permises par le navigateur. Cela supprimerait la restriction d'origine prévue pour notre application web. Une liste précise permet de mieux contrôler les sites autorisés à communiquer avec l'API.

- **Résultat :** Les tests CORS confirment que les origines sur le port `5500` sont autorisées, tandis que `http://localhost:5501` est refusée par la politique CORS. CORS ne remplace pas l'authentification : les clés API restent obligatoires sur les routes protégées.

## Validation

La sécurité a été vérifiée avec des tests automatisés couvrant l'authentification, les autorisations et CORS.

**Résultats finaux :**
- 57 tests réussis avec `pytest`.
- Aucune erreur avec `ruff check .`.
- Formulaire web fonctionnel avec une prédiction affichée.

## Conséquences

Cette solution est simple et adaptée à un projet pédagogique. Les clés sont configurées par des variables d'environnement chargées depuis un fichier `.env` non destiné à être versionné. Pour un déploiement réel, il faudrait également utiliser HTTPS afin de protéger les clés pendant leur transmission.