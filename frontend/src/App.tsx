import React, { useState } from 'react';
import { 
  Droplets, 
  Sprout, 
  AlertTriangle, 
  MapPin, 
  Calendar, 
  Wind,
  Layers,
  Activity
} from 'lucide-react';
import { 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  AreaChart, 
  Area,
  Bar
} from 'recharts';
import type { WaterBalanceRequest, WaterBalanceResponse } from './types';

function App() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<WaterBalanceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const [form, setForm] = useState<WaterBalanceRequest>({
    latitude: -23.5505,
    longitude: -46.6333,
    cultura: 'soja',
    data_plantio: '2026-03-01'
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/cad-estimativa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Erro ao processar dados');
      }
      
      const result = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'úmido': return '#22c55e';
      case 'seco': return '#ef4444';
      default: return '#f59e0b';
    }
  };

  return (
    <div className="container">
      <header style={{ marginBottom: '3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Agro Shield</h1>
          <p style={{ color: 'var(--text-dim)', marginTop: '0.5rem' }}>Inteligência Hídrica para Alta Produtividade</p>
        </div>
        <div className="glass" style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={18} color="var(--primary)" />
          <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>v4.0 Live</span>
        </div>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
        {/* Sidebar Form */}
        <section className="glass card">
          <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Layers size={24} color="var(--primary)" />
            Parâmetros
          </h2>
          <form onSubmit={handleSubmit} className="grid">
            <div>
              <label><MapPin size={14} style={{ marginRight: 4 }} /> Latitude</label>
              <input 
                type="number" 
                step="0.0001" 
                value={form.latitude} 
                onChange={e => setForm({...form, latitude: parseFloat(e.target.value)})} 
              />
            </div>
            <div>
              <label><MapPin size={14} style={{ marginRight: 4 }} /> Longitude</label>
              <input 
                type="number" 
                step="0.0001" 
                value={form.longitude} 
                onChange={e => setForm({...form, longitude: parseFloat(e.target.value)})} 
              />
            </div>
            <div>
              <label><Sprout size={14} style={{ marginRight: 4 }} /> Cultura</label>
              <select 
                value={form.cultura} 
                onChange={e => setForm({...form, cultura: e.target.value})}
              >
                <option value="soja">Soja</option>
                <option value="milho">Milho</option>
              </select>
            </div>
            <div>
              <label><Calendar size={14} style={{ marginRight: 4 }} /> Data de Plantio</label>
              <input 
                type="date" 
                value={form.data_plantio} 
                onChange={e => setForm({...form, data_plantio: e.target.value})} 
              />
            </div>
            <button type="submit" disabled={loading} style={{ marginTop: '1rem' }}>
              {loading ? 'Processando...' : 'Analisar Solo'}
            </button>
            {error && <p style={{ color: '#ef4444', fontSize: '0.875rem', marginTop: '0.5rem' }}>{error}</p>}
          </form>
        </section>

        {/* Dashboard Content */}
        <main>
          {data ? (
            <div className="grid">
              <div className="dashboard-grid" style={{ marginTop: 0 }}>
                <div className="glass card" style={{ position: 'relative', overflow: 'hidden' }}>
                  <div style={{ position: 'absolute', top: 0, right: 0, padding: '1rem' }}>
                    <Droplets size={40} color="var(--primary)" style={{ opacity: 0.1 }} />
                  </div>
                  <label>Status do Solo</label>
                  <h3 style={{ fontSize: '2rem', color: getStatusColor(data.status) }}>{data.status}</h3>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-dim)' }}>{data.mensagem_status}</p>
                </div>

                <div className="glass card">
                  <label>Armazenamento Atual</label>
                  <h3 style={{ fontSize: '2rem' }}>{data.armazenamento_atual_mm} <span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>mm</span></h3>
                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', marginTop: '0.5rem' }}>
                    <div style={{ 
                      width: `${Math.min(100, (data.armazenamento_atual_mm / data.cad_maxima_mm) * 100)}%`, 
                      height: '100%', 
                      background: 'var(--primary)', 
                      borderRadius: '4px',
                      boxShadow: '0 0 10px var(--primary)'
                    }}></div>
                  </div>
                </div>

                <div className="glass card">
                  <label>Previsão de Irrigação</label>
                  {data.alerta_irrigacao ? (
                    <>
                      <h3 style={{ fontSize: '2rem', color: '#f59e0b' }}>{data.previsao_irrigacao_dias} <span style={{ fontSize: '1rem' }}>dias</span></h3>
                      <p style={{ fontSize: '0.875rem', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <AlertTriangle size={14} /> Atenção necessária
                      </p>
                    </>
                  ) : (
                    <>
                      <h3 style={{ fontSize: '2rem', color: 'var(--primary)' }}>Seguro</h3>
                      <p style={{ fontSize: '0.875rem', color: 'var(--text-dim)' }}>Sem necessidade imediata</p>
                    </>
                  )}
                </div>
              </div>

              {/* Chart */}
              <section className="glass card" style={{ minHeight: '400px' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>Balanço Hídrico (Simulação 90 dias)</h3>
                <div style={{ width: '100%', height: '300px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data.dashboard_data}>
                      <defs>
                        <linearGradient id="colorArm" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis 
                        dataKey="date" 
                        stroke="var(--text-dim)" 
                        fontSize={12} 
                        tickFormatter={(str) => new Date(str).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                      />
                      <YAxis stroke="var(--text-dim)" fontSize={12} unit="mm" />
                      <Tooltip 
                        content={({ active, payload, label }) => {
                          if (active && payload && payload.length) {
                            return (
                              <div className="glass" style={{ padding: '1rem', border: '1px solid var(--primary)', borderRadius: '12px' }}>
                                <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>
                                  {label ? new Date(label).toLocaleDateString('pt-BR', { day: '2-digit', month: 'long' }) : ''}
                                </p>
                                {payload.map((p: any) => (
                                  <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: p.color }}></div>
                                    <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>{p.name}:</span>
                                    <span style={{ fontSize: '0.875rem' }}>{p.value.toFixed(1)} mm</span>
                                  </div>
                                ))}
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="arm_mm" 
                        stroke="#22c55e" 
                        strokeWidth={3}
                        fillOpacity={1} 
                        fill="url(#colorArm)" 
                        name="Armazenamento"
                      />
                      <Bar dataKey="chuva_mm" fill="#3b82f6" name="Precipitação" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="irrigacao_necessaria_mm" fill="#f59e0b" name="Lâmina Irrigação" radius={[4, 4, 0, 0]} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </section>

              {/* Specialist Insight */}
              {data.insight_especialista && (
                <div className="glass card" style={{ borderLeft: '4px solid var(--primary)', background: 'rgba(34, 197, 94, 0.05)' }}>
                  <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Wind size={18} color="var(--primary)" />
                    Insight do Especialista
                  </h4>
                  <p style={{ color: 'rgba(255,255,255,0.9)', fontStyle: 'italic' }}>"{data.insight_especialista}"</p>
                </div>
              )}
            </div>
          ) : (
            <div className="glass card float" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '4rem' }}>
              <div className="pulse" style={{ background: 'rgba(255,255,255,0.03)', padding: '2rem', borderRadius: '50%', marginBottom: '2rem' }}>
                <Sprout size={64} color="var(--primary)" opacity={0.5} />
              </div>
              <h2 style={{ marginBottom: '1rem' }}>Pronto para Analisar</h2>
              <p style={{ color: 'var(--text-dim)', maxWidth: '400px' }}>
                Insira as coordenadas da sua propriedade e os dados do plantio para gerar o balanço hídrico em tempo real.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
