export interface DashboardEntry {
  date: string;
  arm_mm: number;
  chuva_mm: number;
  eto_mm: number;
  irrigacao_necessaria_mm: number;
}

export interface WaterBalanceResponse {
  coord: string;
  tipo_solo: string;
  cad_maxima_mm: number;
  armazenamento_atual_mm: number;
  status: string;
  alerta_irrigacao: boolean;
  previsao_irrigacao_dias: number;
  mensagem_status: string;
  insight_especialista?: string;
  clay_bruto?: number;
  sand_bruto?: number;
  dashboard_data: DashboardEntry[];
}

export interface WaterBalanceRequest {
  latitude: number;
  longitude: number;
  cultura: string;
  data_plantio: string;
}
