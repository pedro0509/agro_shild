import httpx
from typing import Dict, Any

BASE_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

async def get_soil_properties(lat: float, lon: float) -> Dict[str, float]:
    """
    Consulta a API SoilGrids e retorna os valores médios processados (com d_factor aplicado).
    Propriedades consultadas: clay, sand, wv0033, wv1500.
    Camadas: 0-5cm e 5-15cm.
    """
    params = {
        "lon": lon,
        "lat": lat,
        "property": ["clay", "sand", "wv0033", "wv1500"],
        "depth": ["0-5cm", "5-15cm"],
        "value": "mean"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(BASE_URL, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        print(f"DEBUG - SoilGrids Raw Data for ({lat}, {lon}): {data}")
    
    results = {}
    layers = data.get("properties", {}).get("layers", [])
    
    for layer in layers:
        name = layer.get("name")
        d_factor = layer.get("unit_measure", {}).get("d_factor", 1)
        
        # Faz a média dos valores das profundidades retornadas
        depths = layer.get("depths", [])
        if not depths:
            continue
            
        values = [d.get("values", {}).get("mean", 0) for d in depths]
        avg_raw_value = sum(values) / len(values)
        
        # Aplica o fator de conversão
        results[name] = avg_raw_value / d_factor
        
    return results
