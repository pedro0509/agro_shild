from datetime import date, timedelta
import pandas as pd
from typing import List, Dict, Any, Tuple

def calculate_ad(vwc33: float, vwc1500: float, tipo_solo: str = "Médio") -> float:
    """
    Calcula a Água Disponível (AD) em cm/cm.
    Implementa Fallback baseado na textura se os dados forem nulos ou inconsistentes.
    """
    ad = vwc33 - vwc1500
    
    if ad <= 0:
        # Fallback baseado no tipo de solo (Hackathon/POC Safety)
        fallbacks = {
            "Argiloso": 0.15,
            "Médio": 0.11,
            "Arenoso": 0.07
        }
        return fallbacks.get(tipo_solo, 0.11)
        
    return ad

def obter_parametros_cultura(cultura: str, dap: int) -> Tuple[float, float]:
    """
    Retorna (Kc, Z) baseado na cultura e dias após o plantio (DAP) - Padrão FAO-56.
    """
    cultura = cultura.lower()
    
    if cultura == "soja":
        if dap <= 20: kc = 0.40
        elif dap <= 50: kc = 0.80
        elif dap <= 90: kc = 1.15
        else: kc = 0.50
        raiz = min(5.0 + (0.8 * dap), 60.0)
        
    elif cultura == "milho":
        if dap <= 20: kc = 0.30
        elif dap <= 50: kc = 0.75
        elif dap <= 90: kc = 1.20
        else: kc = 0.50
        raiz = min(5.0 + (1.0 * dap), 80.0)
        
    else:
        kc = 0.6
        raiz = min(5.0 + (0.6 * dap), 50.0)
        
    return kc, max(5.0, raiz)

def run_water_balance_simulation(
    df_weather: pd.DataFrame, 
    ad: float, 
    planting_date: date,
    vwc33: float,
    vwc1500: float,
    cultura: str
) -> List[Dict[str, Any]]:
    """
    Executa a iteração diária do balanço hídrico (ARM).
    Inicializa com a umidade do satélite da primeira data disponível.
    """
    results = []
    arm_prev = None
    
    for i, row in df_weather.iterrows():
        dap = (row["date"] - planting_date).days
        # Note: Se dap < 0, ignoramos, mas aqui df_weather já deve estar filtrado
        if dap < 0:
            continue
            
        kc, z = obter_parametros_cultura(cultura, dap)
        cad_diaria = ad * z * 10.0
        
        # Inicialização por Observação (Primeira data disponível)
        if arm_prev is None:
            sat_sm = row.get("satellite_soil_moisture")
            ad_ref = vwc33 - vwc1500
            if pd.notna(sat_sm) and ad_ref > 0:
                sat_fraction = (sat_sm - vwc1500) / ad_ref
                arm_prev = max(0.0, min(sat_fraction * cad_diaria, cad_diaria))
            else:
                arm_prev = cad_diaria
            
        eto = row.get("et0_fao_evapotranspiration", 0.0) or 0.0
        chuva = row.get("precipitation_sum", 0.0) or 0.0
        etc = eto * kc
        
        arm_calc = arm_prev + chuva - etc
        arm_calc = max(0.0, min(arm_calc, cad_diaria))
        
        # Calibração via Satélite
        sat_sm = row.get("satellite_soil_moisture")
        ad_ref = vwc33 - vwc1500
        
        if pd.notna(sat_sm) and ad_ref > 0:
            sat_fraction = (sat_sm - vwc1500) / ad_ref
            sat_arm = sat_fraction * cad_diaria
            sat_arm = max(0.0, min(sat_arm, cad_diaria))
            
            if abs(arm_calc - sat_arm) > (0.2 * cad_diaria):
                arm_calc = (arm_calc * 0.7) + (sat_arm * 0.3)
        
        results.append({
            "date": row["date"],
            "arm_mm": round(arm_calc, 2),
            "cad_diaria_mm": round(cad_diaria, 2),
            "chuva_mm": round(chuva, 2),
            "eto_mm": round(eto, 2),
            "kc": kc,
            "z_cm": round(z, 2)
        })
        
        arm_prev = arm_calc
        
    return results
