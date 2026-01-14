import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import json
import io
import sqlite3
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="SPINS Marketing Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Database Functions
DB_PATH = Path(__file__).parent / "spins_history.db"

def init_database():
    """Initialize the SQLite database for historical data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create historical_snapshots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_date TEXT NOT NULL,
            data_period TEXT,
            sales_52w REAL,
            sales_growth_52w REAL,
            units_52w REAL,
            units_growth_52w REAL,
            retailer_count INTEGER,
            top_retailer TEXT,
            top_retailer_sales REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(data_period)
        )
    ''')

    conn.commit()
    conn.close()

def save_snapshot_to_db(data):
    """Save current PowerTabs snapshot to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    upload_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_period = data.get('period_info', '')

    # Extract 52-week metrics
    sales_52w = None
    sales_growth_52w = None
    units_52w = None
    units_growth_52w = None

    if 'overview' in data and not data['overview'].empty:
        overview = data['overview']
        week_52 = overview[overview.iloc[:, 0] == '52 Weeks']
        if not week_52.empty:
            sales_52w = float(week_52.iloc[0, 1])
            sales_growth_52w = float(week_52.iloc[0, 2])
            units_52w = float(week_52.iloc[0, 3])
            units_growth_52w = float(week_52.iloc[0, 4])

    # Extract retailer info
    retailer_count = None
    top_retailer = None
    top_retailer_sales = None

    if 'retailers' in data and not data['retailers'].empty:
        retailers = data['retailers']
        retailer_count = len(retailers)
        top_retailer = retailers.iloc[0, 0]
        top_retailer_sales = float(retailers.iloc[0, 1])

    try:
        # Use REPLACE to update if data_period already exists
        cursor.execute('''
            REPLACE INTO historical_snapshots
            (upload_date, data_period, sales_52w, sales_growth_52w, units_52w,
             units_growth_52w, retailer_count, top_retailer, top_retailer_sales)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (upload_date, data_period, sales_52w, sales_growth_52w, units_52w,
              units_growth_52w, retailer_count, top_retailer, top_retailer_sales))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving to database: {e}")
        return False
    finally:
        conn.close()

def load_historical_from_db():
    """Load all historical snapshots from database"""
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    query = '''
        SELECT upload_date, data_period, sales_52w, sales_growth_52w,
               units_52w, units_growth_52w, retailer_count, top_retailer,
               top_retailer_sales, created_at
        FROM historical_snapshots
        ORDER BY created_at
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def delete_snapshot_from_db(data_period):
    """Delete a specific snapshot from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM historical_snapshots WHERE data_period = ?', (data_period,))
    conn.commit()
    conn.close()

# Initialize database
init_database()

# Initialize session state
if 'uploaded_powertabs_file' not in st.session_state:
    st.session_state.uploaded_powertabs_file = None

# Sidebar - Always show first
st.sidebar.title("📊 Dashboard Controls")
st.sidebar.markdown("---")

# File Upload Section - Always visible
with st.sidebar.expander("📁 Upload SPINS PowerTabs File", expanded=True):
    st.markdown("Upload your SPINS PowerTabs Excel file to analyze data")

    powertabs_file = st.file_uploader(
        "SPINS PowerTabs File",
        type=['xlsx'],
        key='powertabs_uploader',
        help="Upload the SPINS PowerTabs - Entire Report.xlsx file"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Load File", type="primary"):
            if powertabs_file:
                st.session_state.uploaded_powertabs_file = powertabs_file
                load_powertabs_data.clear()
                st.success("✓ PowerTabs data loaded")
                st.rerun()

    with col2:
        if st.button("Reset to Default"):
            st.session_state.uploaded_powertabs_file = None
            load_powertabs_data.clear()
            st.rerun()

    # Show current data source
    if st.session_state.uploaded_powertabs_file:
        st.info("📊 Using uploaded data")
    else:
        st.info("📂 Waiting for PowerTabs file...")

st.sidebar.markdown("---")

# Load data
data = load_powertabs_data(st.session_state.uploaded_powertabs_file)

if data is None or 'overview' not in data:
    # Show friendly error message in main area
    st.title("📊 SPINS Marketing Intelligence Dashboard")
    st.markdown("---")
    st.info("👈 **Please upload your SPINS PowerTabs file using the sidebar to get started!**")
    st.markdown("""
    ### Required File:
    **SPINS PowerTabs - Entire Report.xlsx**

    This file contains all your SPINS market data including:
    - Brand performance metrics
    - Retailer sales and growth
    - Promotional analysis
    - Growth drivers

    ### How to Upload:
    1. Click on "📁 Upload SPINS PowerTabs File" in the left sidebar
    2. Select your PowerTabs Excel file
    3. Click "Load File"

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

# Add current data to history button
st.sidebar.markdown("### 💾 Save to Historical Database")

# Get historical count
historical_df = load_historical_from_db()
snapshot_count = len(historical_df)

if st.sidebar.button("📸 Save Current Snapshot", type="primary"):
    if save_snapshot_to_db(data):
        st.sidebar.success(f"✓ Saved to database!")
        st.rerun()
    else:
        st.sidebar.error("Failed to save snapshot")

if snapshot_count > 0:
    st.sidebar.info(f"📊 {snapshot_count} snapshots in database")
else:
    st.sidebar.info("No historical data yet")

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

    # Load historical data from database
    try:
        hist_df = load_historical_from_db()
    except Exception as e:
        st.error(f"Error loading database: {e}")
        hist_df = pd.DataFrame()

    if hist_df.empty or len(hist_df) == 0:
        st.info("👈 **No historical data yet!**")
        st.markdown("""
        ### How to Build Historical Data:

        1. **Upload your PowerTabs file** (already loaded ✓)
        2. **Click "📸 Save Current Snapshot"** in the sidebar
        3. **Done!** Data is automatically saved to the database

        **Next month:**
        1. Upload new PowerTabs file
        2. Click "Save Current Snapshot" again
        3. View trends in this tab!

        The database persists automatically - no manual file management needed!
        """)
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

    # Month-over-Month comparison (when multiple snapshots exist)
    if len(hist_df) == 1:
        st.markdown("---")
        st.info("💡 **Month-over-Month Comparison:** You have 1 snapshot saved. Next month, upload new PowerTabs data and save another snapshot to see month-over-month trends!")

    if len(hist_df) > 1:
        # Multiple snapshots - show month-over-month comparison
        st.markdown("---")
        st.markdown("### 📅 Month-over-Month Comparison")
        st.success(f"✅ **You have {len(hist_df)} snapshots saved!**")

        # Prepare data for charts
        hist_df['sales_growth'] = hist_df['sales_growth_52w'] * 100
        hist_df['units_growth'] = hist_df['units_growth_52w'] * 100

        # Month-over-Month Sales Trend
        st.markdown("#### 💵 Sales Trend (Month-over-Month)")

        fig_sales = go.Figure()
        fig_sales.add_trace(go.Scatter(
            x=hist_df['data_period'],
            y=hist_df['sales_52w'],
            mode='lines+markers',
            name='Sales',
            text=[f"${val/1e6:.2f}M" for val in hist_df['sales_52w']],
            textposition='top center',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=10)
        ))

        fig_sales.update_layout(
            title="52-Week Sales Trend",
            xaxis_title="Period",
            yaxis_title="Sales ($)",
            height=400,
            showlegend=False,
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig_sales, use_container_width=True)

        # Growth Rate Comparison
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Sales Growth %")
            fig_growth = go.Figure()
            fig_growth.add_trace(go.Bar(
                x=hist_df['data_period'],
                y=hist_df['sales_growth'],
                text=[f"{val:+.1f}%" for val in hist_df['sales_growth']],
                textposition='outside',
                marker_color=['#28a745' if x > 0 else '#dc3545' for x in hist_df['sales_growth']]
            ))
            fig_growth.update_layout(
                xaxis_title="Period",
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
                x=hist_df['data_period'],
                y=hist_df['retailer_count'],
                text=hist_df['retailer_count'],
                textposition='outside',
                marker_color='#17a2b8'
            ))
            fig_retailers.update_layout(
                xaxis_title="Period",
                yaxis_title="Number of Retailers",
                height=350,
                showlegend=False,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_retailers, use_container_width=True)

        # Historical Data Table
        st.markdown("---")
        st.markdown("### 📋 Historical Data Summary")

        display_hist = hist_df[['upload_date', 'data_period', 'sales_52w', 'sales_growth', 'units_52w', 'units_growth', 'retailer_count']].copy()
        display_hist['sales_52w'] = display_hist['sales_52w'].apply(lambda x: f"${x/1e6:.2f}M")
        display_hist['sales_growth'] = display_hist['sales_growth'].apply(lambda x: f"{x:+.1f}%")
        display_hist['units_52w'] = display_hist['units_52w'].apply(lambda x: f"{x/1e3:.1f}K")
        display_hist['units_growth'] = display_hist['units_growth'].apply(lambda x: f"{x:+.1f}%")

        display_hist.columns = ['Saved On', 'Data Period', 'Sales (52W)', 'Sales Growth %', 'Units (52W)', 'Units Growth %', 'Retailers']

        st.dataframe(display_hist, use_container_width=True, hide_index=True)

        # Period-over-Period Comparison
        if len(hist_df) >= 2:
            st.markdown("---")
            st.markdown("### 🔄 Period-over-Period Changes")

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
                growth_change = latest['sales_growth'] - previous['sales_growth']
                st.metric(
                    "Growth Rate Change",
                    f"{latest['sales_growth']:+.1f}%",
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

# Footer
st.markdown("---")
st.markdown("**SPINS Marketing Intelligence Dashboard** | Built for Humble Brands | Data powered by SPINS PowerTabs")
