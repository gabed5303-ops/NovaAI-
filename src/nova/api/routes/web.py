"""Serves Nova's chat web page (the "face") at the site root: GET /

This is a single, self-contained HTML page (styles + script inline) so it needs
no build step and no external files. The page talks to the /chat endpoint we
already built. Keeping the whole page here as one string means it always ships
with the package with zero extra setup.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])

# The entire chat page. Plain string (NOT an f-string) so the JS/CSS braces are
# left alone. The page calls POST /chat itself from the browser.
INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Nova</title>
<style>
  :root {
    --bg: #0b0d12;
    --panel: #141821;
    --panel-2: #1b2130;
    --text: #e8ecf3;
    --muted: #8b93a7;
    --accent: #6c8cff;
    --accent-2: #33d6c8;
    --user: linear-gradient(135deg, #6c8cff, #7a5cff);
    --border: #232a3a;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body {
    background: radial-gradient(1200px 600px at 50% -10%, #182036 0%, var(--bg) 55%);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    display: flex; flex-direction: column; height: 100vh;
  }
  header {
    padding: 16px 20px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 12px;
    background: rgba(11,13,18,0.6); backdrop-filter: blur(8px);
  }
  .logo {
    width: 34px; height: 34px; border-radius: 9px;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    display: grid; place-items: center; font-weight: 800; color: #0b0d12;
  }
  .title { font-weight: 700; font-size: 17px; }
  .subtitle { color: var(--muted); font-size: 12.5px; margin-top: 1px; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent-2);
         box-shadow: 0 0 10px var(--accent-2); margin-left: auto; }
  .status { color: var(--muted); font-size: 12px; }

  main { flex: 1; overflow-y: auto; padding: 24px 16px; }
  .thread { max-width: 760px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }

  .msg { display: flex; gap: 12px; align-items: flex-start; }
  .msg .avatar {
    width: 30px; height: 30px; border-radius: 8px; flex: 0 0 30px;
    display: grid; place-items: center; font-size: 13px; font-weight: 700;
  }
  .msg.assistant .avatar { background: var(--panel-2); color: var(--accent-2); border: 1px solid var(--border); }
  .msg.user .avatar { background: var(--user); color: #fff; }
  .bubble {
    padding: 12px 15px; border-radius: 12px; line-height: 1.55;
    font-size: 15px; white-space: pre-wrap; word-wrap: break-word; max-width: 100%;
  }
  .msg.assistant .bubble { background: var(--panel); border: 1px solid var(--border); border-top-left-radius: 4px; }
  .msg.user { flex-direction: row-reverse; }
  .msg.user .bubble { background: var(--user); color: #fff; border-top-right-radius: 4px; }

  .welcome { text-align: center; color: var(--muted); margin: 48px auto; max-width: 520px; }
  .welcome h1 { color: var(--text); font-size: 26px; margin: 0 0 8px; }
  .chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 18px; }
  .chip { border: 1px solid var(--border); background: var(--panel); color: var(--text);
          padding: 8px 12px; border-radius: 999px; font-size: 13px; cursor: pointer; }
  .chip:hover { border-color: var(--accent); }

  footer { border-top: 1px solid var(--border); padding: 14px 16px;
           background: rgba(11,13,18,0.6); backdrop-filter: blur(8px); }
  .composer { max-width: 760px; margin: 0 auto; display: flex; gap: 10px; align-items: flex-end; }
  textarea {
    flex: 1; resize: none; background: var(--panel); color: var(--text);
    border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px;
    font: inherit; font-size: 15px; max-height: 160px; outline: none;
  }
  textarea:focus { border-color: var(--accent); }
  button.send {
    background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: #0b0d12;
    border: 0; border-radius: 12px; padding: 12px 18px; font-weight: 700; cursor: pointer;
    font-size: 15px;
  }
  button.send:disabled { opacity: .5; cursor: default; }
  .hint { max-width: 760px; margin: 8px auto 0; color: var(--muted); font-size: 11.5px; text-align: center; }
  .typing span { display: inline-block; width: 6px; height: 6px; margin: 0 1px; border-radius: 50%;
                 background: var(--muted); animation: blink 1.2s infinite both; }
  .typing span:nth-child(2){ animation-delay:.2s } .typing span:nth-child(3){ animation-delay:.4s }
  @keyframes blink { 0%,80%,100%{opacity:.2} 40%{opacity:1} }
</style>
</head>
<body>
  <header>
    <div class="logo">N</div>
    <div>
      <div class="title">Nova</div>
      <div class="subtitle">your local AI assistant</div>
    </div>
    <div class="dot" title="online"></div>
    <div class="status" id="model">connecting…</div>
  </header>

  <main id="main">
    <div class="thread" id="thread">
      <div class="welcome" id="welcome">
        <h1>Hey, I'm Nova 👋</h1>
        <div>Ask me anything. I'm running locally and privately on your own machine.</div>
        <div class="chips">
          <div class="chip">Who are you?</div>
          <div class="chip">Write a haiku about space</div>
          <div class="chip">Give me 3 project ideas</div>
        </div>
      </div>
    </div>
  </main>

  <footer>
    <div class="composer">
      <textarea id="input" rows="1" placeholder="Message Nova…"></textarea>
      <button class="send" id="send">Send</button>
    </div>
    <div class="hint">Nova runs on your computer with a local model — free and private.</div>
  </footer>

<script>
  const thread = document.getElementById('thread');
  const input = document.getElementById('input');
  const sendBtn = document.getElementById('send');
  const welcome = document.getElementById('welcome');
  const modelLabel = document.getElementById('model');
  const history = [];

  // Show which AI brain is connected (from /health).
  fetch('/health').then(r => r.json()).then(d => {
    modelLabel.textContent = d.ai_provider ? ('via ' + d.ai_provider) : 'ready';
  }).catch(() => { modelLabel.textContent = 'offline'; });

  function autoGrow() { input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, 160) + 'px'; }
  input.addEventListener('input', autoGrow);

  function addMessage(role, text) {
    if (welcome) welcome.remove();
    const msg = document.createElement('div');
    msg.className = 'msg ' + role;
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = role === 'user' ? 'You' : 'N';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    msg.appendChild(avatar); msg.appendChild(bubble);
    thread.appendChild(msg);
    document.getElementById('main').scrollTop = document.getElementById('main').scrollHeight;
    return bubble;
  }

  function clean(text) {
    // Some reasoning models wrap their private thoughts in <think>…</think>.
    // Hide those so the chat stays clean.
    return (text || '').replace(/<think>[\\s\\S]*?<\\/think>/g, '').trim();
  }

  async function send() {
    const text = input.value.trim();
    if (!text) return;
    input.value = ''; autoGrow();
    addMessage('user', text);
    history.push({ role: 'user', content: text });

    sendBtn.disabled = true;
    const bubble = addMessage('assistant', '');
    bubble.innerHTML = '<span class="typing"><span></span><span></span><span></span></span>';

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        bubble.textContent = '⚠️ ' + (err.detail || ('Error ' + res.status));
      } else {
        const data = await res.json();
        const reply = clean(data.content) || '(no reply)';
        bubble.textContent = reply;
        history.push({ role: 'assistant', content: reply });
      }
    } catch (e) {
      bubble.textContent = '⚠️ Could not reach Nova. Is the server running?';
    } finally {
      sendBtn.disabled = false;
      document.getElementById('main').scrollTop = document.getElementById('main').scrollHeight;
    }
  }

  sendBtn.addEventListener('click', send);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => { input.value = chip.textContent; autoGrow(); send(); });
  });
  input.focus();
</script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """The Nova chat page."""
    return HTMLResponse(INDEX_HTML)
