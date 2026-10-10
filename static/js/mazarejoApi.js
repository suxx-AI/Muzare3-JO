// The only frontend module that makes HTTP requests. Routes come from Django.
function csrfToken() { return document.querySelector('meta[name="csrf-token"]')?.content || ''; }

export async function postJson(endpoint, body) {
  let response;
  try {
    response = await fetch(endpoint, {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json','X-CSRFToken':csrfToken()}, body:JSON.stringify(body)});
  } catch { throw new Error('تعذر الاتصال بالخادم. تحقق من تشغيل مزارع جو ثم حاول مرة أخرى.'); }
  let data;
  try { data = await response.json(); } catch { throw new Error('تعذر إكمال الطلب حالياً. حدّث الصفحة وحاول مرة أخرى.'); }
  if (!response.ok) throw new Error(typeof data?.error === 'string' ? data.error : 'تعذر إكمال التحليل حالياً. حاول مرة أخرى.');
  return data;
}

export async function sendMessage(message, endpoint) {
  const data = await postJson(endpoint, {message});
  if (typeof data?.answer !== 'string' || !data.answer.trim()) throw new Error('لم تصل إجابة مكتملة. حاول مرة أخرى.');
  return data;
}

export async function checkHealth(endpoint) {
  try {
    const response = await fetch(endpoint, {cache:'no-store', signal:AbortSignal.timeout(4000)});
    const data = await response.json();
    return response.ok && data?.status === 'ok' && data?.app === 'mazarejo';
  } catch { return false; }
}
