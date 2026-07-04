"""Serves Nova's public website homepage at GET /

This is the "storefront": hero section, features, how-it-works, and Free/Pro
pricing. Like the chat page, it's one self-contained HTML string — no build
step, no external files, ships with the package.

The "Upgrade to Pro" button is intentionally honest: Pro doesn't exist yet, so
it opens a "coming soon" note instead of pretending to charge money.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])

GITHUB_URL = "https://github.com/gabed5303-ops/NovaAI-"

# Plain string (NOT an f-string) so CSS/JS braces are left alone.
LANDING_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="description" content="Nova — a private, JARVIS-inspired AI assistant that runs on your own machine. Open source, plugin-ready, free." />
<title>Nova — your private AI assistant</title>
<style>
  :root {
    --bg: #0b0d12;
    --panel: #141821;
    --panel-2: #1b2130;
    --text: #e8ecf3;
    --muted: #8b93a7;
    --accent: #6c8cff;
    --accent-2: #33d6c8;
    --border: #232a3a;
    --radius: 16px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    overflow-x: hidden; line-height: 1.6;
  }
  a { color: inherit; text-decoration: none; }

  /* ambient glow orbs */
  .orb { position: fixed; border-radius: 50%; filter: blur(90px); opacity: .35; pointer-events: none; z-index: 0; }
  .orb.one { width: 480px; height: 480px; background: #2b3f8f; top: -160px; left: -120px; }
  .orb.two { width: 420px; height: 420px; background: #0f5f58; top: 30%; right: -160px; }
  .orb.three { width: 380px; height: 380px; background: #3a2b8f; bottom: -140px; left: 30%; }

  .wrap { position: relative; z-index: 1; max-width: 1080px; margin: 0 auto; padding: 0 22px; }

  /* ---------- nav ---------- */
  nav {
    position: sticky; top: 0; z-index: 10;
    backdrop-filter: blur(14px); background: rgba(11,13,18,.72);
    border-bottom: 1px solid var(--border);
  }
  .nav-inner { display: flex; align-items: center; gap: 26px; padding: 14px 0; }
  .logo { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 18px; }
  .logo-mark {
    width: 32px; height: 32px; border-radius: 9px; display: grid; place-items: center;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    color: #0b0d12; font-weight: 900;
  }
  .nav-links { display: flex; gap: 22px; margin-left: auto; align-items: center; }
  .nav-links a { color: var(--muted); font-size: 14.5px; transition: color .2s; }
  .nav-links a:hover { color: var(--text); }
  .btn {
    display: inline-flex; align-items: center; gap: 8px; cursor: pointer;
    border-radius: 12px; padding: 11px 20px; font-weight: 700; font-size: 15px;
    border: 1px solid var(--border); background: var(--panel); color: var(--text);
    transition: transform .15s, box-shadow .2s, border-color .2s;
  }
  .btn:hover { transform: translateY(-1px); border-color: var(--accent); }
  .btn.primary {
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    color: #0b0d12; border: 0;
  }
  .btn.primary:hover { box-shadow: 0 8px 30px rgba(108,140,255,.35); }
  .btn.small { padding: 9px 16px; font-size: 14px; }

  /* ---------- hero ---------- */
  .hero { padding: 84px 0 40px; display: grid; grid-template-columns: 1.1fr .9fr; gap: 48px; align-items: center; }
  .badge {
    display: inline-flex; align-items: center; gap: 8px;
    border: 1px solid var(--border); background: var(--panel);
    color: var(--muted); font-size: 12.5px; font-weight: 600;
    padding: 6px 12px; border-radius: 999px; margin-bottom: 18px;
  }
  .badge .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--accent-2); box-shadow: 0 0 8px var(--accent-2); }
  h1 { font-size: clamp(34px, 5vw, 54px); line-height: 1.12; letter-spacing: -1px; font-weight: 800; }
  h1 .grad {
    background: linear-gradient(95deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .hero p.sub { color: var(--muted); font-size: 18px; margin: 18px 0 28px; max-width: 480px; }
  .hero-ctas { display: flex; gap: 12px; flex-wrap: wrap; }
  .trust { display: flex; gap: 18px; flex-wrap: wrap; margin-top: 30px; color: var(--muted); font-size: 13px; }
  .trust span { display: flex; align-items: center; gap: 6px; }

  /* hero chat mock */
  .mock {
    background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius);
    box-shadow: 0 30px 80px rgba(0,0,0,.5); overflow: hidden;
    transform: rotate(1.5deg); transition: transform .4s;
  }
  .mock:hover { transform: rotate(0deg) scale(1.01); }
  .mock-bar { display: flex; gap: 6px; padding: 12px 14px; border-bottom: 1px solid var(--border); background: var(--panel-2); }
  .mock-bar i { width: 10px; height: 10px; border-radius: 50%; background: #2c3550; }
  .mock-bar i:first-child { background: #ff6058; } .mock-bar i:nth-child(2) { background: #ffbd2e; } .mock-bar i:nth-child(3) { background: #28ca41; }
  .mock-body { padding: 18px; display: flex; flex-direction: column; gap: 12px; font-size: 13.5px; }
  .mb { padding: 10px 13px; border-radius: 11px; max-width: 85%; line-height: 1.5; }
  .mb.user { align-self: flex-end; background: linear-gradient(135deg, var(--accent), #7a5cff); color: #fff; border-bottom-right-radius: 4px; }
  .mb.nova { align-self: flex-start; background: var(--panel-2); border: 1px solid var(--border); border-bottom-left-radius: 4px; }
  .mb.nova b { color: var(--accent-2); }

  /* ---------- sections ---------- */
  section { padding: 72px 0; }
  .sec-head { text-align: center; max-width: 560px; margin: 0 auto 44px; }
  .sec-head h2 { font-size: clamp(26px, 3.5vw, 36px); letter-spacing: -.5px; margin-bottom: 10px; }
  .sec-head p { color: var(--muted); font-size: 16px; }
  .eyebrow { color: var(--accent-2); font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; }

  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; }
  .card {
    background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 26px; transition: transform .2s, border-color .2s;
  }
  .card:hover { transform: translateY(-4px); border-color: #35406060; }
  .card .icon {
    width: 44px; height: 44px; border-radius: 12px; display: grid; place-items: center;
    font-size: 21px; background: var(--panel-2); border: 1px solid var(--border); margin-bottom: 16px;
  }
  .card h3 { font-size: 17px; margin-bottom: 8px; }
  .card p { color: var(--muted); font-size: 14.5px; }

  /* steps */
  .steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; }
  .step { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 26px; position: relative; }
  .step .num {
    position: absolute; top: -14px; left: 22px; width: 28px; height: 28px; border-radius: 50%;
    display: grid; place-items: center; font-size: 13px; font-weight: 800; color: #0b0d12;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
  }
  .step h3 { font-size: 16px; margin: 6px 0 8px; }
  .step p { color: var(--muted); font-size: 14px; margin-bottom: 12px; }
  code.block {
    display: block; background: #0d1017; border: 1px solid var(--border); border-radius: 10px;
    padding: 11px 14px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 13px; color: var(--accent-2); overflow-x: auto; white-space: nowrap;
  }

  /* pricing */
  .plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 22px; max-width: 760px; margin: 0 auto; }
  .plan { background: var(--panel); border: 1px solid var(--border); border-radius: 20px; padding: 32px; display: flex; flex-direction: column; }
  .plan.pro { border: 1px solid transparent; background:
      linear-gradient(var(--panel), var(--panel)) padding-box,
      linear-gradient(135deg, var(--accent), var(--accent-2)) border-box; position: relative; }
  .plan .tag {
    position: absolute; top: -13px; right: 24px; font-size: 11.5px; font-weight: 800;
    letter-spacing: 1px; text-transform: uppercase; color: #0b0d12; padding: 5px 12px;
    border-radius: 999px; background: linear-gradient(135deg, var(--accent), var(--accent-2));
  }
  .plan h3 { font-size: 18px; }
  .price { font-size: 42px; font-weight: 800; margin: 14px 0 2px; letter-spacing: -1px; }
  .price small { font-size: 15px; font-weight: 600; color: var(--muted); letter-spacing: 0; }
  .plan .desc { color: var(--muted); font-size: 14px; margin-bottom: 22px; }
  .plan ul { list-style: none; display: flex; flex-direction: column; gap: 11px; margin-bottom: 26px; font-size: 14.5px; }
  .plan li { display: flex; gap: 10px; align-items: flex-start; }
  .plan li .tick { color: var(--accent-2); font-weight: 800; }
  .plan li.soon { color: var(--muted); }
  .plan .btn { margin-top: auto; justify-content: center; }

  /* CTA band */
  .cta-band {
    text-align: center; border: 1px solid var(--border); border-radius: 24px;
    padding: 56px 30px; background:
      radial-gradient(600px 200px at 50% 0%, rgba(108,140,255,.14), transparent),
      var(--panel);
  }
  .cta-band h2 { font-size: clamp(24px, 3vw, 34px); margin-bottom: 10px; }
  .cta-band p { color: var(--muted); margin-bottom: 26px; }

  footer { border-top: 1px solid var(--border); padding: 34px 0 44px; margin-top: 40px; }
  .foot { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; color: var(--muted); font-size: 13.5px; }
  .foot .logo { font-size: 15px; color: var(--text); }
  .foot .links { margin-left: auto; display: flex; gap: 18px; }
  .foot a:hover { color: var(--text); }

  /* reveal on scroll */
  .reveal { opacity: 0; transform: translateY(18px); transition: opacity .6s, transform .6s; }
  .reveal.visible { opacity: 1; transform: none; }

  /* modal */
  .modal-bg { position: fixed; inset: 0; background: rgba(5,7,10,.7); backdrop-filter: blur(4px);
              display: none; place-items: center; z-index: 50; }
  .modal-bg.open { display: grid; }
  .modal { background: var(--panel); border: 1px solid var(--border); border-radius: 18px;
           padding: 34px; max-width: 400px; margin: 20px; text-align: center; }
  .modal .icon-big { font-size: 40px; margin-bottom: 14px; }
  .modal h3 { margin-bottom: 10px; }
  .modal p { color: var(--muted); font-size: 14.5px; margin-bottom: 22px; }

  @media (max-width: 860px) {
    .hero { grid-template-columns: 1fr; padding-top: 56px; text-align: center; }
    .hero p.sub { margin-left: auto; margin-right: auto; }
    .hero-ctas, .trust { justify-content: center; }
    .mock { max-width: 460px; margin: 0 auto; }
    .nav-links a.hide-m { display: none; }
  }
</style>
</head>
<body>
  <div class="orb one"></div><div class="orb two"></div><div class="orb three"></div>

  <nav>
    <div class="wrap nav-inner">
      <a class="logo" href="/"><span class="logo-mark">N</span> Nova</a>
      <div class="nav-links">
        <a href="#features" class="hide-m">Features</a>
        <a href="#how" class="hide-m">How it works</a>
        <a href="#pricing">Pricing</a>
        <a href="__GITHUB__" target="_blank" rel="noopener" class="hide-m">GitHub</a>
        <a class="btn primary small" href="/chat">Open Chat →</a>
      </div>
    </div>
  </nav>

  <header class="wrap hero">
    <div>
      <div class="badge"><span class="dot"></span> Open source · MIT licensed · v0.3</div>
      <h1>Meet <span class="grad">Nova</span> — your private, JARVIS-inspired AI.</h1>
      <p class="sub">An AI assistant that runs on <b>your own machine</b>. Your conversations never
      leave your computer. Free forever, endlessly extendable with plugins.</p>
      <div class="hero-ctas">
        <a class="btn primary" href="/chat">Start chatting — it's free</a>
        <a class="btn" href="__GITHUB__" target="_blank" rel="noopener">⭐ View on GitHub</a>
      </div>
      <div class="trust">
        <span>🔒 100% local &amp; private</span>
        <span>🧩 Plugin-ready</span>
        <span>💻 macOS · Linux · Windows</span>
      </div>
    </div>
    <div class="mock">
      <div class="mock-bar"><i></i><i></i><i></i></div>
      <div class="mock-body">
        <div class="mb user">Who are you?</div>
        <div class="mb nova"><b>Nova</b> — your personal AI assistant, running locally and privately on your own computer. How can I help? 🚀</div>
        <div class="mb user">Is my data safe?</div>
        <div class="mb nova">Completely. Everything happens on this machine — nothing is sent to the cloud. 🔒</div>
      </div>
    </div>
  </header>

  <section id="features" class="wrap">
    <div class="sec-head reveal">
      <div class="eyebrow">Features</div>
      <h2>Everything an assistant should be</h2>
      <p>Built on a clean, modular architecture designed to grow for years.</p>
    </div>
    <div class="grid">
      <div class="card reveal"><div class="icon">🔒</div><h3>Private by design</h3>
        <p>Runs entirely on your machine with a local AI model. Your chats never touch a server you don't own.</p></div>
      <div class="card reveal"><div class="icon">🧠</div><h3>Local &amp; cloud brains</h3>
        <p>Use free local models via Ollama, or flip one setting to use Anthropic Claude in the cloud. Same Nova either way.</p></div>
      <div class="card reveal"><div class="icon">🧩</div><h3>Plugin system</h3>
        <p>Teach Nova new abilities by dropping in a plugin file — commands are auto-discovered at startup. No core changes.</p></div>
      <div class="card reveal"><div class="icon">💾</div><h3>Built-in memory</h3>
        <p>A memory module with swappable storage backends, so Nova can remember facts between conversations.</p></div>
      <div class="card reveal"><div class="icon">🎙️</div><h3>Voice-ready</h3>
        <p>Speech-to-text and text-to-speech interfaces are wired end-to-end, ready for engines like Whisper and Piper.</p></div>
      <div class="card reveal"><div class="icon">⚡</div><h3>Modern core</h3>
        <p>Async Python, FastAPI, typed settings, an event bus, tests, and CI. Production-quality foundations, not a hack.</p></div>
    </div>
  </section>

  <section id="how" class="wrap">
    <div class="sec-head reveal">
      <div class="eyebrow">How it works</div>
      <h2>Running in three commands</h2>
      <p>If you can copy &amp; paste, you can run Nova.</p>
    </div>
    <div class="steps">
      <div class="step reveal"><div class="num">1</div><h3>Get the code</h3>
        <p>Clone the open-source repo from GitHub.</p>
        <code class="block">git clone __GITHUB__.git</code></div>
      <div class="step reveal"><div class="num">2</div><h3>Install</h3>
        <p>One command installs everything into a local environment.</p>
        <code class="block">uv sync</code></div>
      <div class="step reveal"><div class="num">3</div><h3>Launch</h3>
        <p>Start Nova and open it in your browser.</p>
        <code class="block">uv run nova</code></div>
    </div>
  </section>

  <section id="pricing" class="wrap">
    <div class="sec-head reveal">
      <div class="eyebrow">Pricing</div>
      <h2>Free where it counts</h2>
      <p>Nova is open source. Run it yourself for free, forever. A hosted Pro tier is on the roadmap.</p>
    </div>
    <div class="plans">
      <div class="plan reveal">
        <h3>Free</h3>
        <div class="price">$0 <small>forever</small></div>
        <div class="desc">Run Nova on your own computer.</div>
        <ul>
          <li><span class="tick">✓</span> Unlimited local chat</li>
          <li><span class="tick">✓</span> 100% private — data stays on your machine</li>
          <li><span class="tick">✓</span> Full plugin &amp; command system</li>
          <li><span class="tick">✓</span> Local AI via Ollama</li>
          <li><span class="tick">✓</span> Open source (MIT)</li>
        </ul>
        <a class="btn" href="/chat">Start free</a>
      </div>
      <div class="plan pro reveal">
        <div class="tag">Coming soon</div>
        <h3>Pro</h3>
        <div class="price">$5 <small>/ month</small></div>
        <div class="desc">Nova, hosted for you — no setup at all.</div>
        <ul>
          <li class="soon"><span class="tick">✓</span> Hosted cloud AI — chat from any device</li>
          <li class="soon"><span class="tick">✓</span> Memory synced across devices</li>
          <li class="soon"><span class="tick">✓</span> Voice conversations</li>
          <li class="soon"><span class="tick">✓</span> Priority features &amp; support</li>
        </ul>
        <button class="btn primary" id="proBtn">Join the waitlist</button>
      </div>
    </div>
  </section>

  <section class="wrap">
    <div class="cta-band reveal">
      <h2>Ready to meet Nova?</h2>
      <p>It's free, it's private, and it's already running on your machine.</p>
      <a class="btn primary" href="/chat">Open the chat →</a>
    </div>
  </section>

  <footer>
    <div class="wrap foot">
      <a class="logo" href="/"><span class="logo-mark" style="width:26px;height:26px;font-size:13px;">N</span> Nova</a>
      <span>© 2026 · MIT License</span>
      <div class="links">
        <a href="#features">Features</a>
        <a href="#pricing">Pricing</a>
        <a href="__GITHUB__" target="_blank" rel="noopener">GitHub</a>
        <a href="/docs">API</a>
      </div>
    </div>
  </footer>

  <div class="modal-bg" id="modal">
    <div class="modal">
      <div class="icon-big">🚧</div>
      <h3>Pro is coming soon</h3>
      <p>Nova Pro (hosted, with sync and voice) is still being built. For now, the Free
         tier gives you everything — running privately on your own machine.</p>
      <button class="btn primary" id="modalClose">Got it</button>
    </div>
  </div>

<script>
  // Reveal-on-scroll animation.
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); } });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));

  // "Pro" waitlist modal (honest coming-soon, no fake checkout).
  const modal = document.getElementById('modal');
  document.getElementById('proBtn').addEventListener('click', () => modal.classList.add('open'));
  document.getElementById('modalClose').addEventListener('click', () => modal.classList.remove('open'));
  modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.remove('open'); });
</script>
</body>
</html>
"""

# Inject the GitHub URL (plain replace keeps the big template a non-f-string).
LANDING_HTML = LANDING_HTML.replace("__GITHUB__", GITHUB_URL)


@router.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    """Nova's public homepage."""
    return HTMLResponse(LANDING_HTML)
