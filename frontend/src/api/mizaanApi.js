import { API_BASE_URL, DEFAULT_SESSION_ID } from '../config.js';

export async function sendMessage(message, sessionId = DEFAULT_SESSION_ID) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL.replace(/\/$/, '')}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
  } catch {
    throw new Error('تعذر الاتصال بالخادم. تأكد من تشغيل الـ API ثم حاول مرة أخرى.');
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error('وصل رد غير صالح من الخادم.');
  }
  if (!response.ok) {
    throw new Error(typeof data?.detail === 'string' ? data.detail : 'تعذر إرسال الرسالة. تحقق من البيانات وحاول مرة أخرى.');
  }
  if (typeof data?.answer !== 'string') {
    throw new Error('رد الخادم لا يحتوي على إجابة نصية صالحة.');
  }
  return {
    answer: data.answer,
    dashboard: data.dashboard && typeof data.dashboard === 'object' && !Array.isArray(data.dashboard)
      ? data.dashboard : null,
  };
}
