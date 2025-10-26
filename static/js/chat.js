// static/js/chat.js
// Chat client logic: polling, render, send (with image), enter-to-send, smart auto-scroll.
// Works if template defines `fetchUrl` & `sendUrl` globals OR #messages data-* attrs.

(function(){
  // helper to get path from either global or data-attrs
  const msgDiv = document.getElementById('messages');
  if (!msgDiv) {
    console.warn('chat.js: #messages element not found');
    return;
  }

  const fetchUrl = (typeof window.fetchUrl !== 'undefined') ? window.fetchUrl : msgDiv.dataset.fetchUrl;
  const sendUrl  = (typeof window.sendUrl  !== 'undefined') ? window.sendUrl  : msgDiv.dataset.sendUrl;
  const currentUserId = (typeof window.CURRENT_USER_ID !== 'undefined') ? parseInt(window.CURRENT_USER_ID,10) : parseInt("0",10);

  let autoScrollEnabled = true;
  const SCROLL_THRESHOLD = 120;

  // create hidden file input if not present
  let imageInput = document.getElementById('image-input');
  if (!imageInput) {
    imageInput = document.createElement('input');
    imageInput.type = 'file';
    imageInput.accept = 'image/*';
    imageInput.id = 'image-input';
    imageInput.style.display = 'none';
    document.body.appendChild(imageInput);
  }

  // find send form and textarea; fallback to elements in template
  const form = document.getElementById('send-form') || (function(){
    const f = document.createElement('form');
    f.id = 'send-form';
    document.body.appendChild(f);
    return f;
  })();

  const textarea = document.getElementById('content') || (function(){
    const ta = document.createElement('textarea');
    ta.id = 'content';
    ta.placeholder = 'Tulis pesan...';
    ta.style.display = 'none';
    form.appendChild(ta);
    return ta;
  })();

  // csrf: prefer input[name=csrfmiddlewaretoken] in DOM, fallback to cookie
  function getCsrfToken(){
    const el = document.querySelector('input[name=csrfmiddlewaretoken]');
    if (el) return el.value;
    // fallback: read cookie
    const name = 'csrftoken';
    const match = document.cookie.split(';').map(s=>s.trim()).find(s=>s.startsWith(name+'='));
    if (!match) return '';
    return decodeURIComponent(match.split('=')[1]);
  }

  // scrolling behaviour
  msgDiv.addEventListener('scroll', () => {
    const distanceFromBottom = msgDiv.scrollHeight - msgDiv.scrollTop - msgDiv.clientHeight;
    autoScrollEnabled = distanceFromBottom <= SCROLL_THRESHOLD;
  });

  function escapeHtml(s){
    if (!s) return '';
    return s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
  }

  function renderMessages(messages){
    if (!Array.isArray(messages)) return;
    // compute was near bottom
    const wasNearBottom = (msgDiv.scrollHeight - msgDiv.scrollTop - msgDiv.clientHeight) <= SCROLL_THRESHOLD;

    msgDiv.innerHTML = '';
    messages.forEach(m => {
      const el = document.createElement('div');
      el.className = 'chat-message ' + ((m.sender_id === currentUserId) ? 'from-me' : 'from-other');

      const senderLabel = (m.sender_id === currentUserId) ? 'You' : (m.sender_username || 'User');
      const timeStr = m.created_at ? (new Date(m.created_at)).toLocaleString() : '';

      let topHtml = `<div class="meta-row"><strong class="sender">${escapeHtml(senderLabel)}</strong>`;
      if (timeStr) topHtml += `<span class="time">${escapeHtml(timeStr)}</span>`;
      topHtml += `</div>`;

      let contentHtml = '';
      if (m.image_url) {
        contentHtml += `<div class="img-wrap"><a href="${m.image_url}" target="_blank" rel="noopener"><img src="${m.image_url}" alt="img" /></a></div>`;
      }
      if (m.content) {
        contentHtml += `<div class="text-wrap">${escapeHtml(m.content)}</div>`;
      }

      el.innerHTML = topHtml + contentHtml;
      msgDiv.appendChild(el);
    });

    if (autoScrollEnabled || wasNearBottom) {
      msgDiv.scrollTop = msgDiv.scrollHeight;
      autoScrollEnabled = true;
    }
  }

  async function fetchMessages(){
    if (!fetchUrl) return;
    try {
      const resp = await fetch(fetchUrl, { credentials: 'same-origin' });
      if (!resp.ok) {
        console.warn('fetchMessages: server returned', resp.status);
        return;
      }
      const data = await resp.json();
      if (data && data.messages) renderMessages(data.messages);
    } catch (e) {
      console.error('fetchMessages error', e);
    }
  }

  // Enter to send (Shift+Enter newline)
  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.dispatchEvent(new Event('submit', {cancelable:true}));
    }
  });

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    if (!sendUrl) {
      console.warn('sendUrl not configured');
      return;
    }
    const text = textarea.value.trim();
    const fd = new FormData();
    if (text) fd.append('content', text);
    if (imageInput.files && imageInput.files[0]) fd.append('image', imageInput.files[0]);
    // append csrf
    const csrftok = getCsrfToken();
    if (csrftok) fd.append('csrfmiddlewaretoken', csrftok);

    try {
      const res = await fetch(sendUrl, { method: 'POST', body: fd, credentials: 'same-origin' });
      if (!res.ok) {
        const txt = await res.text();
        alert('Gagal mengirim: ' + txt);
        return;
      }
      textarea.value = '';
      imageInput.value = '';
      await fetchMessages();
    } catch (e) {
      console.error('send error', e);
    }
  });

  // attach button behavior: if template has .attach-btn -> click triggers input
  const attachBtn = document.querySelector('.attach-btn');
  if (attachBtn) {
    attachBtn.addEventListener('click', (e) => {
      e.preventDefault();
      imageInput.click();
    });
  }

  // if user picks file, optionally show small preview (you can extend)
  imageInput.addEventListener('change', () => {
    // can't show UI here without custom element; template may do that
  });

  // start polling
  fetchMessages();
  setInterval(fetchMessages, 2500);
})();
