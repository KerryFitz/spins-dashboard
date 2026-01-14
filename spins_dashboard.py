import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import json
import io
from pathlib import Path
import hashlib

# Page configuration
st.set_page_config(
    page_title="SPINS Marketing Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Password Protection
def check_password():
    """Returns True if the user has entered the correct password."""

    # Password hash for Gusdorf1336
    CORRECT_PASSWORD_HASH = "d08110d9f1d866d04bd61035ca09e754b60a249fb78118ced8d6ccd2126d8922"

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        entered_password = st.session_state["password"]
        entered_hash = hashlib.sha256(entered_password.encode()).hexdigest()

        if entered_hash == CORRECT_PASSWORD_HASH:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # First run, show password input
    if "password_correct" not in st.session_state:
        st.markdown("<h1 style='text-align: center;'>🔒 SPINS Marketing Intelligence Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Humble Brands - Secure Access</h3>", unsafe_allow_html=True)
        st.markdown("---")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input(
                "Enter Password",
                type="password",
                on_change=password_entered,
                key="password",
                help="Contact your administrator if you need access"
            )
        return False

    # Password not correct, show input + error
    elif not st.session_state["password_correct"]:
        st.markdown("<h1 style='text-align: center;'>🔒 SPINS Marketing Intelligence Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Humble Brands - Secure Access</h3>", unsafe_allow_html=True)
        st.markdown("---")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.error("😕 Incorrect password. Please try again.")
            st.text_input(
                "Enter Password",
                type="password",
                on_change=password_entered,
                key="password",
                help="Contact your administrator if you need access"
            )
        return False

    # Password correct
    else:
        return True

# Check password before loading dashboard
if not check_password():
    st.stop()

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .kpi-positive {
        color: #28a745;
        font-weight: bold;
    }
    .kpi-negative {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# PowerTabs Data Loading Functions
@st.cache_data
def load_powertabs_data(file_source=None):
    """Load all sheets from SPINS PowerTabs file"""

    if file_source is None:
        file_path = 'SPINS PowerTabs - Entire Report.xlsx'
    else:
        file_path = file_source

    data = {}

    try:
        # Overview - Key metrics by time period
        df_overview = pd.read_excel(file_path, sheet_name='Overview', header=None)
        # Extract period info from row 1 (0-indexed)
        period_info = df_overview.iloc[1, 0] if len(df_overview) > 1 else ""
        data['period_info'] = period_info

        # Headers are on row 3, data starts on row 4
        overview_data = df_overview.iloc[4:].copy()
        overview_data.columns = df_overview.iloc[3].values
        overview_data = overview_data.reset_index(drop=True)
        data['overview'] = overview_data

        # Brand by Retailer
        df_retailers = pd.read_excel(file_path, sheet_name='Brand by Retailer', header=None)
        retailers_data = df_retailers.iloc[4:].copy()
        retailers_data.columns = df_retailers.iloc[3].values
        retailers_data = retailers_data.reset_index(drop=True)
        # Clean numeric columns
        for col in ['Sales', 'Absolute Chg', '% Chg']:
            if col in retailers_data.columns:
                retailers_data[col] = pd.to_numeric(retailers_data[col], errors='coerce')
        data['retailers'] = retailers_data

        # Retailer Growth - Detailed metrics
        df_retailer_growth = pd.read_excel(file_path, sheet_name='Retailer Growth', header=None)
        retailer_growth_data = df_retailer_growth.iloc[4:].copy()
        retailer_growth_data.columns = df_retailer_growth.iloc[3].values
        retailer_growth_data = retailer_growth_data.reset_index(drop=True)
        # Clean numeric columns
        numeric_cols = [col for col in retailer_growth_data.columns if col not in ['Top 10 Retailers by Dollar Change', 'Primary Driver of Growth']]
        for col in numeric_cols:
            retailer_growth_data[col] = pd.to_numeric(retailer_growth_data[col], errors='coerce')
        data['retailer_growth'] = retailer_growth_data

        # Growth Drivers
        df_growth = pd.read_excel(file_path, sheet_name='Growth Drivers', header=None)
        growth_data = df_growth.iloc[4:].copy()
        growth_data.columns = df_growth.iloc[3].values
        growth_data = growth_data.reset_index(drop=True)
        for col in growth_data.columns:
            if col != 'Driver':
                growth_data[col] = pd.to_numeric(growth_data[col], errors='coerce')
        data['growth_drivers'] = growth_data

        # Promo Summary
        try:
            df_promo = pd.read_excel(file_path, sheet_name='Promo Summary', header=None)
            promo_data = df_promo.iloc[4:].copy()
            promo_data.columns = df_promo.iloc[3].values
            promo_data = promo_data.reset_index(drop=True)
            for col in promo_data.columns:
                if col != 'Promo Type':
                    promo_data[col] = pd.to_numeric(promo_data[col], errors='coerce')
            data['promo'] = promo_data
        except:
            data['promo'] = pd.DataFrame()

        # Brand vs Category
        try:
            df_category = pd.read_excel(file_path, sheet_name='Brand vs. Category', header=None)
            category_data = df_category.iloc[4:].copy()
            category_data.columns = df_category.iloc[3].values
            category_data = category_data.reset_index(drop=True)
            data['category'] = category_data
        except:
            data['category'] = pd.DataFrame()

        return data

    except Exception as e:
        st.error(f"Error loading PowerTabs data: {e}")
        return None

# Helper function to extract file label/date
def get_file_label(uploaded_file):
    """Extract a user-friendly label from the uploaded file"""
    if uploaded_file is None:
        return "Unknown"
    # Try to extract date from filename if it has a pattern
    filename = uploaded_file.name
    # Just return the filename for now
    return filename

# Initialize session state
if 'uploaded_powertabs_files' not in st.session_state:
    st.session_state.uploaded_powertabs_files = []
if 'selected_file_index' not in st.session_state:
    st.session_state.selected_file_index = 0

# Sidebar - Always show first
st.sidebar.title("📊 Dashboard Controls")
st.sidebar.markdown("---")

# File Upload Section - Always visible
with st.sidebar.expander("📁 Upload SPINS PowerTabs Files", expanded=True):
    st.markdown("Upload one or more SPINS PowerTabs Excel files to analyze and compare data")

    powertabs_files = st.file_uploader(
        "SPINS PowerTabs Files",
        type=['xlsx'],
        accept_multiple_files=True,
        key='powertabs_uploader',
        help="Upload one or more SPINS PowerTabs - Entire Report.xlsx files"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Load Files", type="primary"):
            if powertabs_files:
                st.session_state.uploaded_powertabs_files = powertabs_files
                st.session_state.selected_file_index = 0
                load_powertabs_data.clear()
                st.success(f"✓ {len(powertabs_files)} file(s) loaded")
                st.rerun()

    with col2:
        if st.button("Clear All"):
            st.session_state.uploaded_powertabs_files = []
            st.session_state.selected_file_index = 0
            load_powertabs_data.clear()
            st.rerun()

    # Show current data source
    if st.session_state.uploaded_powertabs_files:
        st.info(f"📊 {len(st.session_state.uploaded_powertabs_files)} file(s) uploaded")
    else:
        st.info("📂 Waiting for PowerTabs file(s)...")

st.sidebar.markdown("---")

# File selector if multiple files uploaded
if len(st.session_state.uploaded_powertabs_files) > 1:
    st.sidebar.markdown("### 📂 Select File to Analyze")
    file_options = [get_file_label(f) for f in st.session_state.uploaded_powertabs_files]
    selected_file_name = st.sidebar.selectbox(
        "Choose a file",
        file_options,
        index=st.session_state.selected_file_index,
        help="Select which PowerTabs file to view in the dashboard"
    )
    st.session_state.selected_file_index = file_options.index(selected_file_name)
    st.sidebar.markdown("---")

# Load data from the selected file
current_file = None
if st.session_state.uploaded_powertabs_files:
    current_file = st.session_state.uploaded_powertabs_files[st.session_state.selected_file_index]

data = load_powertabs_data(current_file)

if data is None or 'overview' not in data:
    # Show friendly error message in main area
    st.title("📊 SPINS Marketing Intelligence Dashboard")
    st.markdown("---")
    st.info("👈 **Please upload your SPINS PowerTabs file(s) using the sidebar to get started!**")
    st.markdown("""
    ### Required File:
    **SPINS PowerTabs - Entire Report.xlsx**

    This file contains all your SPINS market data including:
    - Brand performance metrics
    - Retailer sales and growth
    - Promotional analysis
    - Growth drivers

    ### How to Upload:
    1. Click on "📁 Upload SPINS PowerTabs Files" in the left sidebar
    2. Select one or more PowerTabs Excel files
    3. Click "Load Files"

    **Multiple Files:** Upload multiple monthly reports to compare trends over time in the Historical Trends tab!

    Your data stays secure and is only stored temporarily for this session.
    """)
    st.stop()

# If data loaded successfully, continue with dashboard

# Time Period Selector
st.sidebar.markdown("### 🕐 Time Period")
overview = data['overview']
available_periods = overview.iloc[:, 0].tolist()

selected_period = st.sidebar.selectbox(
    "Select Time Period",
    available_periods,
    index=0,  # Default to 52 Weeks
    help="Choose the time horizon for your analysis"
)

st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Select View",
    ["💡 Strategic Insights", "🏠 Executive Overview", "🏪 Retailer Performance",
     "📈 Growth Drivers", "🎯 Promotional Analysis", "📊 Historical Trends"]
)

st.sidebar.markdown("---")

# Show period info
if 'period_info' in data and data['period_info']:
    st.sidebar.markdown("### 📅 Data Period")
    period_text = data['period_info']
    # Extract just the time period part
    if '|' in period_text:
        period_parts = period_text.split('|')
        period = period_parts[0].replace('Period:', '').strip()
        st.sidebar.info(f"{period}")

# Get selected period data
selected_period_data = overview[overview.iloc[:, 0] == selected_period].iloc[0]
selected_sales = float(selected_period_data.iloc[1])
selected_sales_growth = float(selected_period_data.iloc[2])
selected_units = float(selected_period_data.iloc[3])
selected_units_growth = float(selected_period_data.iloc[4])

# ====================================================================================
# STRATEGIC INSIGHTS PAGE
# ====================================================================================
if page == "💡 Strategic Insights":
    st.markdown("<h1 class='main-header'>💡 Strategic Insights</h1>", unsafe_allow_html=True)
    st.markdown(f"**AI-powered analysis and actionable recommendations for {selected_period}**")
    st.markdown("---")

    retailers = data['retailers']
    retailer_growth = data['retailer_growth']
    growth_drivers = data['growth_drivers']

    # Use selected period metrics
    total_sales = selected_sales
    sales_growth = selected_sales_growth * 100
    total_units = selected_units
    units_growth = selected_units_growth * 100

    # Executive Summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            f"Total Sales ({selected_period})",
            f"${total_sales/1e6:.2f}M",
            f"{sales_growth:+.1f}%"
        )

    with col2:
        st.metric(
            f"Total Units ({selected_period})",
            f"{total_units/1e3:.1f}K",
            f"{units_growth:+.1f}%"
        )

    with col3:
        top_retailer = retailers.iloc[0, 0] if not retailers.empty else "N/A"
        top_sales = float(retailers.iloc[0, 1]) if not retailers.empty else 0
        st.metric(
            "Top Retailer",
            top_retailer,
            f"${top_sales/1e6:.2f}M"
        )

    with col4:
        num_retailers = len(retailers)
        st.metric(
            "Active Retailers",
            num_retailers,
            "Channels"
        )

    st.markdown("---")

    # Critical Alerts
    st.markdown("### 🚨 Critical Alerts")
    alerts = []

    # Check for declining sales
    if sales_growth < 0:
        alerts.append({
            'severity': '🔴 HIGH',
            'title': 'Declining Sales Trend',
            'description': f'Sales are down {abs(sales_growth):.1f}% YoY. Immediate action required to reverse trend.'
        })

    # Check for underperforming retailers
    declining_retailers = retailers[retailers['% Chg'] < 0]
    if not declining_retailers.empty and len(declining_retailers) > 0:
        alerts.append({
            'severity': '🟡 MEDIUM',
            'title': f'{len(declining_retailers)} Declining Retailers',
            'description': f'Retailers showing negative growth: {", ".join(declining_retailers.iloc[:, 0].tolist())}'
        })

    # Check recent performance (4 weeks vs 52 weeks)
    week_4 = overview[overview.iloc[:, 0] == '4 Weeks']
    if not week_4.empty:
        recent_growth = float(week_4.iloc[0, 2]) * 100
        if recent_growth < sales_growth - 10:
            alerts.append({
                'severity': '🟡 MEDIUM',
                'title': 'Slowing Momentum',
                'description': f'Recent 4-week growth ({recent_growth:.1f}%) is significantly below 52-week average ({sales_growth:.1f}%).'
            })

    if alerts:
        for alert in alerts:
            st.warning(f"**{alert['severity']} - {alert['title']}**\n\n{alert['description']}")
    else:
        st.success("✅ **No critical alerts** - Performance is on track")

    st.markdown("---")

    # Growth Opportunities
    st.markdown("### 🚀 Growth Opportunities")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Top Performing Retailers")
        # Top 3 retailers by growth rate
        top_growth_retailers = retailers.nlargest(3, '% Chg')
        for idx, row in top_growth_retailers.iterrows():
            retailer_name = row.iloc[0]
            growth_pct = row['% Chg'] * 100
            sales = row['Sales']
            st.success(f"**{retailer_name}**: +{growth_pct:.1f}% (${sales/1e6:.2f}M)")
            st.caption("💡 Consider increased marketing investment and promotional support")

    with col2:
        st.markdown("#### Growth Drivers to Leverage")
        if not growth_drivers.empty:
            for idx, row in growth_drivers.iterrows():
                driver = row.iloc[0]
                chg = row.iloc[3]
                dollars_impact = row.iloc[4]
                if dollars_impact > 0:
                    st.info(f"**{driver}**: +{chg:.1f} → ${dollars_impact/1e3:.0f}K impact")
        else:
            st.info("Growth driver data not available")

    st.markdown("---")

    # Strategic Recommendations
    st.markdown("### 🎯 Strategic Recommendations")

    recommendations = []

    # Recommendation 1: Focus on top performers
    if not retailers.empty:
        top_3_sales = retailers.nlargest(3, 'Sales')
        top_3_names = ", ".join(top_3_sales.iloc[:, 0].tolist())
        top_3_total = top_3_sales['Sales'].sum()
        top_3_pct = (top_3_total / total_sales) * 100

        recommendations.append({
            'priority': '🟢 HIGH',
            'title': f'Double Down on Top Retailers',
            'action': f'Focus 70% of marketing resources on {top_3_names}',
            'rationale': f'These 3 retailers represent {top_3_pct:.1f}% of sales and show strong growth momentum.',
            'next_steps': [
                'Schedule quarterly business reviews with key buyers',
                'Develop co-marketing campaigns',
                'Ensure optimal shelf placement and inventory levels'
            ]
        })

    # Recommendation 2: Address growth drivers
    if not growth_drivers.empty:
        top_driver = growth_drivers.nlargest(1, 'Dollars Chg Due To').iloc[0]
        driver_name = top_driver.iloc[0]
        driver_impact = top_driver.iloc[4]

        recommendations.append({
            'priority': '🟢 HIGH',
            'title': f'Accelerate {driver_name} Strategy',
            'action': f'Invest in expanding {driver_name.lower()}',
            'rationale': f'{driver_name} drove ${driver_impact/1e3:.0f}K in incremental sales.',
            'next_steps': [
                f'Analyze which retailers have room to improve {driver_name.lower()}',
                'Create incentive programs for underperforming locations',
                'Set quarterly targets for improvement'
            ]
        })

    # Recommendation 3: Rescue declining retailers
    if not declining_retailers.empty and len(declining_retailers) > 0:
        worst_performer = declining_retailers.iloc[0]
        worst_name = worst_performer.iloc[0]
        worst_decline = worst_performer['% Chg'] * 100

        recommendations.append({
            'priority': '🟡 MEDIUM',
            'title': 'Turn Around Declining Retailers',
            'action': f'Create recovery plan for {worst_name} and similar accounts',
            'rationale': f'{worst_name} is down {abs(worst_decline):.1f}%. Early intervention can prevent further losses.',
            'next_steps': [
                'Conduct account diagnostic (distribution, pricing, promo, placement)',
                'Compare vs successful retailers to identify gaps',
                'Implement 90-day action plan with weekly check-ins'
            ]
        })

    for rec in recommendations:
        with st.expander(f"{rec['priority']} - {rec['title']}", expanded=True):
            st.markdown(f"**Recommended Action:** {rec['action']}")
            st.markdown(f"**Rationale:** {rec['rationale']}")
            st.markdown("**Next Steps:**")
            for step in rec['next_steps']:
                st.markdown(f"- {step}")

    st.markdown("---")

    # This Week's Action Plan
    st.markdown("### 📋 This Week's Action Plan")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Immediate Actions")
        st.markdown("- [ ] Review top 3 retailer performance with sales team")
        st.markdown("- [ ] Schedule calls with declining retailers")
        st.markdown("- [ ] Analyze promotional effectiveness by account")
        st.markdown("- [ ] Update sales forecasts based on latest trends")

    with col2:
        st.markdown("#### Key Metrics to Monitor")
        st.markdown(f"- **Weekly Sales**: Track against ${total_sales/52/1e3:.0f}K weekly average")
        st.markdown(f"- **Growth Rate**: Maintain above {sales_growth:.1f}% YoY")
        st.markdown("- **Distribution**: Monitor ACV and store count")
        st.markdown("- **Promotional Lift**: Measure ROI on promotions")

# ====================================================================================
# EXECUTIVE OVERVIEW PAGE
# ====================================================================================
elif page == "🏠 Executive Overview":
    st.markdown("<h1 class='main-header'>🏠 Executive Overview</h1>", unsafe_allow_html=True)
    st.markdown(f"**High-level performance metrics for {selected_period}**")
    st.markdown("---")

    # Selected Period Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Sales",
            f"${selected_sales/1e6:.2f}M",
            f"{selected_sales_growth*100:+.1f}%"
        )

    with col2:
        st.metric(
            "Units",
            f"{selected_units/1e3:.1f}K",
            f"{selected_units_growth*100:+.1f}%"
        )

    with col3:
        avg_price = selected_sales / selected_units if selected_units > 0 else 0
        st.metric(
            "Avg Price",
            f"${avg_price:.2f}"
        )

    with col4:
        st.metric(
            "Period",
            selected_period
        )

    st.markdown("---")

    # All Time Periods Comparison
    st.markdown("### 📊 Performance Across All Time Periods")

    if not overview.empty:
        # Create metrics display
        fig = go.Figure()

        # Add sales bars
        fig.add_trace(go.Bar(
            name='Sales ($)',
            x=overview.iloc[:, 0],
            y=overview.iloc[:, 1],
            text=[f"${val/1e6:.2f}M" for val in overview.iloc[:, 1]],
            textposition='auto',
            marker_color='#1f77b4'
        ))

        fig.update_layout(
            title="Sales by Time Period",
            xaxis_title="Time Period",
            yaxis_title="Sales ($)",
            height=400,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # Growth rates
        col1, col2 = st.columns(2)

        with col1:
            fig_dollars = go.Figure()
            fig_dollars.add_trace(go.Bar(
                x=overview.iloc[:, 0],
                y=overview.iloc[:, 2] * 100,
                text=[f"{val*100:+.1f}%" for val in overview.iloc[:, 2]],
                textposition='auto',
                marker_color=['#28a745' if x > 0 else '#dc3545' for x in overview.iloc[:, 2]]
            ))
            fig_dollars.update_layout(
                title="Dollar Growth % by Period",
                xaxis_title="Time Period",
                yaxis_title="Growth %",
                height=350
            )
            st.plotly_chart(fig_dollars, use_container_width=True)

        with col2:
            fig_units = go.Figure()
            fig_units.add_trace(go.Bar(
                x=overview.iloc[:, 0],
                y=overview.iloc[:, 4] * 100,
                text=[f"{val*100:+.1f}%" for val in overview.iloc[:, 4]],
                textposition='auto',
                marker_color=['#28a745' if x > 0 else '#dc3545' for x in overview.iloc[:, 4]]
            ))
            fig_units.update_layout(
                title="Unit Growth % by Period",
                xaxis_title="Time Period",
                yaxis_title="Growth %",
                height=350
            )
            st.plotly_chart(fig_units, use_container_width=True)

        # Data table
        st.markdown("### 📋 Detailed Metrics")
        display_df = overview.copy()
        display_df.columns = ['Time Period', 'Dollars', 'Dollars % Chg', 'Units', 'Units % Chg']
        display_df['Dollars'] = display_df['Dollars'].apply(lambda x: f"${x:,.0f}")
        display_df['Dollars % Chg'] = display_df['Dollars % Chg'].apply(lambda x: f"{x*100:+.1f}%")
        display_df['Units'] = display_df['Units'].apply(lambda x: f"{x:,.0f}")
        display_df['Units % Chg'] = display_df['Units % Chg'].apply(lambda x: f"{x*100:+.1f}%")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# ====================================================================================
# RETAILER PERFORMANCE PAGE
# ====================================================================================
elif page == "🏪 Retailer Performance":
    st.markdown("<h1 class='main-header'>🏪 Retailer Performance</h1>", unsafe_allow_html=True)
    st.markdown("**Detailed analysis of performance by retailer**")
    st.markdown("---")

    retailers = data['retailers']
    retailer_growth = data['retailer_growth']

    # Top performers
    st.markdown("### 🏆 Top Performers")

    col1, col2 = st.columns(2)

    with col1:
        # Sales chart
        fig_sales = px.bar(
            retailers.head(10),
            x='Sales',
            y=retailers.columns[0],
            orientation='h',
            title="Top 10 Retailers by Sales",
            text='Sales'
        )
        fig_sales.update_traces(texttemplate='$%{text:.2s}', textposition='outside')
        fig_sales.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_sales, use_container_width=True)

    with col2:
        # Growth chart
        fig_growth = px.bar(
            retailers.head(10),
            x=retailers.columns[0],
            y='% Chg',
            title="Growth Rate by Retailer",
            text='% Chg',
            color='% Chg',
            color_continuous_scale=['red', 'yellow', 'green']
        )
        fig_growth.update_traces(texttemplate='%{text:.1%}', textposition='outside')
        fig_growth.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_growth, use_container_width=True)

    # Performance Scorecard with weighted scoring
    st.markdown("### 📊 Retailer Performance Scorecard")
    st.markdown("**Scoring:** 70% Sales Volume + 30% Growth Rate")

    scorecard = retailers.copy()

    # Calculate Performance Score (70% volume, 30% growth)
    max_sales = scorecard['Sales'].max()
    scorecard['Sales Score'] = (scorecard['Sales'] / max_sales * 100) if max_sales > 0 else 0

    # Growth score: cap at +50% and -50% for scoring purposes
    scorecard['Growth Score'] = scorecard['% Chg'].clip(-0.5, 0.5) * 100
    scorecard['Growth Score'] = ((scorecard['Growth Score'] + 50) / 100 * 100)

    # Combined Performance Score (70% sales, 30% growth)
    scorecard['Performance Score'] = (scorecard['Sales Score'] * 0.7 + scorecard['Growth Score'] * 0.3)

    # Priority tiers
    def get_priority(score):
        if score >= 70:
            return '🟢 High Priority'
        elif score >= 40:
            return '🟡 Medium Priority'
        else:
            return '🔴 Low Priority'

    scorecard['Priority'] = scorecard['Performance Score'].apply(get_priority)

    # Display scorecard
    display_scorecard = scorecard[[scorecard.columns[0], 'Sales', '% Chg', 'Performance Score', 'Priority']].copy()
    display_scorecard.columns = ['Retailer', 'Sales', 'Growth %', 'Performance Score', 'Priority']
    display_scorecard['Sales'] = display_scorecard['Sales'].apply(lambda x: f"${x/1e6:.2f}M")
    display_scorecard['Growth %'] = display_scorecard['Growth %'].apply(lambda x: f"{x*100:+.1f}%")
    display_scorecard['Performance Score'] = display_scorecard['Performance Score'].apply(lambda x: f"{x:.1f}")

    st.dataframe(display_scorecard, use_container_width=True, hide_index=True)

    # Detailed retailer metrics
    if not retailer_growth.empty:
        st.markdown("---")
        st.markdown("### 🔍 Detailed Retailer Metrics")

        # Select retailer
        retailer_list = retailer_growth.iloc[:, 0].tolist()
        selected_retailer = st.selectbox("Select Retailer for Details", retailer_list)

        retailer_data = retailer_growth[retailer_growth.iloc[:, 0] == selected_retailer]

        if not retailer_data.empty:
            row = retailer_data.iloc[0]

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Dollar Share", f"{row['Dollar Share']:.1%}" if 'Dollar Share' in row else "N/A")
            with col2:
                st.metric("TDP", f"{row['TDP']:.0f}" if 'TDP' in row else "N/A")
            with col3:
                st.metric("Max % ACV", f"{row['Max % ACV']:.0f}%" if 'Max % ACV' in row else "N/A")
            with col4:
                st.metric("Avg # Items", f"{row['Avg # Items']:.1f}" if 'Avg # Items' in row else "N/A")

            st.markdown("#### Primary Growth Driver")
            if 'Primary Driver of Growth' in row:
                st.info(f"**{row['Primary Driver of Growth']}**")

# ====================================================================================
# GROWTH DRIVERS PAGE
# ====================================================================================
elif page == "📈 Growth Drivers":
    st.markdown("<h1 class='main-header'>📈 Growth Drivers</h1>", unsafe_allow_html=True)
    st.markdown("**Understanding what's driving your business growth**")
    st.markdown("---")

    growth_drivers = data['growth_drivers']

    if not growth_drivers.empty:
        # Waterfall chart of growth drivers
        st.markdown("### 💧 Growth Driver Waterfall")

        drivers = growth_drivers.iloc[:, 0].tolist()
        impacts = growth_drivers.iloc[:, 4].tolist()

        # Create waterfall
        fig = go.Figure(go.Waterfall(
            name="Growth Impact",
            orientation="v",
            measure=["relative"] * len(drivers),
            x=drivers,
            textposition="outside",
            text=[f"${val/1e3:.0f}K" for val in impacts],
            y=impacts,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "#28a745"}},
            decreasing={"marker": {"color": "#dc3545"}},
        ))

        fig.update_layout(
            title="Dollar Impact by Growth Driver",
            showlegend=False,
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # Driver details
        st.markdown("### 📊 Driver Details")

        cols = st.columns(len(growth_drivers))

        for idx, (col, (_, row)) in enumerate(zip(cols, growth_drivers.iterrows())):
            with col:
                driver = row.iloc[0]
                yag = row.iloc[1]
                latest = row.iloc[2]
                chg = row.iloc[3]
                impact = row.iloc[4]

                st.markdown(f"#### {driver}")
                st.metric("Latest", f"{latest:.1f}", f"{chg:+.1f}")
                st.metric("YAG", f"{yag:.1f}")
                st.metric("$ Impact", f"${impact/1e3:.0f}K")

        # Recommendations
        st.markdown("---")
        st.markdown("### 💡 Recommendations")

        # Find top positive and negative drivers
        top_driver = growth_drivers.nlargest(1, 'Dollars Chg Due To').iloc[0]
        worst_driver = growth_drivers.nsmallest(1, 'Dollars Chg Due To').iloc[0]

        col1, col2 = st.columns(2)

        with col1:
            st.success(f"""
            **Leverage: {top_driver.iloc[0]}**

            This driver contributed ${top_driver.iloc[4]/1e3:.0f}K in growth.

            **Action:** Double down on this strength. Analyze which retailers have the highest {top_driver.iloc[0].lower()}
            and replicate their success across other accounts.
            """)

        with col2:
            if worst_driver.iloc[4] < 0:
                st.warning(f"""
                **Fix: {worst_driver.iloc[0]}**

                This driver reduced growth by ${abs(worst_driver.iloc[4])/1e3:.0f}K.

                **Action:** Investigate root causes. This may indicate pricing pressure, distribution losses,
                or velocity issues that need immediate attention.
                """)
            else:
                st.info("All drivers contributing positively to growth!")

# ====================================================================================
# PROMOTIONAL ANALYSIS PAGE
# ====================================================================================
elif page == "🎯 Promotional Analysis":
    st.markdown("<h1 class='main-header'>🎯 Promotional Analysis</h1>", unsafe_allow_html=True)
    st.markdown("**Measuring promotional effectiveness and ROI**")
    st.markdown("---")

    promo = data['promo']

    if promo.empty or len(promo) == 0:
        st.warning("⚠️ Promotional data not available in this PowerTabs report")
        st.info("This may indicate:\n- No promotions ran during this period\n- This sheet requires a specific retailer filter in PowerTabs\n- Promotional data is in a different report")
    else:
        # Promo effectiveness
        st.markdown("### 🎯 Promotional Effectiveness")

        col1, col2 = st.columns(2)

        with col1:
            # Dollar lift by promo
            fig_dollar = px.bar(
                promo.sort_values('$ % Lift', ascending=False),
                x='Promo ID',
                y='$ % Lift',
                title="Dollar Lift % by Promotion",
                text='$ % Lift',
                color='$ % Lift',
                color_continuous_scale='Blues'
            )
            fig_dollar.update_traces(texttemplate='%{text:.1%}', textposition='outside')
            st.plotly_chart(fig_dollar, use_container_width=True)

        with col2:
            # Unit lift by promo
            fig_unit = px.bar(
                promo.sort_values('U % Lift', ascending=False),
                x='Promo ID',
                y='U % Lift',
                title="Unit Lift % by Promotion",
                text='U % Lift',
                color='U % Lift',
                color_continuous_scale='Greens'
            )
            fig_unit.update_traces(texttemplate='%{text:.1%}', textposition='outside')
            st.plotly_chart(fig_unit, use_container_width=True)

        # Discount vs Lift analysis
        st.markdown("### 📉 Discount vs Lift Analysis")

        fig_scatter = px.scatter(
            promo,
            x='% Disc',
            y='$ % Lift',
            size='# of Weeks',
            color='U % Lift',
            hover_data=['Base Price', 'Promo Price'],
            title="Discount Depth vs Dollar Lift (Size = Duration)",
            labels={'% Disc': 'Discount %', '$ % Lift': 'Dollar Lift %'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        # Promo details table
        st.markdown("### 📋 Promotion Details")

        display_promo = promo.copy()
        display_promo['Base Price'] = display_promo['Base Price'].apply(lambda x: f"${x:.2f}")
        display_promo['Promo Price'] = display_promo['Promo Price'].apply(lambda x: f"${x:.2f}")
        display_promo['% Disc'] = display_promo['% Disc'].apply(lambda x: f"{x*100:.1f}%")
        display_promo['$ % Lift'] = display_promo['$ % Lift'].apply(lambda x: f"{x*100:.1f}%")
        display_promo['U % Lift'] = display_promo['U % Lift'].apply(lambda x: f"{x*100:.1f}%")

        st.dataframe(display_promo, use_container_width=True, hide_index=True)

        # Recommendations
        st.markdown("---")
        st.markdown("### 💡 Promotional Recommendations")

        # Find most efficient promo (best lift per discount point)
        promo['efficiency'] = promo['$ % Lift'] / abs(promo['% Disc'])
        best_promo = promo.nlargest(1, 'efficiency').iloc[0]

        col1, col2 = st.columns(2)

        with col1:
            st.success(f"""
            **Most Efficient Promotion**

            **Promo ID:** {int(best_promo['Promo ID'])}
            - **Discount:** {best_promo['% Disc']*100:.1f}%
            - **Dollar Lift:** {best_promo['$ % Lift']*100:.1f}%
            - **Efficiency:** {best_promo['efficiency']:.2f}x

            This promotion delivered the best return per discount point.
            """)

        with col2:
            avg_discount = promo['% Disc'].mean() * 100
            avg_lift = promo['$ % Lift'].mean() * 100

            st.info(f"""
            **Average Performance**

            - **Avg Discount:** {avg_discount:.1f}%
            - **Avg Dollar Lift:** {avg_lift:.1f}%
            - **Total Promo Weeks:** {promo['# of Weeks'].sum():.0f}

            Use these benchmarks for future promotional planning.
            """)

# ====================================================================================
# HISTORICAL TRENDS PAGE
# ====================================================================================
elif page == "📊 Historical Trends":
    st.markdown("<h1 class='main-header'>📊 Historical Trends</h1>", unsafe_allow_html=True)
    st.markdown("**Compare performance across multiple time periods**")
    st.markdown("---")

    num_files = len(st.session_state.uploaded_powertabs_files)

    if num_files == 0:
        st.info("👈 **No data uploaded yet!**")
        st.markdown("""
        ### How to View Historical Trends:

        Upload one or more PowerTabs files in the sidebar to see trends!

        **Single File:** See trends across 52W, 24W, 12W, 4W time periods
        **Multiple Files:** Compare month-over-month performance across all uploaded files
        """)
        st.stop()
    elif num_files == 1:
        st.info("💡 **Single File Uploaded:** Showing trends across time periods (52W, 24W, 12W, 4W). Upload multiple monthly PowerTabs files to see month-over-month comparisons!")
    # Show current PowerTabs trends (from different time periods in current data)
    if data and 'overview' in data:
        st.markdown("### 📈 Current Period Trends")
        st.markdown("**Performance across different time horizons in your current PowerTabs data**")

        overview = data['overview']

        # Sales by time period
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 💵 Sales by Time Period")
            fig_sales_periods = go.Figure()
            fig_sales_periods.add_trace(go.Bar(
                x=overview.iloc[:, 0],
                y=overview.iloc[:, 1],
                text=[f"${val/1e6:.2f}M" for val in overview.iloc[:, 1]],
                textposition='outside',
                marker_color='#1f77b4'
            ))
            fig_sales_periods.update_layout(
                xaxis_title="Time Period",
                yaxis_title="Sales ($)",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_sales_periods, use_container_width=True)

        with col2:
            st.markdown("#### 📈 Growth Rate by Time Period")
            fig_growth_periods = go.Figure()
            fig_growth_periods.add_trace(go.Bar(
                x=overview.iloc[:, 0],
                y=overview.iloc[:, 2] * 100,
                text=[f"{val*100:+.1f}%" for val in overview.iloc[:, 2]],
                textposition='outside',
                marker_color=['#28a745' if x > 0 else '#dc3545' for x in overview.iloc[:, 2]]
            ))
            fig_growth_periods.update_layout(
                xaxis_title="Time Period",
                yaxis_title="Growth %",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_growth_periods, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📊 Performance Metrics")

        # Show all time periods in a table
        display_overview = overview.copy()
        display_overview.columns = ['Time Period', 'Dollars', 'Dollars % Chg', 'Units', 'Units % Chg']
        display_overview['Dollars'] = display_overview['Dollars'].apply(lambda x: f"${x/1e6:.2f}M")
        display_overview['Dollars % Chg'] = display_overview['Dollars % Chg'].apply(lambda x: f"{x*100:+.1f}%")
        display_overview['Units'] = display_overview['Units'].apply(lambda x: f"{x/1e3:.1f}K")
        display_overview['Units % Chg'] = display_overview['Units % Chg'].apply(lambda x: f"{x*100:+.1f}%")

        st.dataframe(display_overview, use_container_width=True, hide_index=True)

    # Month-over-Month comparison (when multiple files uploaded)
    if num_files > 1:
        st.markdown("---")
        st.markdown("### 📅 File-by-File Comparison")
        st.success(f"✅ **You have {num_files} files uploaded!**")

        # Load data from all files
        multi_file_data = []
        for i, file in enumerate(st.session_state.uploaded_powertabs_files):
            file_data = load_powertabs_data(file)
            if file_data and 'overview' in file_data:
                overview = file_data['overview']
                week_52 = overview[overview.iloc[:, 0] == '52 Weeks']
                if not week_52.empty:
                    file_label = get_file_label(file)
                    multi_file_data.append({
                        'file_label': file_label,
                        'sales_52w': float(week_52.iloc[0, 1]),
                        'sales_growth_52w': float(week_52.iloc[0, 2]),
                        'units_52w': float(week_52.iloc[0, 3]),
                        'units_growth_52w': float(week_52.iloc[0, 4]),
                        'retailer_count': len(file_data.get('retailers', []))
                    })

        if len(multi_file_data) > 0:
            hist_df = pd.DataFrame(multi_file_data)

            # Sales Trend Across Files
            st.markdown("#### 💵 Sales Trend (52-Week)")

            fig_sales = go.Figure()
            fig_sales.add_trace(go.Scatter(
                x=hist_df['file_label'],
                y=hist_df['sales_52w'],
                mode='lines+markers',
                name='Sales',
                text=[f"${val/1e6:.2f}M" for val in hist_df['sales_52w']],
                textposition='top center',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=10)
            ))

            fig_sales.update_layout(
                xaxis_title="File",
                yaxis_title="Sales ($)",
                height=400,
                showlegend=False,
                xaxis_tickangle=-45
            )

            st.plotly_chart(fig_sales, use_container_width=True)

            # Growth Rate Comparison
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📊 Sales Growth % (52W)")
                fig_growth = go.Figure()
                fig_growth.add_trace(go.Bar(
                    x=hist_df['file_label'],
                    y=hist_df['sales_growth_52w'] * 100,
                    text=[f"{val*100:+.1f}%" for val in hist_df['sales_growth_52w']],
                    textposition='outside',
                    marker_color=['#28a745' if x > 0 else '#dc3545' for x in hist_df['sales_growth_52w']]
                ))
                fig_growth.update_layout(
                    xaxis_title="File",
                    yaxis_title="Growth %",
                    height=350,
                    showlegend=False,
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_growth, use_container_width=True)

            with col2:
                st.markdown("### 🏪 Retailer Count")
                fig_retailers = go.Figure()
                fig_retailers.add_trace(go.Bar(
                    x=hist_df['file_label'],
                    y=hist_df['retailer_count'],
                    text=hist_df['retailer_count'],
                    textposition='outside',
                    marker_color='#17a2b8'
                ))
                fig_retailers.update_layout(
                    xaxis_title="File",
                    yaxis_title="Number of Retailers",
                    height=350,
                    showlegend=False,
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_retailers, use_container_width=True)

            # Historical Data Table
            st.markdown("---")
            st.markdown("### 📋 File Comparison Summary")

            display_hist = hist_df.copy()
            display_hist['sales_52w_fmt'] = display_hist['sales_52w'].apply(lambda x: f"${x/1e6:.2f}M")
            display_hist['sales_growth_fmt'] = display_hist['sales_growth_52w'].apply(lambda x: f"{x*100:+.1f}%")
            display_hist['units_52w_fmt'] = display_hist['units_52w'].apply(lambda x: f"{x/1e3:.1f}K")
            display_hist['units_growth_fmt'] = display_hist['units_growth_52w'].apply(lambda x: f"{x*100:+.1f}%")

            display_hist = display_hist[['file_label', 'sales_52w_fmt', 'sales_growth_fmt', 'units_52w_fmt', 'units_growth_fmt', 'retailer_count']]
            display_hist.columns = ['File', 'Sales (52W)', 'Sales Growth %', 'Units (52W)', 'Units Growth %', 'Retailers']

            st.dataframe(display_hist, use_container_width=True, hide_index=True)

            # File-to-File Comparison (latest vs previous)
            if len(hist_df) >= 2:
                st.markdown("---")
                st.markdown("### 🔄 Latest vs Previous File")

                latest = hist_df.iloc[-1]
                previous = hist_df.iloc[-2]

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    sales_change = ((latest['sales_52w'] - previous['sales_52w']) / previous['sales_52w']) * 100
                    st.metric(
                        "Sales Change",
                        f"${latest['sales_52w']/1e6:.2f}M",
                        f"{sales_change:+.1f}%"
                    )

                with col2:
                    growth_change = (latest['sales_growth_52w'] - previous['sales_growth_52w']) * 100
                    st.metric(
                        "Growth Rate Change",
                        f"{latest['sales_growth_52w']*100:+.1f}%",
                        f"{growth_change:+.1f}pp"
                    )

                with col3:
                    units_change = ((latest['units_52w'] - previous['units_52w']) / previous['units_52w']) * 100
                    st.metric(
                        "Units Change",
                        f"{latest['units_52w']/1e3:.1f}K",
                        f"{units_change:+.1f}%"
                    )

                with col4:
                    retailer_change = int(latest['retailer_count'] - previous['retailer_count'])
                    st.metric(
                        "Retailer Change",
                        int(latest['retailer_count']),
                        f"{retailer_change:+d}"
                    )
        else:
            st.warning("Could not load data from uploaded files")

# Footer
st.markdown("---")
st.markdown("**SPINS Marketing Intelligence Dashboard** | Built for Humble Brands | Data powered by SPINS PowerTabs")
