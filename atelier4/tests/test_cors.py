
"""Tests CORS de l'API LogiAI."""


def test_cors_localhost_5500_autorise(client):
    """Le navigateur sur localhost:5500 est autorisé."""
    reponse = client.options(
        "/v1/predict",
        headers={
            "Origin": "http://localhost:5500",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-api-key",
        },
    )

    assert reponse.status_code == 200
    assert (
        reponse.headers["access-control-allow-origin"]
        == "http://localhost:5500"
    )


def test_cors_127_0_0_1_5500_autorise(client):
    """Le navigateur sur 127.0.0.1:5500 est autorisé."""
    reponse = client.options(
        "/v1/predict",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-api-key",
        },
    )

    assert reponse.status_code == 200
    assert (
        reponse.headers["access-control-allow-origin"]
        == "http://127.0.0.1:5500"
    )


def test_cors_localhost_5501_refuse(client):
    """Le navigateur sur localhost:5501 est refusé."""
    reponse = client.options(
        "/v1/predict",
        headers={
            "Origin": "http://localhost:5501",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-api-key",
        },
    )

    assert reponse.status_code == 400
    assert "access-control-allow-origin" not in reponse.headers
