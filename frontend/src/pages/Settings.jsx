export default function Settings() {
  return (
    <div className="page fade-in">
      <h2>Настройки</h2>
      <p className="text-hint">Управление аккаунтом и API</p>
      
      <div className="glass-panel" style={{ marginTop: '20px' }}>
        <h3>Модель Gemini</h3>
        <select style={{ width: '100%', padding: '10px', marginTop: '10px', borderRadius: '8px', border: '1px solid var(--tg-theme-hint-color)' }}>
          <option>Gemini 1.5 Flash (Быстрая)</option>
          <option>Gemini 1.5 Pro (Точная)</option>
        </select>
      </div>

      <div className="glass-panel" style={{ marginTop: '20px' }}>
        <h3>Глоссарий</h3>
        <p className="text-hint" style={{ marginTop: '8px' }}>Здесь вы сможете задавать правила перевода для терминов.</p>
        <button className="btn-primary" style={{ marginTop: '16px', background: 'var(--tg-theme-button-color)', opacity: 0.8 }}>Управление</button>
      </div>
    </div>
  );
}
