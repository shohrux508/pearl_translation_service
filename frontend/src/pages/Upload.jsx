import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

export default function Upload() {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('ru');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  
  const fileInputRef = useRef(null);

  useEffect(() => {
    axios.get('/api/templates/')
      .then(response => setTemplates(response.data))
      .catch(err => console.error("Error fetching templates:", err));
  }, []);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSelectFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleSubmit = async () => {
    if (!file || !selectedTemplate) return;
    
    setIsSubmitting(true);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_id', selectedTemplate);
    formData.append('lang', selectedLanguage);
    
    let userId = 123456789; // Default for dev outside Telegram
    if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
      userId = window.Telegram.WebApp.initDataUnsafe.user.id;
    }
    formData.append('user_id', userId.toString());
    
    try {
      await axios.post('/api/templates/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setSubmitSuccess(true);
      // Give haptic feedback
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert("Ошибка при загрузке документа.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitSuccess) {
    return (
      <div className="page fade-in text-center" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div style={{ fontSize: '64px', marginBottom: '20px' }}>🚀</div>
        <h2>Документ в работе!</h2>
        <p className="text-hint" style={{ marginTop: '10px' }}>
          Мы уже начали извлекать данные и переводить их. Готовый `.docx` файл придёт вам прямо в этот чат от бота в течение 10-15 секунд!
        </p>
        <button 
          className="btn-primary" 
          style={{ marginTop: '40px', background: 'var(--tg-theme-hint-color)' }}
          onClick={() => {
            setSubmitSuccess(false);
            setFile(null);
          }}
        >
          Загрузить ещё один
        </button>
      </div>
    );
  }

  const isFormValid = file && selectedTemplate;

  return (
    <div className="page fade-in">
      <h2>Новый перевод</h2>
      <p className="text-hint">Загрузите фотографию документа</p>
      
      <div 
        className="glass-panel text-center" 
        style={{ 
          marginTop: '20px', 
          padding: '40px 20px', 
          borderStyle: 'dashed',
          borderColor: isDragging ? 'var(--tg-theme-button-color)' : 'var(--glass-border)',
          backgroundColor: isDragging ? 'rgba(82, 136, 193, 0.1)' : 'var(--glass-bg)',
          transition: 'all 0.3s ease',
          cursor: 'pointer',
          position: 'relative'
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleSelectFileClick}
      >
        {file ? (
          <div>
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'center' }}>
              {file.type.startsWith('image/') ? (
                   <img src={URL.createObjectURL(file)} alt="preview" style={{ maxHeight: '120px', borderRadius: '12px', objectFit: 'contain' }} />
              ) : (
                <div style={{ fontSize: '48px' }}>📸</div>
              )}
            </div>
            <h3 style={{ color: 'var(--tg-theme-button-color)', wordBreak: 'break-all' }}>{file.name}</h3>
            <p className="text-hint">{(file.size / 1024).toFixed(1)} KB</p>
            <p className="text-hint" style={{ marginTop: '10px', fontSize: '13px' }}>Нажмите, чтобы выбрать другое фото</p>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📸</div>
            <h3>Нажмите или перетащите фото</h3>
            <p className="text-hint">Форматы: .jpg, .jpeg, .png</p>
          </div>
        )}
        
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          accept="image/jpeg, image/png, image/jpg" 
          onChange={handleFileChange} 
        />
      </div>

      <div style={{ marginTop: '20px', display: 'flex', gap: '12px' }}>
        <div style={{ flex: 1 }}>
          <h3 style={{ fontSize: '15px', marginBottom: '8px' }}>Тип документа</h3>
          <select 
            className="glass-panel"
            style={{ width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid var(--glass-border)', outline: 'none' }}
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
          >
            <option value="" disabled>Выберите тип...</option>
            {templates.map(t => (
              <option key={t.id} value={t.id}>{t.emoji} {t.name}</option>
            ))}
          </select>
        </div>
        <div style={{ width: '120px' }}>
          <h3 style={{ fontSize: '15px', marginBottom: '8px' }}>Язык</h3>
          <select 
            className="glass-panel"
            style={{ width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid var(--glass-border)', outline: 'none' }}
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
          >
            <option value="ru">🇷🇺 RU</option>
            <option value="en">🇬🇧 EN</option>
          </select>
        </div>
      </div>

      <button 
        className="btn-primary" 
        onClick={handleSubmit}
        style={{ 
          marginTop: '30px',
          opacity: isFormValid && !isSubmitting ? 1 : 0.5,
          cursor: isFormValid && !isSubmitting ? 'pointer' : 'not-allowed',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '8px'
        }} 
        disabled={!isFormValid || isSubmitting}
      >
        {isSubmitting ? (
          <>
            <span className="spinner" style={{ width: '16px', height: '16px', border: '2px solid rgba(255,255,255,0.3)', borderTop: '2px solid white', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></span>
            Обработка...
          </>
        ) : (
          "Начать перевод"
        )}
      </button>
      <style>{`
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
