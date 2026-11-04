
"""Tester les valeurs limites et les entrées malformées.

Le projet contient 2 bugs volontaires dans les bornes.
Ces tests doivent permettre de les détecter.
"""

import pytest

# (champ, valeur envoyée, code HTTP attendu)
CAS_LIMITES = [
    # 1. Distance : de 1 à 1000 km
    ("distance_km", 1, 200),
    ("distance_km", 0.9, 422),
    ("distance_km", 1000, 200),
    ("distance_km", 1001, 422),

    # 2. Poids : de 0.1 à 3500 kg
    ("poids_kg", 0.1, 200),
    ("poids_kg", 0, 422),
    ("poids_kg", 3500, 200),
    ("poids_kg", 3500.1, 422),

    # 3. Heure de départ : de 0 à 23
    ("heure_depart", 0, 200),
    ("heure_depart", -1, 422),
    ("heure_depart", 23, 200),
    ("heure_depart", 24, 422),
    ("heure_depart", 11.5, 422),

    # 4. Pluie : de 0 à 100 mm
    ("pluie_mm", 0, 200),
    ("pluie_mm", -0.1, 422),
    ("pluie_mm", 100, 200),
    ("pluie_mm", 100.1, 422),

    # 5. Trafic : de 0 à 10
    ("trafic_index", 0, 200),
    ("trafic_index", -0.1, 422),
    ("trafic_index", 10, 200),
    ("trafic_index", 10.1, 422),

    # 6. Nombre d'arrêts : de 0 à 15
    ("nb_arrets", 0, 200),
    ("nb_arrets", -1, 422),
    ("nb_arrets", 15, 200),
    ("nb_arrets", 16, 422),
    ("nb_arrets", 2.5, 422),

    # 7. Type de véhicule
    ("type_vehicule", "moto", 200),
    ("type_vehicule", "fourgon", 200),
    ("type_vehicule", "camion", 200),
    ("type_vehicule", "avion", 422),
]


@pytest.mark.parametrize("champ, valeur, attendu", CAS_LIMITES)
def test_valeurs_limites(
    client, headers_user, livraison_valide, champ, valeur, attendu
):
    livraison_valide[champ] = valeur

    r = client.post(
        "/v1/predict",
        json=livraison_valide,
        headers=headers_user
    )

    assert r.status_code == attendu, (
        f"{champ}={valeur} : "
        f"attendu {attendu}, obtenu {r.status_code}"
    )
