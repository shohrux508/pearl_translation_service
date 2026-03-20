import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Templates() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch data from our FastAPI backend
    axios.get('/api/templates')
      .then(response => {
        setTemplates(response.data);
      })
      .catch(error => {
        console.error("Error fetching templates:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <div className="page slide-in">
      <h2>Шаблоны перевода</h2>
      <p className="text-hint">Выберите или создайте новый шаблон промпта для ИИ</p>
      
      <div style={{ marginTop: '20px' }}>
        {loading ? (
          <div>Загрузка...</div>
        ) : (
          <div className="template-list">
            {templates.length === 0 ? <p className="text-hint">Шаблонов пока нет</p> : templates.map(t => (
              <div key={t.id} className="glass-panel" style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '24px', marginRight: '12px' }}>{t.emoji}</span>
                  <h3 style={{ margin: 0 }}>{t.name}</h3>
                </div>
                
                <p className="text-hint" style={{ fontSize: '13px' }}>
                  Доступно: {t.ru_template ? '🇷🇺 RU ' : ''} {t.en_template ? '🇬🇧 EN' : ''}
                  {!t.ru_template && !t.en_template && 'нет шаблонов'}
                </p>

                <div style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
                   <button className="btn-primary" style={{ padding: '8px 16px', fontSize: '14px', flex: 1 }}>Выбрать</button>
                   <button className="btn-primary" style={{ padding: '8px 16px', fontSize: '14px', background: 'var(--tg-theme-hint-color)', width: 'auto' }}>✏️</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <button className="btn-primary" style={{ marginTop: '20px' }}>+ Добавить класс</button>
    </div>
  );
}
