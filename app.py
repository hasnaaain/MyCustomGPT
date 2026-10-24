import html
import os

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

try:
    from duckduckgo_search import DDGS
except ImportError:  # package renamed in newer releases
    from ddgs import DDGS

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Custom GPT",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — glassmorphism (reference: soft frosted dashboard)
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Manrope:wght@400;500;600;700&display=swap');

:root {
    --glass: rgba(28, 28, 32, 0.55);
    --glass-strong: rgba(22, 22, 26, 0.72);
    --glass-soft: rgba(255, 255, 255, 0.06);
    --glass-card: rgba(255, 255, 255, 0.08);
    --cream: #efe9df;
    --cream-dim: #d9d2c6;
    --text: #f3f1ec;
    --text-muted: rgba(243, 241, 236, 0.55);
    --border: rgba(255, 255, 255, 0.14);
    --border-soft: rgba(255, 255, 255, 0.08);
    --shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
    --radius: 28px;
    --radius-sm: 18px;
    --radius-pill: 999px;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Manrope', sans-serif !important;
    color: var(--text) !important;
}

/* Open canvas background (no framed page card) */
[data-testid="stAppViewContainer"] {
    background: #0a0a0a !important;
}
[data-testid="stAppViewContainer"]::before {
    content: none;
}
.stApp { background: #0a0a0a !important; }

#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent !important; }

h1, h2, h3, .brand-title, .gate-title, .side-brand {
    font-family: 'Outfit', sans-serif !important;
    letter-spacing: -0.03em;
    font-weight: 600 !important;
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.96); }
    to   { opacity: 1; transform: scale(1); }
}
@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-14px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes softFloat {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-5px); }
}
@keyframes glassShine {
    0%   { background-position: 0% 50%; }
    100% { background-position: 100% 50%; }
}

.anim-fade-up { animation: fadeUp 0.55s cubic-bezier(0.22, 1, 0.36, 1) both; }
.anim-fade-in { animation: fadeIn 0.4s ease both; }
.anim-scale   { animation: scaleIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }

/* Main content — no outer card (ChatGPT-style open canvas) */
[data-testid="stMain"] .block-container {
    max-width: 780px !important;
    padding: 1.2rem 1.25rem 2rem !important;
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
}

/* Glass sidebar */
section[data-testid="stSidebar"] {
    background: transparent !important;
}
section[data-testid="stSidebar"] > div {
    background: var(--glass-strong) !important;
    backdrop-filter: blur(28px) saturate(140%);
    -webkit-backdrop-filter: blur(28px) saturate(140%);
    border-right: 1px solid var(--border) !important;
    margin: 1rem 0.65rem 1rem 0.85rem !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow), inset 0 1px 0 rgba(255,255,255,0.06);
    padding-top: 1.4rem !important;
}
/* Restore Material icon fonts (a global * font rule was breaking them
   into raw text like "keyboard_double" on hover). */
[data-testid="stIconMaterial"],
.material-icons,
.material-symbols-rounded,
.material-symbols-outlined,
span[translate="no"] {
    font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
    font-style: normal !important;
    font-weight: normal !important;
    letter-spacing: normal !important;
    text-transform: none !important;
}

/* Soften the sidebar collapse control */
[data-testid="stSidebarCollapseButton"] {
    color: rgba(243, 241, 236, 0.45) !important;
}
[data-testid="stSidebarCollapseButton"]:hover {
    color: var(--cream) !important;
}

/* Onboarding glass card */
.gate-wrap {
    max-width: 440px;
    margin: 10vh auto 0;
    padding: 2.6rem 2.3rem 1.4rem;
    background: var(--glass);
    backdrop-filter: blur(32px) saturate(150%);
    -webkit-backdrop-filter: blur(32px) saturate(150%);
    border: 1px solid var(--border);
    border-radius: 32px;
    box-shadow: var(--shadow), inset 0 1px 0 rgba(255,255,255,0.1);
    animation: scaleIn 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.gate-mark {
    font-family: 'Outfit', sans-serif;
    font-size: 2.4rem;
    font-weight: 600;
    color: var(--cream);
    text-align: center;
    line-height: 1;
    animation: softFloat 3.2s ease-in-out infinite;
}
.gate-title {
    font-size: 1.9rem;
    text-align: center;
    margin: 0.7rem 0 0.4rem;
    color: var(--text);
}
.gate-sub {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.92rem;
    margin-bottom: 1.5rem;
    line-height: 1.55;
    font-weight: 400;
}
.step-pills {
    display: flex;
    gap: 0.45rem;
    justify-content: center;
    margin-bottom: 0.4rem;
}
.step-pill {
    height: 5px;
    width: 28px;
    border-radius: var(--radius-pill);
    background: rgba(255,255,255,0.12);
    transition: all 0.35s ease;
}
.step-pill.active {
    background: var(--cream);
    width: 42px;
}
.step-pill.done {
    background: var(--cream-dim);
}

/* Hero */
.brand-hero {
    text-align: center;
    padding: 3.2rem 1rem 1.8rem;
    animation: fadeUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.brand-hero .mark {
    font-family: 'Outfit', sans-serif;
    font-size: 2.6rem;
    font-weight: 600;
    color: var(--cream);
    display: block;
    margin-bottom: 0.35rem;
}
.brand-hero h1 {
    font-family: 'Outfit', sans-serif !important;
    font-size: 2.15rem !important;
    margin: 0 !important;
    color: var(--text) !important;
    font-weight: 600 !important;
}
.brand-hero p {
    color: var(--text-muted);
    font-size: 0.98rem;
    margin: 0.55rem auto 0;
    max-width: 400px;
    font-weight: 400;
}

/* Pill top bar (visual only) */
.top-pills {
    display: flex;
    justify-content: center;
    gap: 0.4rem;
    flex-wrap: wrap;
    margin: 0.2rem 0 1.2rem;
    animation: fadeUp 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.top-pill {
    font-family: 'Manrope', sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    padding: 0.45rem 1rem;
    border-radius: var(--radius-pill);
    color: var(--text-muted);
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border-soft);
    transition: all 0.25s ease;
}
.top-pill.active {
    background: var(--cream);
    color: #1a1a1e;
    border-color: transparent;
    font-weight: 600;
}

/* Chat bubbles — nested glass cards */
.msg-row {
    display: flex;
    margin: 0.9rem 0;
    animation: fadeUp 0.4s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.msg-row.human { justify-content: flex-end; }
.msg-row.ai    { justify-content: flex-start; }

.bubble {
    max-width: min(680px, 90%);
    padding: 1rem 1.2rem;
    border-radius: 22px;
    line-height: 1.55;
    font-size: 0.95rem;
    font-weight: 400;
    word-break: break-word;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.bubble:hover {
    transform: translateY(-1px);
}
.bubble.human {
    background: var(--cream);
    color: #1c1c20;
    border: none;
    border-bottom-right-radius: 8px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.18);
}
.bubble.ai {
    background: var(--glass-card);
    border: 1px solid var(--border);
    border-bottom-left-radius: 8px;
    color: var(--text);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
}
.bubble .role-tag {
    font-family: 'Outfit', sans-serif;
    font-size: 0.68rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
    font-weight: 600;
    opacity: 0.55;
}
.bubble.human .role-tag { color: #1c1c20; }
.bubble.ai .role-tag { color: var(--cream); opacity: 0.7; }

.search-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.7rem;
    font-weight: 500;
    color: #1c1c20;
    background: var(--cream);
    padding: 0.22rem 0.65rem;
    border-radius: var(--radius-pill);
    margin-bottom: 0.55rem;
    animation: fadeIn 0.45s ease both;
}

/* History */
.hist-item {
    padding: 0.75rem 0.95rem;
    margin: 0.4rem 0;
    border-radius: 14px;
    background: rgba(255,255,255,0.04);
    border: 1px solid transparent;
    color: var(--text-muted);
    font-size: 0.86rem;
    font-weight: 500;
    transition: all 0.25s ease;
    animation: slideInLeft 0.35s cubic-bezier(0.22, 1, 0.36, 1) both;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.hist-item:hover {
    background: rgba(255,255,255,0.1);
    border-color: var(--border);
    color: var(--text);
}
.hist-empty {
    color: var(--text-muted);
    font-size: 0.84rem;
    padding: 1.1rem 0.6rem;
    text-align: center;
    line-height: 1.5;
}

.composer-zone {
    max-width: 720px;
    margin: 0.8rem auto 0;
    padding: 0.4rem 0 0.6rem;
    animation: fadeUp 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.composer-hint {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.76rem;
    margin-top: 0.6rem;
    font-weight: 400;
}

/* Inputs — pill / soft glass */
.stTextInput > div > div > input,
.stTextArea textarea {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-pill) !important;
    color: var(--text) !important;
    font-family: 'Manrope', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.85rem 1.2rem !important;
    transition: border-color 0.25s, box-shadow 0.25s, background 0.25s !important;
}
.stTextArea textarea {
    border-radius: var(--radius-sm) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: rgba(239, 233, 223, 0.45) !important;
    box-shadow: 0 0 0 3px rgba(239, 233, 223, 0.12) !important;
    background: rgba(255,255,255,0.09) !important;
}
.stTextInput label, .stTextArea label, .stCheckbox label, .stToggle label,
[data-testid="stWidgetLabel"] p {
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    font-family: 'Manrope', sans-serif !important;
}

/* Cream primary buttons (reference active pills) */
div[data-testid="stButton"] > button,
div[data-testid="stFormSubmitButton"] > button {
    background: var(--cream) !important;
    color: #1a1a1e !important;
    border: none !important;
    border-radius: var(--radius-pill) !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
    padding: 0.65rem 1.5rem !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.2) !important;
}
div[data-testid="stButton"] > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-2px) !important;
    background: #f7f3ec !important;
    box-shadow: 0 10px 28px rgba(0,0,0,0.28) !important;
}
div[data-testid="stButton"] > button[kind="secondary"] {
    background: rgba(255,255,255,0.06) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    box-shadow: none !important;
}
div[data-testid="stButton"] > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.12) !important;
}

.side-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 1.35rem 0 0.55rem;
    font-weight: 600;
}
.side-brand {
    font-size: 1.2rem;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.side-brand span {
    display: inline-flex;
    width: 32px;
    height: 32px;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: var(--cream);
    color: #1a1a1e;
    font-size: 0.95rem;
}

.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.74rem;
    font-weight: 500;
    color: var(--text-muted);
    margin-top: 0.55rem;
    padding: 0.3rem 0.7rem;
    border-radius: var(--radius-pill);
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border-soft);
}
.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #7dcea0;
    box-shadow: 0 0 8px rgba(125, 206, 160, 0.6);
}

.stSpinner > div {
    border-top-color: var(--cream) !important;
}

/* Soft settings card in sidebar */
.settings-card {
    margin-top: 0.6rem;
    padding: 0.9rem;
    border-radius: var(--radius-sm);
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border-soft);
    animation: fadeUp 0.45s ease both;
}

div[data-baseweb="notification"], .stAlert {
    border-radius: 16px !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def _init_state() -> None:
    defaults = {
        "api_key": "",
        "authenticated": False,
        "messages": [],
        "system_role": "You are a helpful, concise assistant. When web search results are provided, use them to give up-to-date answers and cite sources briefly.",
        "web_search": True,
        "pending_prompt": None,
        "onboard_step": 1,  # 1 = API key, 2 = system role, 3 = ready
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ---------------------------------------------------------------------------
# Web search (DuckDuckGo — no extra API key)
# ---------------------------------------------------------------------------
def browser_search(query: str, max_results: int = 5) -> str:
    """Fetch fresh web snippets so the model can answer with current info."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No web results found."
        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            body = r.get("body", "")
            href = r.get("href", "")
            lines.append(f"{i}. {title}\n   {body}\n   Source: {href}")
        return "\n\n".join(lines)
    except Exception as exc:  # noqa: BLE001 — surface search failures to the model
        return f"Web search unavailable ({exc}). Answer from your knowledge and note the limitation."


def ensure_system_message() -> None:
    msgs = st.session_state.messages
    role = st.session_state.system_role.strip() or "You are a helpful assistant."
    if not msgs:
        msgs.append(SystemMessage(content=role))
        return
    if isinstance(msgs[0], SystemMessage):
        msgs[0] = SystemMessage(content=role)
    else:
        msgs.insert(0, SystemMessage(content=role))


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.5,
        api_key=st.session_state.api_key,
    )


def run_chat_turn(user_text: str) -> None:
    ensure_system_message()
    st.session_state.messages.append(HumanMessage(content=user_text))

    invoke_messages = list(st.session_state.messages)
    used_search = False

    if st.session_state.web_search:
        with st.spinner("Searching the web for latest updates…"):
            snippets = browser_search(user_text)
        used_search = True
        search_context = (
            "Live web search results (use these for current facts; cite briefly):\n\n"
            f"{snippets}\n\n"
            f"User question: {user_text}"
        )
        # Inject as a temporary HumanMessage so the model sees fresh context
        # without permanently polluting history with raw search dumps.
        invoke_messages = invoke_messages[:-1] + [
            HumanMessage(content=search_context)
        ]

    with st.spinner("Thinking…"):
        response = get_llm().invoke(invoke_messages)

    content = response.content
    if used_search:
        # Store a lightweight flag via prefix the UI can detect
        st.session_state.messages.append(
            AIMessage(content=content, additional_kwargs={"web_search": True})
        )
    else:
        st.session_state.messages.append(AIMessage(content=content))


# ---------------------------------------------------------------------------
# Onboarding: API key → system role → enter chat
# ---------------------------------------------------------------------------
def render_onboarding() -> None:
    step = st.session_state.onboard_step

    pills = []
    for i in range(1, 4):
        cls = "step-pill"
        if i < step:
            cls += " done"
        elif i == step:
            cls += " active"
        pills.append(f'<div class="{cls}"></div>')

    st.markdown(
        f"""
        <div class="gate-wrap">
            <div class="gate-mark">◈</div>
            <div class="gate-title">Custom GPT</div>
            <div class="gate-sub">Frosted chat with live web search.<br>Set up once — then ask anything.</div>
            <div class="step-pills">{"".join(pills)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Align form under the card
    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        if step == 1:
            st.markdown(
                '<div class="anim-fade-up"><p style="color:rgba(243,241,236,0.55);text-align:center;margin-bottom:0.5rem;font-family:Manrope,sans-serif;font-size:0.9rem;">Step 1 — OpenAI API key</p></div>',
                unsafe_allow_html=True,
            )
            key = st.text_input(
                "OpenAI API key",
                type="password",
                placeholder="sk-…",
                label_visibility="collapsed",
                key="gate_api_key",
            )
            if st.button("Continue", use_container_width=True, key="btn_step1"):
                if not key or not key.strip().startswith("sk-"):
                    st.error("Enter a valid OpenAI API key starting with sk-")
                else:
                    st.session_state.api_key = key.strip()
                    os.environ["OPENAI_API_KEY"] = key.strip()
                    st.session_state.onboard_step = 2
                    st.rerun()

        elif step == 2:
            st.markdown(
                '<div class="anim-fade-up"><p style="color:rgba(243,241,236,0.55);text-align:center;margin-bottom:0.5rem;font-family:Manrope,sans-serif;font-size:0.9rem;">Step 2 — How should the assistant behave?</p></div>',
                unsafe_allow_html=True,
            )
            role = st.text_area(
                "System role",
                value=st.session_state.system_role,
                height=110,
                label_visibility="collapsed",
                key="gate_system_role",
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Back", use_container_width=True, type="secondary", key="btn_back2"):
                    st.session_state.onboard_step = 1
                    st.rerun()
            with c2:
                if st.button("Continue", use_container_width=True, key="btn_step2"):
                    st.session_state.system_role = (role or "").strip() or st.session_state.system_role
                    st.session_state.onboard_step = 3
                    st.rerun()

        elif step == 3:
            st.markdown(
                '<div class="anim-fade-up anim-scale"><p style="color:rgba(243,241,236,0.55);text-align:center;margin-bottom:0.85rem;font-family:Manrope,sans-serif;font-size:0.9rem;">You\'re ready. Web search is on by default so answers stay current.</p></div>',
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Back", use_container_width=True, type="secondary", key="btn_back3"):
                    st.session_state.onboard_step = 2
                    st.rerun()
            with c2:
                if st.button("Enter chat", use_container_width=True, key="btn_enter"):
                    st.session_state.authenticated = True
                    ensure_system_message()
                    st.rerun()


# ---------------------------------------------------------------------------
# Main chat UI
# ---------------------------------------------------------------------------
def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="side-brand anim-fade-in"><span>◈</span> Custom GPT</div>'
            '<div class="status-chip"><span class="status-dot"></span> Connected</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="side-label">History</div>', unsafe_allow_html=True)

        human_turns = [
            m for m in st.session_state.messages if isinstance(m, HumanMessage)
        ]
        if not human_turns:
            st.markdown(
                '<div class="hist-empty">No conversations yet.<br>Your prompts will appear here.</div>',
                unsafe_allow_html=True,
            )
        else:
            for i, msg in enumerate(human_turns):
                preview = msg.content.strip().replace("\n", " ")
                if len(preview) > 48:
                    preview = preview[:48] + "…"
                delay = min(i, 6) * 0.04
                st.markdown(
                    f'<div class="hist-item" style="animation-delay:{delay}s">'
                    f"{html.escape(preview)}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown('<div class="side-label">Settings</div>', unsafe_allow_html=True)
        st.markdown('<div class="settings-card">', unsafe_allow_html=True)

        st.session_state.web_search = st.toggle(
            "Browser search",
            value=st.session_state.web_search,
            help="Fetches DuckDuckGo results before each reply so the model sees current information.",
        )

        new_role = st.text_area(
            "System role",
            value=st.session_state.system_role,
            height=90,
            key="sidebar_system_role",
        )
        if new_role != st.session_state.system_role:
            st.session_state.system_role = new_role
            ensure_system_message()

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("New chat", use_container_width=True, type="secondary"):
            st.session_state.messages = []
            ensure_system_message()
            st.rerun()

        if st.button("Change API key", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            st.session_state.onboard_step = 1
            st.rerun()


def render_messages() -> None:
    visible = [
        m
        for m in st.session_state.messages
        if isinstance(m, (HumanMessage, AIMessage))
    ]

    st.markdown(
        """
        <div class="top-pills">
            <span class="top-pill active">Chat</span>
            <span class="top-pill">History</span>
            <span class="top-pill">Search</span>
            <span class="top-pill">Settings</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not visible:
        st.markdown(
            """
            <div class="brand-hero">
                <span class="mark">◈</span>
                <h1>Custom GPT</h1>
                <p>Ask anything. Browser search keeps answers current with live web results.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for msg in visible:
        body = html.escape(msg.content).replace("\n", "<br>")
        if isinstance(msg, HumanMessage):
            st.markdown(
                f"""
                <div class="msg-row human">
                    <div class="bubble human">
                        <div class="role-tag">You</div>
                        {body}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif isinstance(msg, AIMessage):
            searched = bool(msg.additional_kwargs.get("web_search"))
            badge = (
                '<div class="search-badge">Live web search</div>'
                if searched
                else ""
            )
            st.markdown(
                f"""
                <div class="msg-row ai">
                    <div class="bubble ai">
                        <div class="role-tag">Assistant</div>
                        {badge}
                        {body}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_composer() -> None:
    st.markdown('<div class="composer-zone">', unsafe_allow_html=True)

    with st.form("composer", clear_on_submit=True):
        prompt = st.text_input(
            "Message",
            placeholder="Send a message…",
            label_visibility="collapsed",
            key="center_prompt",
        )
        sent = st.form_submit_button("Send", use_container_width=True)

    st.markdown(
        '<p class="composer-hint">Enter to send · Browser search adds live context when enabled</p></div>',
        unsafe_allow_html=True,
    )

    if sent and prompt and prompt.strip():
        run_chat_turn(prompt.strip())
        st.rerun()


# ---------------------------------------------------------------------------
# App entry
# ---------------------------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
        [data-testid="stMain"] .block-container {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            backdrop-filter: none !important;
            margin-top: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    render_onboarding()
else:
    render_sidebar()
    render_messages()
    render_composer()
