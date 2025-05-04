import streamlit as st
import requests
import json
import time
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
REFRESH_INTERVAL = 5  # Seconds between dashboard updates

# Set page configuration
st.set_page_config(
    page_title="Gmail Automation Dashboard",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .subheader {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0D47A1;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    
    .status-running {
        color: #4CAF50;
        font-weight: bold;
    }
    
    .status-stopped {
        color: #F44336;
        font-weight: bold;
    }
    
    .status-waiting {
        color: #FFC107;
        font-weight: bold;
    }
    
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1E88E5;
    }
    
    .log-container {
        height: 300px;
        overflow-y: auto;
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.25rem;
        border: 1px solid #e9ecef;
        font-family: monospace;
    }
    
    .email-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1976D2;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .email-subject {
        font-weight: bold;
    }
    
    .email-sender {
        color: #616161;
        font-style: italic;
    }
    
    .email-body {
        margin-top: 0.5rem;
        white-space: pre-wrap;
    }
    
    .metric-card {
        text-align: center;
        padding: 1rem;
        background-color: white;
        border-radius: 0.5rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E88E5;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #616161;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'workflow_logs' not in st.session_state:
    st.session_state.workflow_logs = []
    
if 'processed_emails' not in st.session_state:
    st.session_state.processed_emails = []
    
if 'email_categories' not in st.session_state:
    st.session_state.email_categories = {}
    
if 'run_count' not in st.session_state:
    st.session_state.run_count = 0

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None

if 'workflow_status' not in st.session_state:
    st.session_state.workflow_status = "Stopped"

def format_datetime(dt):
    """Format datetime for display."""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt

# Sidebar
with st.sidebar:
    st.markdown("### 🔧 Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Start Workflow", use_container_width=True):
            st.session_state.workflow_status = "Running"
            st.session_state.workflow_logs.append({
                "timestamp": datetime.now(),
                "message": "Workflow started manually",
                "level": "INFO"
            })
            
            # Call the API to start the workflow
            try:
                response = requests.post(f"{API_URL}/invoke", 
                                         json={"input": {"emails": [], "current_email": {}, "email_category": "", "generated_email": ""}})
                if response.status_code == 200:
                    st.session_state.workflow_logs.append({
                        "timestamp": datetime.now(),
                        "message": "API call successful",
                        "level": "INFO"
                    })
                else:
                    st.session_state.workflow_logs.append({
                        "timestamp": datetime.now(),
                        "message": f"API error: {response.status_code} - {response.text}",
                        "level": "ERROR"
                    })
            except Exception as e:
                st.session_state.workflow_logs.append({
                    "timestamp": datetime.now(),
                    "message": f"Error calling API: {str(e)}",
                    "level": "ERROR"
                })
            
    with col2:
        if st.button("🛑 Stop Workflow", use_container_width=True):
            st.session_state.workflow_status = "Stopped"
            st.session_state.workflow_logs.append({
                "timestamp": datetime.now(),
                "message": "Workflow stopped manually",
                "level": "WARNING"
            })
            
    st.markdown("### ⚙️ Settings")
    refresh_rate = st.slider("Refresh Interval (seconds)", 
                            min_value=1, 
                            max_value=60, 
                            value=REFRESH_INTERVAL)
    
    # Mock data loading for demo
    if st.button("Load Sample Data"):
        # Add sample emails
        st.session_state.processed_emails = [
            {
                "id": "email123",
                "timestamp": datetime.now(),
                "subject": "Question about product pricing",
                "sender": "customer@example.com",
                "category": "pricing",
                "status": "replied",
                "response": "Thank you for your interest in our products. Our pricing structure is as follows..."
            },
            {
                "id": "email456",
                "timestamp": datetime.now(),
                "subject": "Technical support needed",
                "sender": "user@example.com",
                "category": "support",
                "status": "replied",
                "response": "I'm sorry to hear you're experiencing issues. Here are some troubleshooting steps..."
            },
            {
                "id": "email789",
                "timestamp": datetime.now(),
                "subject": "Newsletter subscription",
                "sender": "potential@example.com",
                "category": "marketing",
                "status": "skipped",
                "response": ""
            }
        ]
        
        # Update categories
        st.session_state.email_categories = {
            "pricing": 1,
            "support": 1,
            "marketing": 1,
            "unrelated": 1
        }
        
        # Add logs
        st.session_state.workflow_logs = [
            {"timestamp": datetime.now(), "message": "Started workflow", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Loading inbox emails", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Found 3 unprocessed emails", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Processing email: Question about product pricing", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Categorized as: pricing", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Generated response for email123", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Processing email: Technical support needed", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Categorized as: support", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Generated response for email456", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Processing email: Newsletter subscription", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Categorized as: marketing", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Skipped unrelated email", "level": "INFO"},
            {"timestamp": datetime.now(), "message": "Workflow completed", "level": "INFO"}
        ]
        
        st.session_state.run_count = 1
        st.session_state.workflow_status = "Stopped"
    
    st.markdown("### 📊 Stats")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{st.session_state.run_count}</div>
        <div class="metric-label">Total Runs</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(st.session_state.processed_emails)}</div>
        <div class="metric-label">Emails Processed</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.last_refresh:
        st.markdown(f"""
        <div style="font-size: 0.8rem; color: #616161; text-align: center; margin-top: 1rem;">
            Last refreshed: {format_datetime(st.session_state.last_refresh)}
        </div>
        """, unsafe_allow_html=True)

# Main content
st.markdown('<h1 class="main-header">📧 Gmail Automation Workflow Dashboard</h1>', unsafe_allow_html=True)

# Status and metrics row
col1, col2, col3 = st.columns(3)

with col1:
    status_color = "status-running" if st.session_state.workflow_status == "Running" else "status-stopped"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Workflow Status</div>
        <div class="metric-value {status_color}">{st.session_state.workflow_status}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Count emails by status
    replied_count = sum(1 for email in st.session_state.processed_emails if email["status"] == "replied")
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Emails Replied</div>
        <div class="metric-value">{replied_count}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    # Count emails by status
    skipped_count = sum(1 for email in st.session_state.processed_emails if email["status"] == "skipped")
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Emails Skipped</div>
        <div class="metric-value">{skipped_count}</div>
    </div>
    """, unsafe_allow_html=True)

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📈 Workflow Visualization", "📝 Logs", "📨 Processed Emails", "📊 Analytics"])

# Tab 1: Workflow Visualization
with tab1:
    st.markdown('<h2 class="subheader">Workflow Graph</h2>', unsafe_allow_html=True)
    
    # Create a Plotly figure to visualize the workflow
    fig = go.Figure()
    
    # Define node positions for the workflow
    nodes = {
        "load_inbox_emails": {"x": 0, "y": 0, "name": "Load Inbox Emails"},
        "is_email_inbox_empty": {"x": 1, "y": 0, "name": "Is Email Inbox Empty?"},
        "categorize_email": {"x": 2, "y": 0, "name": "Categorize Email"},
        "construct_rag_queries": {"x": 3, "y": -1, "name": "Construct RAG Queries"},
        "retrieve_from_rag": {"x": 4, "y": -1, "name": "Retrieve from RAG"},
        "email_writer": {"x": 5, "y": 0, "name": "Email Writer"},
        "email_proofreader": {"x": 6, "y": 0, "name": "Email Proofreader"},
        "send_email": {"x": 7, "y": 0, "name": "Send Email"},
        "skip_unrelated_email": {"x": 3, "y": 1, "name": "Skip Unrelated Email"},
        "end": {"x": 8, "y": 0, "name": "END"}
    }
    
    # Add nodes
    for node_id, node_info in nodes.items():
        color = "#1E88E5"  # Default color
        size = 20
        
        # Highlight specific nodes based on email categories or status
        if node_id == "categorize_email" and st.session_state.email_categories:
            color = "#4CAF50"  # Green for active categorization
            size = 25
        elif node_id == "email_writer" and any(email["status"] == "replied" for email in st.session_state.processed_emails):
            color = "#4CAF50"  # Green for active writing
            size = 25
        elif node_id == "skip_unrelated_email" and any(email["status"] == "skipped" for email in st.session_state.processed_emails):
            color = "#FFC107"  # Yellow for skipped emails
            size = 25
            
        fig.add_trace(go.Scatter(
            x=[node_info["x"]],
            y=[node_info["y"]],
            mode="markers+text",
            marker=dict(size=size, color=color),
            text=[node_info["name"]],
            textposition="bottom center",
            name=node_id
        ))
    
    # Add edges
    edges = [
        ("load_inbox_emails", "is_email_inbox_empty"),
        ("is_email_inbox_empty", "categorize_email"),
        ("is_email_inbox_empty", "end"),
        ("categorize_email", "construct_rag_queries"),
        ("categorize_email", "skip_unrelated_email"),
        ("construct_rag_queries", "retrieve_from_rag"),
        ("retrieve_from_rag", "email_writer"),
        ("email_writer", "email_proofreader"),
        ("email_proofreader", "send_email"),
        ("email_proofreader", "email_writer"),
        ("send_email", "is_email_inbox_empty"),
        ("skip_unrelated_email", "is_email_inbox_empty")
    ]
    
    for start, end in edges:
        if start in nodes and end in nodes:
            fig.add_trace(go.Scatter(
                x=[nodes[start]["x"], nodes[end]["x"]],
                y=[nodes[start]["y"], nodes[end]["y"]],
                mode="lines",
                line=dict(width=1, color="#9E9E9E"),
                showlegend=False
            ))
    
    # Layout
    fig.update_layout(
        showlegend=False,
        title="Gmail Automation Workflow Graph",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="white",
        height=500,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Current workflow state
    st.markdown('<h2 class="subheader">Current Workflow State</h2>', unsafe_allow_html=True)
    
    if st.session_state.workflow_status == "Running":
        last_log = st.session_state.workflow_logs[-1] if st.session_state.workflow_logs else {"message": "No logs available"}
        st.markdown(f"""
        <div class="info-box">
            <strong>Current Operation:</strong> {last_log.get("message", "No operation")}
            <br>
            <strong>Status:</strong> <span class="status-running">Active</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="info-box">
            <strong>Current Operation:</strong> None
            <br>
            <strong>Status:</strong> <span class="status-stopped">Inactive</span>
        </div>
        """, unsafe_allow_html=True)

# Tab 2: Logs
with tab2:
    st.markdown('<h2 class="subheader">Workflow Logs</h2>', unsafe_allow_html=True)
    
    # Create dataframe for logs
    if st.session_state.workflow_logs:
        logs_df = pd.DataFrame(st.session_state.workflow_logs)
        logs_df["timestamp"] = logs_df["timestamp"].apply(format_datetime)
        
        # Apply styling based on log level
        def color_log_level(val):
            if val == "ERROR":
                return "background-color: #FFCDD2; color: #B71C1C"
            elif val == "WARNING":
                return "background-color: #FFF9C4; color: #F57F17"
            elif val == "INFO":
                return "background-color: #E3F2FD; color: #0D47A1"
            return ""
        
        styled_logs = logs_df.style.applymap(color_log_level, subset=["level"])
        st.dataframe(styled_logs, use_container_width=True)
    else:
        st.info("No logs available yet. Start the workflow to see logs.")
        
    # Add a clear logs button
    if st.button("Clear Logs"):
        st.session_state.workflow_logs = []
        st.experimental_rerun()

# Tab 3: Processed Emails
with tab3:
    st.markdown('<h2 class="subheader">Processed Emails</h2>', unsafe_allow_html=True)
    
    if st.session_state.processed_emails:
        # Create an expander for each email
        for i, email in enumerate(st.session_state.processed_emails):
            with st.expander(f"{email['subject']} - {email['sender']}"):
                st.markdown(f"""
                <div class="email-card">
                    <div class="email-subject">{email['subject']}</div>
                    <div class="email-sender">From: {email['sender']}</div>
                    <div>Category: <strong>{email['category']}</strong></div>
                    <div>Status: <strong>{email['status']}</strong></div>
                    <div>Processed: {format_datetime(email['timestamp'])}</div>
                    <hr>
                    <div class="email-body">{email['response'] if email['response'] else 'No response generated (email was skipped)'}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No emails have been processed yet.")

# Tab 4: Analytics
with tab4:
    st.markdown('<h2 class="subheader">Email Analytics</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Category distribution
        if st.session_state.email_categories:
            fig = go.Figure(data=[go.Pie(
                labels=list(st.session_state.email_categories.keys()),
                values=list(st.session_state.email_categories.values()),
                hole=.3,
                marker_colors=['#1E88E5', '#43A047', '#FFC107', '#E53935', '#5E35B1']
            )])
            
            fig.update_layout(
                title="Email Categories Distribution",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available yet.")
    
    with col2:
        # Email processing status
        if st.session_state.processed_emails:
            status_counts = {"replied": 0, "skipped": 0, "pending": 0}
            for email in st.session_state.processed_emails:
                if email["status"] in status_counts:
                    status_counts[email["status"]] += 1
            
            fig = go.Figure(data=[go.Bar(
                x=list(status_counts.keys()),
                y=list(status_counts.values()),
                marker_color=['#4CAF50', '#FFC107', '#9E9E9E']
            )])
            
            fig.update_layout(
                title="Email Processing Status",
                xaxis_title="Status",
                yaxis_title="Count",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No email processing data available yet.")
    
    # Processing time metrics (if we had real data)
    st.markdown('<h2 class="subheader">Processing Performance</h2>', unsafe_allow_html=True)
    
    # Mock performance data
    performance_data = {
        "category": ["pricing", "support", "marketing", "billing", "technical"],
        "avg_time": [15.2, 22.7, 8.5, 18.3, 25.1]
    }
    
    fig = go.Figure(data=[go.Bar(
        x=performance_data["category"],
        y=performance_data["avg_time"],
        marker_color='#1976D2'
    )])
    
    fig.update_layout(
        title="Average Processing Time by Email Category (seconds)",
        xaxis_title="Email Category",
        yaxis_title="Average Time (s)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Auto-refresh mechanism
st.markdown("---")
refresh_placeholder = st.empty()
auto_refresh = st.checkbox("Enable auto-refresh", value=True)

if auto_refresh:
    refresh_placeholder.markdown(f"Dashboard will auto-refresh every {refresh_rate} seconds.")
    time.sleep(1)  # Small delay to prevent excessive updates
    
    # In a real app, you would make API calls here to get updated data
    # For demo purposes, we're just updating the last refresh time
    st.session_state.last_refresh = datetime.now()
    
    # In a production app, you would call your API to get updated status
    # Example:
    # try:
    #     response = requests.get(f"{API_URL}/status")
    #     if response.status_code == 200:
    #         data = response.json()
    #         update_session_state_from_data(data)
    # except Exception as e:
    #     st.error(f"Error refreshing data: {str(e)}")
    
    # This would trigger a refresh after the specified interval
    if auto_refresh:
        refresh_placeholder.markdown(f"Auto-refreshing in {refresh_rate} seconds...")
else:
    refresh_placeholder.markdown("Auto-refresh is disabled.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center;">
    <p>Gmail Automation Workflow Dashboard | Developed with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)