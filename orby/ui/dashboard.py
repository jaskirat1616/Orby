"""Web dashboard for Orby using Streamlit-like interface."""
import streamlit as st
import asyncio
from pathlib import Path
from typing import Dict, List
import json
from datetime import datetime
from ..model_management import model_manager
from ..ui.enhanced_ui import ui
from ..utils.session import session_manager


class OrbyDashboard:
    """Web dashboard for Orby."""
    
    def __init__(self):
        self.title = "Orby Dashboard"
        self.port = 8501
    
    def run_dashboard(self):
        """Run the Streamlit dashboard."""
        # This would normally launch a Streamlit app
        # For now, we'll simulate the dashboard functionality
        
        st.set_page_config(
            page_title=self.title,
            page_icon="🤖",
            layout="wide"
        )
        
        st.title("🤖 Orby Dashboard")
        st.markdown("Local-first AI with agentic powers")
        
        # Sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Go to",
            ["Overview", "Models", "Sessions", "Settings", "Live Monitor"]
        )
        
        if page == "Overview":
            self._show_overview()
        elif page == "Models":
            self._show_models()
        elif page == "Sessions":
            self._show_sessions()
        elif page == "Settings":
            self._show_settings()
        elif page == "Live Monitor":
            self._show_live_monitor()
    
    def _show_overview(self):
        """Show overview dashboard."""
        st.header("Overview")
        
        # Show current model status
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Current Model")
            if model_manager.current_model:
                st.info(f"**{model_manager.current_model.name}**")
                st.caption(f"Backend: {model_manager.current_model.backend}")
            else:
                st.warning("No model selected")
        
        with col2:
            st.subheader("System Status")
            st.success("Running")
            st.caption("Ready to assist")
        
        # Recent activity
        st.subheader("Recent Activity")
        st.info("Dashboard ready - connect to see activity")
    
    def _show_models(self):
        """Show models dashboard."""
        st.header("Available Models")
        
        # Refresh models
        if st.button("🔄 Refresh Models"):
            model_manager.refresh_models()
            st.success("Models refreshed!")
        
        # Group models by backend
        models_by_backend = model_manager.get_models_by_backend()
        
        for backend, models in models_by_backend.items():
            st.subheader(f"{backend.upper()} Models")
            
            if models:
                for model in models:
                    with st.expander(f"📋 {model.name}"):
                        st.write(f"**Backend:** {model.backend}")
                        if model.parameters:
                            st.write(f"**Parameters:** {model.parameters}")
                        if model.size:
                            size_gb = model.size / (1024**3)
                            st.write(f"**Size:** {size_gb:.2f} GB")
                        if model.benchmark_score:
                            st.write(f"**Performance Score:** {model.benchmark_score:.2f}")
            else:
                st.info("No models available")
    
    def _show_sessions(self):
        """Show sessions dashboard."""
        st.header("Sessions")
        
        # List existing sessions
        sessions = session_manager.list_sessions()
        
        if sessions:
            st.subheader("Saved Sessions")
            
            for session_info in sessions:
                with st.expander(f"💾 {session_info['name']}"):
                    st.write(f"**Model:** {session_info['model']}")
                    st.write(f"**Backend:** {session_info['backend']}")
                    st.write(f"**Created:** {session_info['created_at']}")
                    if session_info['tags']:
                        st.write(f"**Tags:** {', '.join(session_info['tags'])}")
                    
                    if st.button(f"Load {session_info['name']}"):
                        session_manager.load_session(session_info['name'])
                        st.success(f"Loaded session: {session_info['name']}")
        else:
            st.info("No saved sessions")
        
        # Create new session
        st.subheader("Create New Session")
        session_name = st.text_input("Session Name")
        if st.button("Create Session") and session_name:
            session_manager.create_session(session_name)
            st.success(f"Created session: {session_name}")
    
    def _show_settings(self):
        """Show settings dashboard."""
        st.header("Settings")
        
        st.subheader("Model Settings")
        st.info("Settings management coming soon")
        
        st.subheader("Backend Configuration")
        st.info("Backend configuration coming soon")
    
    def _show_live_monitor(self):
        """Show live monitoring dashboard."""
        st.header("Live Monitoring")
        
        st.subheader("File Changes")
        st.info("Live monitoring coming soon")
        
        st.subheader("Performance Metrics")
        st.info("Performance metrics coming soon")


# Dashboard instance
dashboard = OrbyDashboard()


def start_web_dashboard():
    """Start the web dashboard."""
    try:
        import streamlit.web.bootstrap as bootstrap
        
        # This would start the Streamlit server
        # For now, we'll just show instructions
        st.info("Web dashboard is ready! Run with: `streamlit run orby_dashboard.py`")
    except ImportError:
        st.error("Streamlit not installed. Install with: pip install streamlit")