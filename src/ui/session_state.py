import streamlit as st
from src.ui.state_manager import init_state

DEFAULT_CENTER = [2.7258, 101.9424]  # Seremban, Malaysia
DEFAULT_ZOOM = 12


def init_session_state() -> None:
    init_state()
