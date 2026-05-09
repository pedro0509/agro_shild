from fastapi import FastAPI, HTTPException, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import date, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from typing import List

from app.models.schemas import WaterBalanceRequest, WaterBalanceResponse, DashboardEntry
from app.services.soilgrids_client import get_soil_properties
from app.services.weather_manager import WeatherManager
from app.core.zarc_classifier import classify_soil
from app.core.water_balance import (
    calculate_ad, 
    run_water_balance_simulation
)
from app.db.database import SessionLocal, WeatherHistory, SoilData

app = FastAPI(title="Agro Shield - Persistência Hídrica v4")
weather_manager = WeatherManager()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # Pega apenas a primeira mensagem de erro para simplificar
    err = exc.errors()[0]
    msg = err.get("msg", "Erro de validação")
    # Limpa a mensagem se ela começar com "Value error, "
    msg = msg.replace("Value error, ", "")
    return JSONResponse(
        status_code=400,
        content={"detail": msg}
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "Agro Shield API v4 is running with Soil & Weather Persistence"}

@app.post("/api/v1/cad-estimativa", response_model=WaterBalanceResponse)
async def get_cad_estimativa(request: WaterBalanceRequest, db: Session = Depends(get_db)):
    try:
        # 1. Validação de Data e Trava de Segurança
        today = date.today()
        if request.data_plantio >= today:
             raise HTTPException(
                status_code=400, 
                detail="A data do plantio deve ser anterior à data de hoje."
            )
            
        # Filtro de Realidade (POC): Limita a data mínima de processamento
        DATA_LIMITE_POC = date(2026, 2, 10)
        data_efetiva_plantio = max(request.data_plantio, DATA_LIMITE_POC)
        
        # Validação do Ciclo (150 dias)
        dap_total = (today - request.data_plantio).days
        if dap_total > 150:
            raise HTTPException(
                status_code=400,
                detail=f"Ciclo de cultura encerrado para esta data de plantio ({dap_total} dias). O limite máximo é de 150 dias."
            )

        # 2. Busca Dados de Solo (Primeiro no Banco de Dados)
        soil = db.query(SoilData).filter(
            SoilData.latitude == request.latitude,
            SoilData.longitude == request.longitude
        ).first()
        
        if not soil:
            raw_soil = await get_soil_properties(request.latitude, request.longitude)
            tipo_solo = classify_soil(raw_soil["clay"], raw_soil["sand"])
            
            soil = SoilData(
                latitude=request.latitude,
                longitude=request.longitude,
                clay=raw_soil["clay"],
                sand=raw_soil["sand"],
                wv0033=raw_soil["wv0033"],
                wv1500=raw_soil["wv1500"],
                tipo_solo=tipo_solo
            )
            db.add(soil)
            db.commit()
            db.refresh(soil)
            
        vwc33 = soil.wv0033
        if vwc33 > 1.0: vwc33 /= 100.0
        vwc1500 = soil.wv1500
        if vwc1500 > 1.0: vwc1500 /= 100.0
        ad = calculate_ad(vwc33, vwc1500, tipo_solo=soil.tipo_solo)
        
        # 3. Definição do Intervalo de Datas
        dap = (today - data_efetiva_plantio).days
        api_limit_date = today - timedelta(days=90)
        start_weather = max(data_efetiva_plantio, api_limit_date)
        end_weather = min(request.data_plantio + timedelta(days=90), today) + timedelta(days=7)
        if end_weather < start_weather:
            end_weather = start_weather + timedelta(days=7)

        # 4. Busca Histórico no Banco de Dados
        db_weather = db.query(WeatherHistory).filter(
            WeatherHistory.latitude == request.latitude,
            WeatherHistory.longitude == request.longitude,
            WeatherHistory.date >= start_weather,
            WeatherHistory.date <= end_weather
        ).all()
        
        dates_in_db = {w.date for w in db_weather}
        all_dates_needed = {start_weather + timedelta(days=x) for x in range((end_weather - start_weather).days + 1)}
        missing_dates = all_dates_needed - dates_in_db
        
        if missing_dates:
            df_api = weather_manager.get_weather_data(request.latitude, request.longitude, start_weather, end_weather)
            for _, row in df_api.iterrows():
                if row["date"] not in dates_in_db:
                    new_weather = WeatherHistory(
                        latitude=request.latitude,
                        longitude=request.longitude,
                        date=row["date"],
                        precipitation=row["precipitation_sum"],
                        eto=row["et0_fao_evapotranspiration"],
                        soil_moisture=row["satellite_soil_moisture"]
                    )
                    db.add(new_weather)
            db.commit()
            db_weather = db.query(WeatherHistory).filter(
                WeatherHistory.latitude == request.latitude,
                WeatherHistory.longitude == request.longitude,
                WeatherHistory.date >= start_weather,
                WeatherHistory.date <= end_weather
            ).order_by(WeatherHistory.date).all()

        weather_records = []
        for w in db_weather:
            weather_records.append({
                "date": w.date,
                "precipitation_sum": w.precipitation,
                "et0_fao_evapotranspiration": w.eto,
                "satellite_soil_moisture": w.soil_moisture
            })
        df_weather = pd.DataFrame(weather_records)

        # 5. Simulação do Balanço Hídrico
        simulation_results = run_water_balance_simulation(
            df_weather, ad, data_efetiva_plantio, vwc33, vwc1500, request.cultura
        )
        
        # 6. Inteligência Preditiva e Alertas
        arm_atual = 0.0
        cad_atual = 0.0
        alerta_irrigacao = False
        dias_ate_seca = 0
        mensagem_status = "Solo com umidade adequada"
        current_status = "Úmido"
        
        dashboard_list = []
        for i, res in enumerate(simulation_results):
            dashboard_list.append(DashboardEntry(
                date=res["date"],
                arm_mm=res["arm_mm"],
                chuva_mm=res["chuva_mm"],
                eto_mm=res["eto_mm"]
            ))
            
            if res["date"] == today:
                arm_atual = res["arm_mm"]
                cad_atual = res["cad_diaria_mm"]
                if arm_atual <= (0.5 * cad_atual):
                    current_status = "Seco"
                    mensagem_status = "Atenção: Solo abaixo do limite de segurança"
            
            if res["date"] > today and not alerta_irrigacao:
                limite_critico = 0.5 * res["cad_diaria_mm"]
                if res["arm_mm"] <= limite_critico:
                    alerta_irrigacao = True
                    dias_ate_seca = (res["date"] - today).days
                    
                    chuva_prevista = res["chuva_mm"]
                    chuva_dia_anterior = simulation_results[i-1]["chuva_mm"] if i > 0 else 0
                    
                    if chuva_prevista > 10 or chuva_dia_anterior > 10:
                        alerta_irrigacao = False
                        mensagem_status = f"Chuva prevista ({max(chuva_prevista, chuva_dia_anterior)}mm) atende à demanda"
                    else:
                        mensagem_status = f"Irrigar em {dias_ate_seca} dias"

        chuva_recente = sum([res["chuva_mm"] for res in simulation_results if res["date"] in [date(2026, 5, 8), date(2026, 5, 9)]])
        insight = None
        if chuva_recente > 150:
            insight = f"Insight: Solo Saturado ({chuva_recente:.1f}mm chuva recente)."
        elif alerta_irrigacao:
            insight = "Insight: Planeje a irrigação para os próximos dias."

        return WaterBalanceResponse(
            coord=f"{request.latitude}, {request.longitude}",
            tipo_solo=soil.tipo_solo,
            cad_maxima_mm=round(cad_atual, 2),
            armazenamento_atual_mm=round(arm_atual, 2),
            status=current_status,
            alerta_irrigacao=alerta_irrigacao,
            previsao_irrigacao_dias=dias_ate_seca,
            mensagem_status=mensagem_status,
            insight_especialista=insight,
            clay_bruto=soil.clay,
            sand_bruto=soil.sand,
            dashboard_data=dashboard_list
        )
        
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
