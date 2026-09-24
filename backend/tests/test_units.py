import pytest
from backend.services.units import convert_units, are_units_compatible, normalize_unit


def test_normalize_unit():
    assert normalize_unit(" KG ") == "kg"
    assert normalize_unit("ML") == "ml"
    assert normalize_unit("") == ""


def test_mass_conversions():
    assert convert_units(1.4, "kg", "g") == 1400.0
    assert convert_units(180, "g", "kg") == 0.18
    assert convert_units(500, "g", "g") == 500.0


def test_volume_conversions():
    assert convert_units(1.5, "l", "ml") == 1500.0
    assert convert_units(40, "ml", "l") == 0.04


def test_incompatible_units():
    with pytest.raises(ValueError):
        convert_units(100, "g", "ml")


def test_are_units_compatible():
    assert are_units_compatible("kg", "g") is True
    assert are_units_compatible("ml", "l") is True
    assert are_units_compatible("kg", "ml") is False
