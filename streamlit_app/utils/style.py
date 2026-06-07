"""design system injection helper.

TODO migration:
  When porting the UI to TypeScript / Vue, delete this file and replace
  ``inject_design_system()`` with ``import './styles/tokens.css'`` in the
  Vue entry file. The two CSS files (``assets/design_tokens.css`` and
  ``assets/global.css``) are framework-agnostic and can be copied
  verbatim into ``web/src/styles/``.
"""

from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
GLOBAL_CSS = ASSETS_DIR / "global.css"


@st.cache_data(show_spinner=False)
def _read_global_css() -> str:
    if not GLOBAL_CSS.exists():
        return ""
    return GLOBAL_CSS.read_text(encoding="utf-8")


def inject_design_system() -> None:
    """Read ``assets/global.css`` and inject it as a global ``<style>`` block.

    Safe to call multiple times: Streamlit re-runs the script on every
    interaction, but the CSS content is cached and the injected block
    replaces the previous one without compounding side effects.
    """
    css = _read_global_css()
    if not css:
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
