let sessionId = null;
let handedOff = false;

function getTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

async function init() {
  try {
    const res = await fetch('/api/session/new', { method: 'POST' });
    const data = await res.json();
    sessionId = data.session_id;
    addMsg('bot', "Hi! I'm Kiko 👋\nHow can I help you today?");
  } catch {
    addMsg('bot', '⚠️ Could not connect to server. Please refresh.');
  }
}

function formatText(text) {
  text = text.replace(/\\n/g, '\n');
  text = text.replace(/\*\*(.*?)\*\*/g, '$1').replace(/\*(.*?)\*/g, '$1');
  text = text.replace(/^[\-\*]\s+/gm, '• ');
  text = text.replace(/\n{3,}/g, '\n\n');
  return text.trim();
}

function addMsg(role, text) {
  const row = document.createElement('div');
  row.className = 'bubble-row ' + role;

  const bubble = document.createElement('div');
  bubble.className = 'msg';
  bubble.textContent = role === 'bot' ? formatText(text) : text;

  const ts = document.createElement('div');
  ts.className = 'ts';
  ts.textContent = getTime();

  row.appendChild(bubble);
  row.appendChild(ts);
  document.getElementById('messages').appendChild(row);
  scrollBottom();
  return row;
}

function addTyping() {
  const row = document.createElement('div');
  row.className = 'typing-row';
  row.id = 'typing-indicator';
  row.innerHTML = `
    <div class="typing-bubble">
      <div class="typing-shimmer"></div>
      <span class="typing-label">Kiko is typing</span>
    </div>`;
  document.getElementById('messages').appendChild(row);
  scrollBottom();
}

function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

function scrollBottom() {
  const m = document.getElementById('messages');
  m.scrollTop = m.scrollHeight;
}

function setInputState(enabled) {
  document.getElementById('msg-input').disabled = !enabled;
  document.getElementById('send-btn').disabled = !enabled;
}

// Avatar ring + status dot share one status color (signature element)
function setStatus(color, label) {
  document.getElementById('avatar-ring').style.setProperty('--ring-color', color);
  document.getElementById('status-dot').style.background = color;
  document.getElementById('status-text').textContent = label;
}

async function send() {
  if (handedOff) return;
  const input = document.getElementById('msg-input');
  const text = input.value.trim();
  if (!text || !sessionId) return;

  input.value = '';
  setInputState(false);
  addMsg('user', text);
  addTyping();

  try {
    const res = await fetch('/api/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message: text, user_name: 'User' })
    });

    removeTyping();

    if (res.status === 429) {
      addMsg('bot', '⚠️ Too many messages. Please wait a moment.');
      setInputState(true);
      return;
    }

    const data = await res.json();
    addMsg('bot', data.response);

    if (data.handoff) {
      handedOff = true;
      const el = document.createElement('div');
      el.className = 'handoff';
      el.textContent = '⚠️ Connecting you to a human agent…';
      document.getElementById('messages').appendChild(el);
      scrollBottom();
      setInputState(false);
      document.getElementById('msg-input').placeholder = 'Chat ended — handed off to agent';
      setStatus('var(--danger)', 'Handed off');
      return;
    }
  } catch {
    removeTyping();
    addMsg('bot', '⚠️ Something went wrong. Please try again.');
  }

  setInputState(true);
  input.focus();
}

document.getElementById('send-btn').addEventListener('click', send);
document.getElementById('msg-input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) send();
});

init();