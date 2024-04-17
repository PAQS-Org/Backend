def calculate_unit_price(quantity):
    if quantity > 100000 or quantity < 200:
        return "out of bounds"
    elif quantity <= 100000:
        unit = 0.01
    elif quantity >= 50000:
        unit = 0.02
    elif quantity >= 10000:
        unit = 0.04
    elif quantity >= 5000:
        unit = 0.06
    elif quantity >= 1000:
        unit = 0.08
    elif quantity >= 500:
        unit = 0.10
    elif quantity >= 200:
        unit = 0.15
    elif quantity <= 200:
        unit = 0.20
    else:
        unit = 0

    total = quantity * unit
    return (total, quantity, unit)
