from app.core.zarc_classifier import classify_soil
from app.core.water_balance import (
    calculate_ad, 
    obter_parametros_cultura
)
from datetime import date, timedelta

def test_soil_classification():
    assert classify_soil(40.0, 20.0) == "Argiloso"
    assert classify_soil(25.0, 70.0) == "Médio"
    assert classify_soil(10.0, 80.0) == "Arenoso"

def test_water_balance_math():
    ad = calculate_ad(0.38, 0.22)
    assert round(ad, 2) == 0.16
    # CAD em 40cm seria 0.16 * 40 * 10 = 64.0
    cad = ad * 40.0 * 10.0
    assert cad == 64.0

def test_fao56_parameters_soja():
    # Soja 10 DAP
    kc, z = obter_parametros_cultura("soja", 10)
    assert kc == 0.40
    assert z == 5.0 + (0.8 * 10) # 13.0
    
    # Soja 80 DAP
    kc, z = obter_parametros_cultura("soja", 80)
    assert kc == 1.15
    assert z == 60.0 # Limit

def test_fao56_parameters_milho():
    # Milho 10 DAP
    kc, z = obter_parametros_cultura("milho", 10)
    assert kc == 0.30
    assert z == 15.0
    
    # Milho 90 DAP
    kc, z = obter_parametros_cultura("milho", 90)
    assert kc == 1.20
    assert z == 80.0
