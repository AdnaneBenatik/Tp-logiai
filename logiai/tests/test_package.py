
from importlib.metadata import entry_points, version


def test_package_installe():
    assert version("logiai")


def test_commande_declaree():
    noms = {
        e.name
        for e in entry_points(group="console_scripts")
    }
    assert "logiai-predict" in noms
