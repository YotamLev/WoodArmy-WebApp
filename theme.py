import json

import streamlit as st
import streamlit.components.v1 as components

THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Frank+Ruhl+Libre:wght@300;400;600&display=swap');

:root {
  --wa-forest-deep: #0f1a14;
  --wa-forest-mid: #1a2b22;
  --wa-forest-light: #243529;
  --wa-moss: #6b8f71;
  --wa-brass: #c9a227;
  --wa-brass-dim: #8b6914;
  --wa-copper: #b87333;
  --wa-parchment: #e8dfc8;
  --wa-parchment-dim: #a39e8f;
  --wa-rain: #4a6670;
  --wa-fog: rgba(74, 102, 112, 0.12);
}

.stApp {
  background:
    radial-gradient(ellipse at 15% 0%, rgba(107, 143, 113, 0.14) 0%, transparent 45%),
    radial-gradient(ellipse at 85% 20%, rgba(74, 102, 112, 0.18) 0%, transparent 40%),
    linear-gradient(180deg, #0a120e 0%, var(--wa-forest-deep) 35%, #121f19 100%);
  font-family: "Frank Ruhl Libre", "Times New Roman", serif;
  color: var(--wa-parchment);
}

.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image:
    repeating-linear-gradient(
      105deg,
      transparent,
      transparent 2px,
      rgba(74, 102, 112, 0.03) 2px,
      rgba(74, 102, 112, 0.03) 3px
    );
  opacity: 0.55;
  z-index: 0;
}

.block-container {
  position: relative;
  z-index: 1;
  padding-top: 1.5rem;
  max-width: 1100px;
}

h1, h2, h3, h4,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2 {
  font-family: "Cinzel", "Frank Ruhl Libre", serif !important;
  color: var(--wa-parchment) !important;
  letter-spacing: 0.04em;
}

h1 {
  text-shadow: 0 2px 18px rgba(0, 0, 0, 0.45);
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #141f19 0%, #0d1612 100%);
  border-right: 1px solid rgba(201, 162, 39, 0.25);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.35);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
  color: var(--wa-parchment) !important;
}

[data-testid="stMetric"] {
  background: linear-gradient(145deg, rgba(36, 53, 41, 0.95), rgba(26, 43, 34, 0.9));
  border: 1px solid rgba(201, 162, 39, 0.35);
  border-radius: 6px;
  padding: 0.85rem 1rem;
  box-shadow:
    inset 0 1px 0 rgba(232, 223, 200, 0.06),
    0 8px 24px rgba(0, 0, 0, 0.25);
}

[data-testid="stMetricLabel"] {
  font-family: "Cinzel", serif !important;
  font-size: 0.78rem !important;
  color: var(--wa-moss) !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

[data-testid="stMetricValue"] {
  font-family: "Frank Ruhl Libre", serif !important;
  color: var(--wa-brass) !important;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 0.5rem;
  background: transparent;
  border-bottom: 1px solid rgba(201, 162, 39, 0.2);
}

.stTabs [data-baseweb="tab"] {
  font-family: "Cinzel", serif;
  color: var(--wa-parchment-dim);
  background: rgba(26, 43, 34, 0.6);
  border: 1px solid rgba(201, 162, 39, 0.15);
  border-radius: 6px 6px 0 0;
  padding: 0.55rem 1.25rem;
  letter-spacing: 0.06em;
}

.stTabs [aria-selected="true"] {
  color: var(--wa-brass) !important;
  background: rgba(36, 53, 41, 0.95) !important;
  border-color: rgba(201, 162, 39, 0.45) !important;
  box-shadow: 0 -2px 12px rgba(201, 162, 39, 0.12);
}

[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
  border: 1px solid rgba(201, 162, 39, 0.28);
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.28);
}

div[data-testid="stAlert"] {
  border-radius: 6px;
  border: 1px solid rgba(201, 162, 39, 0.25);
  background: rgba(36, 53, 41, 0.85) !important;
  color: var(--wa-parchment) !important;
}

.stButton > button {
  font-family: "Cinzel", serif;
  letter-spacing: 0.05em;
  border: 1px solid var(--wa-brass-dim) !important;
  background: linear-gradient(180deg, #3d4f3a 0%, #2a3b30 100%) !important;
  color: var(--wa-parchment) !important;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.stButton > button:hover {
  border-color: var(--wa-brass) !important;
  box-shadow: 0 0 14px rgba(201, 162, 39, 0.25);
  color: var(--wa-brass) !important;
}

.stButton > button[kind="primary"] {
  background: linear-gradient(180deg, #8b6914 0%, #6b4f10 100%) !important;
  border-color: var(--wa-brass) !important;
  color: #1a1208 !important;
  font-weight: 700;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stSelectbox > div > div {
  background-color: rgba(15, 26, 20, 0.85) !important;
  color: var(--wa-parchment) !important;
  border-color: rgba(201, 162, 39, 0.25) !important;
  border-radius: 4px;
}

.wa-banner {
  text-align: center;
  margin: 0 0 1.75rem;
  padding: 1.35rem 1rem 1.1rem;
  border: 1px solid rgba(201, 162, 39, 0.35);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(36, 53, 41, 0.92), rgba(20, 31, 25, 0.95)),
    repeating-linear-gradient(
      90deg,
      transparent,
      transparent 24px,
      rgba(201, 162, 39, 0.04) 24px,
      rgba(201, 162, 39, 0.04) 25px
    );
  box-shadow:
    inset 0 1px 0 rgba(232, 223, 200, 0.07),
    0 12px 40px rgba(0, 0, 0, 0.35);
}

.wa-banner-eyebrow {
  font-family: "Cinzel", serif;
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--wa-moss);
  margin-bottom: 0.55rem;
}

.wa-banner-title {
  font-family: "Cinzel", serif;
  font-size: clamp(1.6rem, 3vw, 2.35rem);
  font-weight: 700;
  color: var(--wa-parchment);
  margin: 0 0 0.45rem;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.5);
}

.wa-banner-subtitle {
  font-family: "Frank Ruhl Libre", serif;
  font-size: 1.02rem;
  line-height: 1.65;
  color: var(--wa-parchment-dim);
  max-width: 720px;
  margin: 0 auto;
}

.wa-banner-rule {
  width: 120px;
  height: 2px;
  margin: 0.85rem auto 0;
  background: linear-gradient(90deg, transparent, var(--wa-brass), transparent);
}

.wa-footer {
  text-align: center;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(201, 162, 39, 0.15);
  font-family: "Cinzel", serif;
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  color: var(--wa-parchment-dim);
  opacity: 0.75;
}

.wa-section-label {
  font-family: "Cinzel", serif;
  font-size: 0.75rem;
  letter-spacing: 0.14em;
  color: var(--wa-moss);
  margin-bottom: 0.25rem;
}
"""


def apply_theme() -> None:
    css = json.dumps(THEME_CSS)
    components.html(
        f"""
        <script>
        (function () {{
            const doc = window.parent.document;
            if (doc.getElementById("wa-theme-style")) return;
            const style = doc.createElement("style");
            style.id = "wa-theme-style";
            style.textContent = {css};
            doc.head.appendChild(style);
        }})();
        </script>
        """,
        height=0,
    )


def render_banner(content: dict) -> None:
    title = content.get("title", "ריקשה — יומן המשלחת")
    subtitle = content.get("subtitle", "")
    tagline = content.get("tagline", "☙ חברת הרייקשה ☙")

    st.markdown(
        f"""
<div class="wa-banner">
  <div class="wa-banner-eyebrow">{tagline}</div>
  <div class="wa-banner-title">{title}</div>
  <div class="wa-banner-subtitle">{subtitle}</div>
  <div class="wa-banner-rule"></div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        '<div class="wa-footer">יער רטוב · נחושת וברזל · דרך הרייקשה</div>',
        unsafe_allow_html=True,
    )
