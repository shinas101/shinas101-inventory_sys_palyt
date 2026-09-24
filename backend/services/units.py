MASS_CONVERSIONS = {
    "g": 1.0,
    "kg": 1000.0,
    "mg": 0.001,
}

VOLUME_CONVERSIONS = {
    "ml": 1.0,
    "l": 1000.0,
}

COUNT_CONVERSIONS = {
    "pcs": 1.0,
    "pc": 1.0,
    "unit": 1.0,
    "piece": 1.0,
    "pieces": 1.0,
}


def normalize_unit(unit):
    if not unit or not isinstance(unit, str):
        return ""
    return unit.strip().lower()


def get_dimension(unit):
    u = normalize_unit(unit)
    if u in MASS_CONVERSIONS:
        return "mass", MASS_CONVERSIONS[u]
    if u in VOLUME_CONVERSIONS:
        return "volume", VOLUME_CONVERSIONS[u]
    if u in COUNT_CONVERSIONS:
        return "count", COUNT_CONVERSIONS[u]
    raise ValueError(f"Unknown unit: '{unit}'")


def are_units_compatible(unit1, unit2):
    try:
        dim1, _ = get_dimension(unit1)
        dim2, _ = get_dimension(unit2)
        return dim1 == dim2
    except ValueError:
        return False


def convert_units(amount, from_unit, to_unit):
    if amount < 0:
        raise ValueError("Amount cannot be negative")

    u1 = normalize_unit(from_unit)
    u2 = normalize_unit(to_unit)

    if u1 == u2:
        return round(float(amount), 4)

    dim1, factor1 = get_dimension(u1)
    dim2, factor2 = get_dimension(u2)

    if dim1 != dim2:
        raise ValueError(f"Cannot convert between {dim1} ({from_unit}) and {dim2} ({to_unit})")

    base_value = float(amount) * factor1
    converted_value = base_value / factor2
    return round(converted_value, 4)
