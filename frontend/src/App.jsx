import { useState } from 'react';
import { sendMessage } from './api/mizaanApi.js';
import { DEFAULT_SESSION_ID } from './config.js';
import Chat from './components/Chat.jsx';
import Dashboard from './components/Dashboard.jsx';
import AgentActivity from './components/AgentActivity.jsx';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sessionId, setSessionId] = useState(DEFAULT_SESSION_ID);

  async function handleSend(text) {
    if (loading || !text.trim()) return;
    setLoading(true);
    setError('');
    setMessages((previous) => [...previous, { role: 'user', text }]);
    try {
      const response = await sendMessage(text, sessionId);
      setMessages((previous) => [...previous, { role: 'assistant', text: response.answer }]);
      if (response.dashboard !== null) setDashboard(response.dashboard);
    } catch (failure) {
      setError(failure.message);
    } finally {
      setLoading(false);
    }
  }

  function changeSession(value) {
    setSessionId(value);
    setMessages([]);
    setDashboard(null);
    setError('');
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#"><span className="brand-mark">م</span><div><strong>ميزان</strong><span>ذكاء القرار الزراعي</span></div></a>
        <div className="topbar-meta"><span className="demo-badge">نسخة تجريبية</span><span className="country-label">الأردن · التخطيط الزراعي</span></div>
      </header>
      <section className="page-intro"><div className="eyebrow">من البيانات إلى القرار</div><h1>خطّط بثقة. استثمر بوعي.</h1><p>مساحة واحدة للمحادثة، ومقارنة خطط مزرعتك حسب البيانات المتاحة.</p></section>
      <main className="workspace">
        <section className="chat-column"><Chat messages={messages} loading={loading} error={error} onSend={handleSend} sessionId={sessionId} onSessionChange={changeSession} /><AgentActivity loading={loading} /></section>
        <Dashboard dashboard={dashboard} />
      </main>
      <footer className="footer">ميزان · دعم القرارات الاقتصادية الزراعية<span>تقديرات تخطيطية حسب البيانات المتاحة</span></footer>
    </div>
  );
}
