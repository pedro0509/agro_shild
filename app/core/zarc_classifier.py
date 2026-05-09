def classify_soil(clay_percent: float, sand_percent: float) -> str:
    """
    Classifica o solo segundo a regra do ZARC:
    Tipo 3 (Argiloso): Teor de argila >= 35%
    Tipo 2 (Médio): Teor de argila entre 15% e 35% E teor de areia < 85%
    Tipo 1 (Arenoso): Teor de argila < 15% OU (Teor de argila entre 15% e 35% com areia >= 85%)
    """
    if clay_percent >= 35.0:
        return "Argiloso"
    elif 15.0 <= clay_percent < 35.0:
        if sand_percent < 85.0:
            return "Médio"
        else:
            return "Arenoso"
    else:
        return "Arenoso"
