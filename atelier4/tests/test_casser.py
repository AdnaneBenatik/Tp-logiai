
"""Casser son API : tester les requêtes invalides."""

import pytest

VALID = {
    "distance_km": 120.0,
    "poids_kg": 450.0,
    "heure_depart": 17,
    "pluie_mm": 8.0,
    "trafic_index": 7.5,
    "nb_arrets": 4,
    "type_vehicule": "camion",
}

SANS_POIDS = {k: v for k, v in VALID.items() if k != "poids_kg"}

CAS_REFUSES = [
    ("valeur absurde", "/v1/predict",
     {**VALID, "poids_kg": 99999}, 422),

    ("champ manquant", "/v1/predict",
     SANS_POIDS, 422),

    ("texte au lieu d'un nombre", "/v1/predict",
     {**VALID, "distance_km": "bonjour"}, 422),

    ("champ en trop", "/v1/predict",
     {**VALID, "couleur": "rouge"}, 422),

    ("mauvaise route", "/v1/inconnue",
     VALID, 404),
]


@pytest.mark.parametrize(
    "description, url, corps, attendu", CAS_REFUSES
)
def test_requete_refusee(
    client, headers_user, description, url, corps, attendu
):
    r = client.post(url, json=corps, headers=headers_user)
    assert r.status_code == attendu, description
