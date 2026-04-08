import streamlit as st


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
        .main-header {
            text-align: center;
            padding: 12px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            color: white;
            margin-bottom: 14px;
        }
        .main-header h1 {
            margin: 0;
            font-size: 1.9em;
        }
        .section-divider {
            margin: 30px 0 20px 0;
        }
        .metric-card {
            background: #f0f2f6;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        section[data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 430px;
            max-width: 430px;
        }
        section[data-testid="stSidebar"][aria-expanded="false"] {
            min-width: 0 !important;
            max-width: 0 !important;
        }
        @media (max-width: 1024px) {
            section[data-testid="stSidebar"][aria-expanded="true"] {
                min-width: 320px;
                max-width: 320px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str = "", icon_line: str = "") -> None:
    icon_markup = f"<div style='font-size: 22px; line-height: 1.1;'>{icon_line}</div>" if icon_line else ""
    subtitle_markup = f"<p style='margin: 4px 0; font-size: 0.85em;'>{subtitle}</p>" if subtitle else ""

    header_html = (
        '<div class="main-header">'
        f"{icon_markup}"
        f"<h1>{title}</h1>"
        f"{subtitle_markup}"
        "</div>"
    )

    st.markdown(
        header_html,
        unsafe_allow_html=True,
    )
