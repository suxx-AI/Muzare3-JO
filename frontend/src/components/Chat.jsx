import { useEffect, useRef, useState } from 'react';

export default function Chat({ messages, loading, error, onSend, sessionId, onSessionChange }) {
  const [text, setText] = useState('');
  const [sessionDraft, setSessionDraft] = useState(sessionId);
  const bottom = useRef(null);
  useEffect(() => { if (messages.length || loading) bottom.current?.scrollIntoView({ block: 'nearest' }); }, [messages, loading]);

  function submit(event) {
    event.preventDefault();
    if (!text.trim() || loading) return;
    onSend(text.trim());
    setText('');
  }

  return (
    <div className="panel chat-panel">
      <div className="panel-heading"><div><span className="eyebrow">مساعدك الزراعي</span><h2>محادثة ميزان</h2></div><span className="pill">{loading ? 'جارٍ إعداد الرد' : 'جاهز للمحادثة'}</span></div>
      <form className="session-control" onSubmit={(event) => { event.preventDefault(); if (!loading && sessionDraft.trim()) { onSessionChange(sessionDraft.trim()); setText(''); } }}>
        <label htmlFor="session-id">معرّف المحادثة</label><input id="session-id" dir="ltr" value={sessionDraft} onChange={(event) => setSessionDraft(event.target.value)} disabled={loading} required />
        <button type="submit" disabled={loading || !sessionDraft.trim() || sessionDraft.trim() === sessionId}>تغيير</button>
      </form>
      <div className="chat-history" role="log" aria-label="رسائل المحادثة" aria-live="polite">
        {messages.length === 0 && <div className="chat-welcome"><span className="welcome-symbol">↗</span><h3>قرارك القادم يبدأ بسؤال</h3><p>اذكر مساحة الأرض، والميزانية، والمحاصيل التي تفكّر بها، لنبدأ إعداد خطة مبنية على البيانات.</p><div className="prompt-hint">مثال على سؤال</div><button className="example-prompt" onClick={() => setText('عندي ٢٠ دونم وميزانية ١٠ آلاف دينار. قارن زراعة "بندورة" و"خيار" واعطيني خطة متوازنة بين الهامش والمياه.')} disabled={loading}>كيف أوزّع أرضي بين المحاصيل ضمن ميزانيتي؟ <span>←</span></button></div>}
        {messages.map((message, index) => <article className={`message ${message.role}`} key={index}><span className="message-author">{message.role === 'user' ? 'أنت' : 'ميزان'}</span><p>{message.text || 'لم يصل نص للإجابة.'}</p></article>)}
        {loading && <div className="loading-message" role="status"><span className="loading-dot" />ميزان يعمل على طلبك…</div>}
        <div ref={bottom} />
      </div>
      {error && <div className="error-message" role="alert">{error}</div>}
      <form className="composer" onSubmit={submit}><label className="sr-only" htmlFor="chat-message">رسالتك لميزان</label><textarea id="chat-message" rows="3" placeholder="اكتب سؤالك عن مزرعتك…" value={text} onChange={(event) => setText(event.target.value)} disabled={loading} /><div className="composer-actions"><span>أضف المساحة والميزانية للحصول على خطة أدق</span><button type="submit" className="primary-button" disabled={loading || !text.trim()}>{loading ? 'جارٍ الإرسال…' : 'إرسال'} <span aria-hidden="true">↑</span></button></div></form>
    </div>
  );
}
