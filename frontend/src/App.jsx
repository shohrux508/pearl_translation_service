import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Templates from './pages/Templates';
import Upload from './pages/Upload';
import History from './pages/History';
import Settings from './pages/Settings';
import './index.css';

// Simple Icons component
const Icon = ({ name, active }) => {
  const color = active ? 'var(--tg-theme-button-color)' : 'currentColor';
  if (name === 'templates') return <svg fill={color} viewBox="0 0 24 24"><path d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z"/></svg>;
  if (name === 'upload') return <svg fill={color} viewBox="0 0 24 24"><path d="M9 16h6v-6h4l-7-7-7 7h4v6zm-4 2h14v2H5v-2z"/></svg>;
  if (name === 'history') return <svg fill={color} viewBox="0 0 24 24"><path d="M13 3h-2v10l8.5 5 1-1.73-7.5-4.42V3z"/></svg>;
  if (name === 'settings') return <svg fill={color} viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.73 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.49-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>;
  return null;
}

const BottomNav = () => {
  const location = useLocation();
  const currentPath = location.pathname;

  return (
    <nav className="bottom-nav">
      <Link to="/" className={`nav-item ${currentPath === '/' ? 'active' : ''}`}>
        <Icon name="templates" active={currentPath === '/'} />
        <span>Шаблоны</span>
      </Link>
      <Link to="/upload" className={`nav-item ${currentPath === '/upload' ? 'active' : ''}`}>
        <Icon name="upload" active={currentPath === '/upload'} />
        <span>Новый</span>
      </Link>
      <Link to="/history" className={`nav-item ${currentPath === '/history' ? 'active' : ''}`}>
        <Icon name="history" active={currentPath === '/history'} />
        <span>История</span>
      </Link>
      <Link to="/settings" className={`nav-item ${currentPath === '/settings' ? 'active' : ''}`}>
        <Icon name="settings" active={currentPath === '/settings'} />
        <span>Настройки</span>
      </Link>
    </nav>
  );
};

function App() {
  useEffect(() => {
    // Notify telegram that app is ready to be displayed
    if (window.Telegram && window.Telegram.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);

  return (
    <Router>
      <div className="app-container">
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Templates />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
        <BottomNav />
      </div>
    </Router>
  );
}

export default App;
