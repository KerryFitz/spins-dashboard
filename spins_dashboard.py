import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

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

# Data loading functions
@st.cache_data
def load_brand_data(file_source=None):
    """Load the brand and retailers data"""
    if file_source is not None:
        df = pd.read_excel(file_source, sheet_name='Raw')
    else:
        df = pd.read_excel('SPINs Brand and Retailers_110225.xlsx', sheet_name='Raw')

    # Clean percentage columns - convert to numeric
    pct_cols = [col for col in df.columns if '% Chg' in col or '% ACV' in col]
    for col in pct_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Clean ARP columns
    arp_cols = [col for col in df.columns if 'ARP' in col]
    for col in arp_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

@st.cache_data
def load_trend_data(file_source=None):
    """Load the Humble trend data"""
    if file_source is not None:
        df = pd.read_excel(file_source, sheet_name='Raw')
    else:
        df = pd.read_excel('SPINs Humble_Trended Sale_100525.xlsx', sheet_name='Raw')

    # Clean percentage columns
    pct_cols = [col for col in df.columns if '% Chg' in col or '% ACV' in col]
    for col in pct_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert TIME FRAME to datetime for sorting
    df['Date'] = pd.to_datetime(df['TIME FRAME'].str.extract(r'(\d{2}/\d{2}/\d{4})')[0], format='%m/%d/%Y')
    df = df.sort_values('Date')

    return df

# Initialize session state for uploaded files
if 'uploaded_brand_file' not in st.session_state:
    st.session_state.uploaded_brand_file = None
if 'uploaded_trend_file' not in st.session_state:
    st.session_state.uploaded_trend_file = None

# Load data
try:
    brand_df = load_brand_data(st.session_state.uploaded_brand_file)
    trend_df = load_trend_data(st.session_state.uploaded_trend_file)
    data_loaded = True
except Exception as e:
    st.error(f"Error loading data: {e}")
    data_loaded = False

if data_loaded:
    # Sidebar
    st.sidebar.title("📊 Dashboard Controls")
    st.sidebar.markdown("---")

    # Navigation
    page = st.sidebar.radio(
        "Select View",
        ["💡 Strategic Insights", "🏠 Executive Overview", "📈 Sales Performance", "🏆 Competitive Analysis",
         "🏪 Retailer Performance", "📉 Trend Analysis", "🎯 Promotional Analysis"]
    )

    st.sidebar.markdown("---")

    # File Upload Section
    with st.sidebar.expander("📁 Upload New Data Files", expanded=False):
        st.markdown("Upload new weekly SPINS data to update the dashboard")

        brand_file = st.file_uploader(
            "Brand & Retailers File",
            type=['xlsx'],
            key='brand_uploader',
            help="Upload the SPINS Brand and Retailers Excel file"
        )

        trend_file = st.file_uploader(
            "Trend Data File",
            type=['xlsx'],
            key='trend_uploader',
            help="Upload the SPINS Humble Trended Sale Excel file"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Load Files", type="primary"):
                if brand_file:
                    st.session_state.uploaded_brand_file = brand_file
                    load_brand_data.clear()
                    st.success("✓ Brand data loaded")
                if trend_file:
                    st.session_state.uploaded_trend_file = trend_file
                    load_trend_data.clear()
                    st.success("✓ Trend data loaded")
                if brand_file or trend_file:
                    st.rerun()

        with col2:
            if st.button("Reset to Default"):
                st.session_state.uploaded_brand_file = None
                st.session_state.uploaded_trend_file = None
                load_brand_data.clear()
                load_trend_data.clear()
                st.rerun()

        # Show current data source
        if st.session_state.uploaded_brand_file or st.session_state.uploaded_trend_file:
            st.info("📊 Using uploaded data")
        else:
            st.info("📂 Using default data files")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filters")

    # Common filters
    time_periods = sorted(brand_df['TIME FRAME'].dropna().unique())
    selected_period = st.sidebar.selectbox("Time Period", time_periods, index=len(time_periods)-1)

    # Filter data based on selection
    filtered_df = brand_df[brand_df['TIME FRAME'] == selected_period].copy()

    # Strategic analysis functions
    def generate_insights(filtered_df, brand_df, trend_df, selected_period):
        """Generate strategic insights and recommendations"""
        insights = {
            'alerts': [],
            'opportunities': [],
            'threats': [],
            'recommendations': [],
            'key_metrics': {}
        }

        # Get HUMBLE data
        humble_data = filtered_df[filtered_df['DESCRIPTION'] == 'HUMBLE']

        if humble_data.empty:
            return insights

        # Calculate key metrics
        total_sales = humble_data['Dollars'].sum()
        total_units = humble_data['Units'].sum()
        avg_growth = humble_data['Dollars, % Chg, Yago'].mean()
        avg_acv = humble_data['Max % ACV'].astype(float).mean()
        promo_sales = humble_data['Dollars, Promo'].sum()
        promo_pct = (promo_sales / total_sales * 100) if total_sales > 0 else 0

        insights['key_metrics'] = {
            'total_sales': total_sales,
            'avg_growth': avg_growth * 100,
            'avg_acv': avg_acv,
            'promo_pct': promo_pct
        }

        # ALERTS - Identify concerning trends
        if avg_growth < -0.05:
            insights['alerts'].append({
                'severity': 'high',
                'title': 'Declining Sales Trend',
                'description': f'Sales are down {abs(avg_growth)*100:.1f}% YoY. Immediate action required.',
                'metric': avg_growth * 100
            })

        if promo_pct > 50:
            insights['alerts'].append({
                'severity': 'medium',
                'title': 'High Promotional Dependency',
                'description': f'{promo_pct:.1f}% of sales come from promotions. Risk of margin erosion.',
                'metric': promo_pct
            })

        # Check for distribution losses
        declining_acv = humble_data[humble_data['Max % ACV, +/- Chg, Yago'] < -5]
        if not declining_acv.empty:
            for _, row in declining_acv.iterrows():
                insights['alerts'].append({
                    'severity': 'high',
                    'title': f'Distribution Loss at {row["GEOGRAPHY"]}',
                    'description': f'ACV dropped by {abs(row["Max % ACV, +/- Chg, Yago"]):.1f} points.',
                    'metric': row['Max % ACV, +/- Chg, Yago']
                })

        # OPPORTUNITIES - Identify growth opportunities
        high_growth_retailers = humble_data[humble_data['Dollars, % Chg, Yago'] > 0.15].sort_values('Dollars, % Chg, Yago', ascending=False)
        for _, row in high_growth_retailers.head(3).iterrows():
            insights['opportunities'].append({
                'title': f'Strong Growth at {row["GEOGRAPHY"]}',
                'description': f'Sales up {row["Dollars, % Chg, Yago"]*100:.1f}% YoY. Consider increasing investment.',
                'metric': row['Dollars, % Chg, Yago'] * 100,
                'action': f'Expand distribution or promotional support at {row["GEOGRAPHY"]}'
            })

        # Low ACV but high sales velocity = opportunity
        for _, row in humble_data.iterrows():
            acv = pd.to_numeric(row['Max % ACV'], errors='coerce')
            if pd.notna(acv) and acv < 50 and row['Dollars'] > humble_data['Dollars'].median():
                velocity = row['Units'] / row['# of Stores Selling'] if row['# of Stores Selling'] > 0 else 0
                if velocity > humble_data['Units'].sum() / humble_data['# of Stores Selling'].sum():
                    insights['opportunities'].append({
                        'title': f'Distribution Gap at {row["GEOGRAPHY"]}',
                        'description': f'Strong velocity ({velocity:.1f} units/store) but only {acv:.1f}% ACV.',
                        'metric': acv,
                        'action': f'Negotiate expanded distribution at {row["GEOGRAPHY"]}'
                    })

        # THREATS - Competitive analysis
        for geo in humble_data['GEOGRAPHY'].unique():
            geo_data = filtered_df[filtered_df['GEOGRAPHY'] == geo]
            humble_sales = geo_data[geo_data['DESCRIPTION'] == 'HUMBLE']['Dollars'].sum()

            # Find competitors with higher growth
            competitors = geo_data[geo_data['DESCRIPTION'] != 'HUMBLE'].copy()
            if not competitors.empty:
                top_competitors = competitors.nlargest(5, 'Dollars')
                growing_competitors = top_competitors[top_competitors['Dollars, % Chg, Yago'] > avg_growth + 0.10]

                for _, comp in growing_competitors.iterrows():
                    if comp['Dollars'] > humble_sales * 0.5:  # Significant competitor
                        insights['threats'].append({
                            'title': f'{comp["DESCRIPTION"]} Gaining Share',
                            'description': f'Growing {comp["Dollars, % Chg, Yago"]*100:.1f}% YoY at {geo}, faster than HUMBLE.',
                            'metric': comp['Dollars, % Chg, Yago'] * 100,
                            'competitor': comp['DESCRIPTION']
                        })

        # RECOMMENDATIONS
        # 1. Retailer prioritization
        retailer_scores = []
        for _, row in humble_data.iterrows():
            score = 0
            growth = row['Dollars, % Chg, Yago'] if pd.notna(row['Dollars, % Chg, Yago']) else 0
            sales = row['Dollars']

            # Score based on sales and growth
            if growth > 0.10:
                score += 3
            elif growth > 0:
                score += 1
            elif growth < -0.10:
                score -= 2

            if sales > humble_data['Dollars'].quantile(0.75):
                score += 2

            retailer_scores.append({
                'retailer': row['GEOGRAPHY'],
                'score': score,
                'sales': sales,
                'growth': growth * 100
            })

        retailer_scores = sorted(retailer_scores, key=lambda x: x['score'], reverse=True)

        # Top priority retailers
        if retailer_scores:
            top_3 = retailer_scores[:3]
            insights['recommendations'].append({
                'category': 'Retailer Focus',
                'priority': 'high',
                'title': 'Prioritize High-Performance Retailers',
                'actions': [f"{r['retailer']}: ${r['sales']:,.0f} sales, {r['growth']:.1f}% growth" for r in top_3],
                'rationale': 'These retailers show strong performance and growth momentum.'
            })

        # Declining retailers need attention
        declining = [r for r in retailer_scores if r['growth'] < -5]
        if declining:
            insights['recommendations'].append({
                'category': 'Retailer Risk',
                'priority': 'high',
                'title': 'Address Declining Retailers',
                'actions': [f"{r['retailer']}: {r['growth']:.1f}% decline" for r in declining[:3]],
                'rationale': 'Immediate intervention needed to reverse negative trends.'
            })

        # 2. Promotional strategy
        if promo_pct > 40:
            insights['recommendations'].append({
                'category': 'Promotional Strategy',
                'priority': 'medium',
                'title': 'Reduce Promotional Dependency',
                'actions': [
                    f'Current promo mix: {promo_pct:.1f}% (Target: 25-35%)',
                    'Improve everyday shelf presence and visibility',
                    'Test premium positioning at select retailers'
                ],
                'rationale': 'High promotional dependency erodes margins and brand equity.'
            })
        elif promo_pct < 20:
            insights['recommendations'].append({
                'category': 'Promotional Strategy',
                'priority': 'low',
                'title': 'Consider Increased Promotional Activity',
                'actions': [
                    f'Current promo mix: {promo_pct:.1f}%',
                    'Test targeted promotions at underperforming retailers',
                    'Trial sampling programs to drive awareness'
                ],
                'rationale': 'Limited promotional activity may be leaving sales on the table.'
            })

        # 3. Distribution expansion
        low_acv_retailers = humble_data[humble_data['Max % ACV'].astype(float) < 50]
        if not low_acv_retailers.empty:
            insights['recommendations'].append({
                'category': 'Distribution',
                'priority': 'medium',
                'title': 'Expand Distribution Coverage',
                'actions': [f"{row['GEOGRAPHY']}: {pd.to_numeric(row['Max % ACV'], errors='coerce'):.1f}% ACV"
                           for _, row in low_acv_retailers.head(3).iterrows()],
                'rationale': 'Low ACV indicates significant white space opportunity.'
            })

        return insights

    # Main content
    if page == "💡 Strategic Insights":
        st.markdown('<p class="main-header">Strategic Insights & Recommendations</p>', unsafe_allow_html=True)
        st.markdown(f"**Period:** {selected_period}")
        st.markdown("*AI-powered analysis of your SPINS data*")
        st.markdown("---")

        # Generate insights
        insights = generate_insights(filtered_df, brand_df, trend_df, selected_period)

        # Executive Summary
        st.subheader("📊 Executive Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            sales = insights['key_metrics'].get('total_sales', 0)
            st.metric("Total Sales", f"${sales:,.0f}")

        with col2:
            growth = insights['key_metrics'].get('avg_growth', 0)
            st.metric("Avg YoY Growth", f"{growth:.1f}%",
                     delta=f"{growth:.1f}%",
                     delta_color="normal")

        with col3:
            acv = insights['key_metrics'].get('avg_acv', 0)
            st.metric("Avg Distribution", f"{acv:.1f}%")

        with col4:
            promo = insights['key_metrics'].get('promo_pct', 0)
            color = "inverse" if promo > 40 else "normal"
            st.metric("Promo Mix", f"{promo:.1f}%", delta_color=color)

        st.markdown("---")

        # Alerts Section
        if insights['alerts']:
            st.subheader("🚨 Critical Alerts")
            st.markdown("*Immediate attention required*")

            for alert in insights['alerts']:
                severity_color = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(alert['severity'], '⚪')

                with st.container():
                    cols = st.columns([1, 20])
                    with cols[0]:
                        st.markdown(f"### {severity_color}")
                    with cols[1]:
                        st.markdown(f"**{alert['title']}**")
                        st.markdown(alert['description'])
                    st.markdown("")
        else:
            st.success("✅ No critical alerts. Performance is within acceptable ranges.")

        st.markdown("---")

        # Opportunities Section
        if insights['opportunities']:
            st.subheader("🎯 Growth Opportunities")
            st.markdown("*Areas where you can accelerate growth*")

            for opp in insights['opportunities'][:5]:  # Top 5 opportunities
                with st.expander(f"✨ {opp['title']}", expanded=True):
                    st.markdown(opp['description'])
                    if 'action' in opp:
                        st.markdown(f"**Recommended Action:** {opp['action']}")

        st.markdown("---")

        # Threats Section
        if insights['threats']:
            st.subheader("⚠️ Competitive Threats")
            st.markdown("*Monitor these competitive dynamics*")

            threat_list = []
            for threat in insights['threats'][:5]:
                threat_list.append({
                    'Competitor': threat.get('competitor', 'N/A'),
                    'Issue': threat['title'],
                    'Description': threat['description'],
                    'Growth Rate': f"{threat['metric']:.1f}%"
                })

            if threat_list:
                threat_df = pd.DataFrame(threat_list)
                st.dataframe(threat_df, width='stretch', hide_index=True)

        st.markdown("---")

        # Strategic Recommendations
        st.subheader("💡 Strategic Recommendations")
        st.markdown("*Prioritized action plan based on data analysis*")

        if insights['recommendations']:
            # Group by priority
            high_priority = [r for r in insights['recommendations'] if r['priority'] == 'high']
            medium_priority = [r for r in insights['recommendations'] if r['priority'] == 'medium']
            low_priority = [r for r in insights['recommendations'] if r['priority'] == 'low']

            if high_priority:
                st.markdown("### 🔴 High Priority")
                for rec in high_priority:
                    with st.expander(f"**{rec['title']}** - {rec['category']}", expanded=True):
                        st.markdown(f"*{rec['rationale']}*")
                        st.markdown("**Actions:**")
                        for action in rec['actions']:
                            st.markdown(f"• {action}")

            if medium_priority:
                st.markdown("### 🟡 Medium Priority")
                for rec in medium_priority:
                    with st.expander(f"**{rec['title']}** - {rec['category']}"):
                        st.markdown(f"*{rec['rationale']}*")
                        st.markdown("**Actions:**")
                        for action in rec['actions']:
                            st.markdown(f"• {action}")

            if low_priority:
                st.markdown("### 🟢 Low Priority")
                for rec in low_priority:
                    with st.expander(f"**{rec['title']}** - {rec['category']}"):
                        st.markdown(f"*{rec['rationale']}*")
                        st.markdown("**Actions:**")
                        for action in rec['actions']:
                            st.markdown(f"• {action}")

        # Key Metrics to Watch
        st.markdown("---")
        st.subheader("📈 Key Metrics to Monitor")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Week-over-Week:**")
            st.markdown("• Total sales trend")
            st.markdown("• YoY growth rate")
            st.markdown("• Average transaction value")
            st.markdown("• Promotional effectiveness")

        with col2:
            st.markdown("**Month-over-Month:**")
            st.markdown("• Distribution (ACV) changes")
            st.markdown("• Market share vs competitors")
            st.markdown("• Retailer mix shifts")
            st.markdown("• Velocity (units per store)")

        # Trend Analysis from historical data
        st.markdown("---")
        st.subheader("📉 Performance Trends")

        # Get trend data for HUMBLE
        natural_trend = trend_df[trend_df['GEOGRAPHY'] == 'TOTAL US - NATURAL EXPANDED CHANNEL'].copy()

        if not natural_trend.empty and len(natural_trend) >= 12:
            # Calculate trend indicators
            recent_sales = natural_trend.tail(12)['Dollars'].mean()
            prior_sales = natural_trend.head(12)['Dollars'].mean()
            trend_direction = ((recent_sales - prior_sales) / prior_sales * 100) if prior_sales > 0 else 0

            col1, col2 = st.columns(2)

            with col1:
                if trend_direction > 10:
                    st.success(f"📈 **Accelerating Growth**: Sales trending up {trend_direction:.1f}% over time")
                elif trend_direction > 0:
                    st.info(f"➡️ **Stable Growth**: Sales trending up {trend_direction:.1f}% over time")
                elif trend_direction > -10:
                    st.warning(f"⚠️ **Slowing Growth**: Sales trending down {abs(trend_direction):.1f}% over time")
                else:
                    st.error(f"📉 **Declining**: Sales trending down {abs(trend_direction):.1f}% over time")

            with col2:
                # Calculate volatility
                sales_std = natural_trend['Dollars'].std()
                sales_mean = natural_trend['Dollars'].mean()
                volatility = (sales_std / sales_mean * 100) if sales_mean > 0 else 0

                if volatility < 10:
                    st.success(f"✅ **Stable Performance**: Low volatility ({volatility:.1f}%)")
                elif volatility < 20:
                    st.info(f"ℹ️ **Moderate Volatility**: {volatility:.1f}%")
                else:
                    st.warning(f"⚠️ **High Volatility**: {volatility:.1f}% - Review consistency")

        # Action Plan Summary
        st.markdown("---")
        st.subheader("📋 This Week's Action Plan")

        st.markdown("""
        **Immediate Actions (Next 7 Days):**
        1. Review and address any high-priority alerts above
        2. Contact account managers for declining retailers
        3. Analyze top growth retailers for expansion opportunities

        **This Month:**
        1. Implement recommendations from medium-priority section
        2. Review promotional calendar against performance data
        3. Assess competitive positioning in key markets

        **Strategic Planning:**
        1. Evaluate distribution gaps and expansion opportunities
        2. Review pricing strategy vs. competition
        3. Plan promotional strategy for next quarter based on ROI analysis
        """)

    elif page == "🏠 Executive Overview":
        st.markdown('<p class="main-header">Executive Overview</p>', unsafe_allow_html=True)
        st.markdown(f"**Period:** {selected_period}")
        st.markdown("---")

        # Get Humble data
        humble_data = filtered_df[filtered_df['DESCRIPTION'] == 'HUMBLE']

        if not humble_data.empty:
            # Calculate totals across all retailers
            total_sales = humble_data['Dollars'].sum()
            total_units = humble_data['Units'].sum()
            avg_growth = humble_data['Dollars, % Chg, Yago'].mean() * 100
            avg_acv = humble_data['Max % ACV'].astype(float).mean()

            # Top metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Sales",
                    f"${total_sales:,.0f}",
                    f"{avg_growth:.1f}% YoY" if not pd.isna(avg_growth) else "N/A"
                )

            with col2:
                st.metric(
                    "Total Units",
                    f"{total_units:,.0f}",
                    ""
                )

            with col3:
                st.metric(
                    "Avg Distribution (ACV)",
                    f"{avg_acv:.1f}%",
                    ""
                )

            with col4:
                promo_sales = humble_data['Dollars, Promo'].sum()
                promo_pct = (promo_sales / total_sales * 100) if total_sales > 0 else 0
                st.metric(
                    "Promo Sales %",
                    f"{promo_pct:.1f}%",
                    ""
                )

            st.markdown("---")

            # Two column layout
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Sales by Retailer")
                retailer_sales = humble_data.groupby('GEOGRAPHY')['Dollars'].sum().sort_values(ascending=False).head(10)
                fig = px.bar(
                    x=retailer_sales.values,
                    y=retailer_sales.index,
                    orientation='h',
                    labels={'x': 'Sales ($)', 'y': 'Retailer'},
                    title=f"Top 10 Retailers - {selected_period}"
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, width='stretch')

            with col2:
                st.subheader("Growth Rate by Retailer")
                growth_data = humble_data[['GEOGRAPHY', 'Dollars, % Chg, Yago']].dropna()
                growth_data = growth_data.sort_values('Dollars, % Chg, Yago', ascending=False).head(10)

                fig = px.bar(
                    growth_data,
                    x='Dollars, % Chg, Yago',
                    y='GEOGRAPHY',
                    orientation='h',
                    labels={'Dollars, % Chg, Yago': 'YoY Growth %', 'GEOGRAPHY': 'Retailer'},
                    title="Top Growth Retailers"
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, width='stretch')

            # Time series from trend data
            st.markdown("---")
            st.subheader("Sales Trend - Last 2 Years")

            trend_natural = trend_df[trend_df['GEOGRAPHY'] == 'TOTAL US - NATURAL EXPANDED CHANNEL'].copy()

            if not trend_natural.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=trend_natural['Date'],
                    y=trend_natural['Dollars'],
                    mode='lines+markers',
                    name='Sales',
                    line=dict(color='#1f77b4', width=3)
                ))

                fig.update_layout(
                    title='HUMBLE Sales - Natural Expanded Channel (Rolling 12 Weeks)',
                    xaxis_title='Date',
                    yaxis_title='Sales ($)',
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, width='stretch')

        else:
            st.warning("No data available for HUMBLE brand in selected period")

    elif page == "📈 Sales Performance":
        st.markdown('<p class="main-header">Sales Performance Analysis</p>', unsafe_allow_html=True)
        st.markdown(f"**Period:** {selected_period}")
        st.markdown("---")

        # Brand selector
        brands = sorted(filtered_df['DESCRIPTION'].dropna().unique())
        selected_brand = st.selectbox("Select Brand", brands, index=brands.index('HUMBLE') if 'HUMBLE' in brands else 0)

        brand_data = filtered_df[filtered_df['DESCRIPTION'] == selected_brand]

        if not brand_data.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            total_sales = brand_data['Dollars'].sum()
            total_units = brand_data['Units'].sum()
            avg_arp = (total_sales / total_units) if total_units > 0 else 0
            yoy_growth = brand_data['Dollars, % Chg, Yago'].mean() * 100

            with col1:
                st.metric("Total Sales", f"${total_sales:,.0f}")
            with col2:
                st.metric("Total Units", f"{total_units:,.0f}")
            with col3:
                st.metric("Avg Price", f"${avg_arp:.2f}")
            with col4:
                growth_color = "🟢" if yoy_growth > 0 else "🔴"
                st.metric("YoY Growth", f"{growth_color} {yoy_growth:.1f}%")

            st.markdown("---")

            # Detailed metrics table
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Sales by Retailer")
                sales_table = brand_data[['GEOGRAPHY', 'Dollars', 'Units', 'Dollars, % Chg, Yago']].copy()
                sales_table['Dollars, % Chg, Yago'] = sales_table['Dollars, % Chg, Yago'] * 100
                sales_table = sales_table.sort_values('Dollars', ascending=False)
                sales_table.columns = ['Retailer', 'Sales ($)', 'Units', 'YoY Growth (%)']
                st.dataframe(
                    sales_table.style.format({
                        'Sales ($)': '${:,.0f}',
                        'Units': '{:,.0f}',
                        'YoY Growth (%)': '{:.1f}%'
                    }),
                    height=400,
                    width='stretch'
                )

            with col2:
                st.subheader("Promotional Mix")
                promo_data = brand_data[['GEOGRAPHY', 'Dollars, Promo', 'Dollars, Non-Promo']].copy()
                promo_data = promo_data.groupby('GEOGRAPHY').sum().reset_index()
                promo_data['Total'] = promo_data['Dollars, Promo'] + promo_data['Dollars, Non-Promo']
                promo_data = promo_data.sort_values('Total', ascending=False).head(10)

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Promo',
                    x=promo_data['GEOGRAPHY'],
                    y=promo_data['Dollars, Promo'],
                    marker_color='#ff7f0e'
                ))
                fig.add_trace(go.Bar(
                    name='Non-Promo',
                    x=promo_data['GEOGRAPHY'],
                    y=promo_data['Dollars, Non-Promo'],
                    marker_color='#1f77b4'
                ))

                fig.update_layout(
                    barmode='stack',
                    title='Sales: Promo vs Non-Promo',
                    xaxis_title='Retailer',
                    yaxis_title='Sales ($)',
                    height=400
                )
                st.plotly_chart(fig, width='stretch')

            # Distribution metrics
            st.markdown("---")
            st.subheader("Distribution & Velocity")

            col1, col2 = st.columns(2)

            with col1:
                dist_data = brand_data[['GEOGRAPHY', 'Max % ACV', 'TDP']].copy()
                dist_data['Max % ACV'] = pd.to_numeric(dist_data['Max % ACV'], errors='coerce')
                dist_data = dist_data.dropna().sort_values('Max % ACV', ascending=False).head(10)

                fig = px.bar(
                    dist_data,
                    x='GEOGRAPHY',
                    y='Max % ACV',
                    title='Store Coverage (Max % ACV)',
                    labels={'Max % ACV': 'ACV %', 'GEOGRAPHY': 'Retailer'}
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, width='stretch')

            with col2:
                velocity = brand_data[['GEOGRAPHY', '# of Stores Selling', 'Units']].copy()
                velocity['Units per Store'] = velocity['Units'] / velocity['# of Stores Selling']
                velocity = velocity.dropna().sort_values('Units per Store', ascending=False).head(10)

                fig = px.bar(
                    velocity,
                    x='GEOGRAPHY',
                    y='Units per Store',
                    title='Sales Velocity (Units per Store)',
                    labels={'Units per Store': 'Units/Store', 'GEOGRAPHY': 'Retailer'}
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, width='stretch')

    elif page == "🏆 Competitive Analysis":
        st.markdown('<p class="main-header">Competitive Analysis</p>', unsafe_allow_html=True)
        st.markdown(f"**Period:** {selected_period}")
        st.markdown("---")

        # Geography selector
        geographies = sorted(filtered_df['GEOGRAPHY'].dropna().unique())
        selected_geo = st.selectbox("Select Market/Retailer", geographies)

        geo_data = filtered_df[filtered_df['GEOGRAPHY'] == selected_geo].copy()

        if not geo_data.empty:
            # Top brands
            top_brands = geo_data.nlargest(20, 'Dollars')

            st.subheader(f"Top 20 Brands - {selected_geo}")

            col1, col2 = st.columns([2, 1])

            with col1:
                fig = px.bar(
                    top_brands,
                    x='Dollars',
                    y='DESCRIPTION',
                    orientation='h',
                    title='Sales Ranking',
                    labels={'Dollars': 'Sales ($)', 'DESCRIPTION': 'Brand'}
                )
                fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, width='stretch')

            with col2:
                # Market share
                top_brands_copy = top_brands.copy()
                total_top20 = top_brands_copy['Dollars'].sum()
                top_brands_copy['Share'] = (top_brands_copy['Dollars'] / total_top20 * 100)

                st.markdown("### Market Share %")
                share_table = top_brands_copy[['DESCRIPTION', 'Share', 'Dollars']].sort_values('Share', ascending=False)
                share_table.columns = ['Brand', 'Share %', 'Sales ($)']
                st.dataframe(
                    share_table.style.format({
                        'Share %': '{:.1f}%',
                        'Sales ($)': '${:,.0f}'
                    }),
                    height=600,
                    width='stretch'
                )

            st.markdown("---")

            # Growth leaders vs laggards
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Growth Leaders")
                growth_leaders = geo_data.nlargest(10, 'Dollars, % Chg, Yago')[['DESCRIPTION', 'Dollars', 'Dollars, % Chg, Yago']].copy()
                growth_leaders['Dollars, % Chg, Yago'] = growth_leaders['Dollars, % Chg, Yago'] * 100
                growth_leaders = growth_leaders[growth_leaders['Dollars, % Chg, Yago'] > 0]

                if not growth_leaders.empty:
                    fig = px.bar(
                        growth_leaders,
                        x='Dollars, % Chg, Yago',
                        y='DESCRIPTION',
                        orientation='h',
                        title='Fastest Growing Brands (YoY %)',
                        labels={'Dollars, % Chg, Yago': 'Growth %', 'DESCRIPTION': 'Brand'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')

            with col2:
                st.subheader("Declining Brands")
                decliners = geo_data.nsmallest(10, 'Dollars, % Chg, Yago')[['DESCRIPTION', 'Dollars', 'Dollars, % Chg, Yago']].copy()
                decliners['Dollars, % Chg, Yago'] = decliners['Dollars, % Chg, Yago'] * 100
                decliners = decliners[decliners['Dollars, % Chg, Yago'] < 0]

                if not decliners.empty:
                    fig = px.bar(
                        decliners,
                        x='Dollars, % Chg, Yago',
                        y='DESCRIPTION',
                        orientation='h',
                        title='Declining Brands (YoY %)',
                        labels={'Dollars, % Chg, Yago': 'Growth %', 'DESCRIPTION': 'Brand'},
                        color_discrete_sequence=['#dc3545']
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')

    elif page == "🏪 Retailer Performance":
        st.markdown('<p class="main-header">Retailer Performance</p>', unsafe_allow_html=True)
        st.markdown(f"**Period:** {selected_period}")
        st.markdown("---")

        # Focus on Humble
        humble_data = filtered_df[filtered_df['DESCRIPTION'] == 'HUMBLE'].copy()

        if not humble_data.empty:
            st.subheader("HUMBLE Performance by Retailer")
            st.markdown("*Retailers ranked by Performance Score (weighted combination of sales volume + growth)*")

            # Create comprehensive retailer scorecard
            scorecard = humble_data[[
                'GEOGRAPHY', 'Dollars', 'Units', 'Dollars, % Chg, Yago',
                'Max % ACV', 'TDP', 'Dollars, Promo', '# of Stores Selling'
            ]].copy()

            scorecard['Promo %'] = (scorecard['Dollars, Promo'] / scorecard['Dollars'] * 100)
            scorecard['Dollars, % Chg, Yago'] = scorecard['Dollars, % Chg, Yago'] * 100
            scorecard['Max % ACV'] = pd.to_numeric(scorecard['Max % ACV'], errors='coerce')

            # Calculate Performance Score (weighted: 70% volume, 30% growth)
            # Normalize sales to 0-100 scale
            max_sales = scorecard['Dollars'].max()
            scorecard['Sales Score'] = (scorecard['Dollars'] / max_sales * 100) if max_sales > 0 else 0

            # Growth score: cap at +50% and -50% for scoring purposes
            scorecard['Growth Score'] = scorecard['Dollars, % Chg, Yago'].clip(-50, 50)
            # Normalize to 0-100 scale (0% growth = 50 points, +50% = 100 points, -50% = 0 points)
            scorecard['Growth Score'] = ((scorecard['Growth Score'] + 50) / 100 * 100)

            # Combined Performance Score (70% sales, 30% growth)
            scorecard['Performance Score'] = (scorecard['Sales Score'] * 0.7 + scorecard['Growth Score'] * 0.3)

            # Add priority tier
            def get_priority(row):
                score = row['Performance Score']
                if score >= 70:
                    return '🟢 High'
                elif score >= 50:
                    return '🟡 Medium'
                else:
                    return '🔴 Low'

            scorecard['Priority'] = scorecard.apply(get_priority, axis=1)

            # Sort by performance score
            scorecard = scorecard.sort_values('Performance Score', ascending=False)

            # Display table
            display_cols = ['GEOGRAPHY', 'Performance Score', 'Priority', 'Dollars', 'Dollars, % Chg, Yago', 'Units', 'Max % ACV', 'TDP', 'Promo %', '# of Stores Selling']
            scorecard_display = scorecard[display_cols].copy()
            scorecard_display.columns = ['Retailer', 'Performance Score', 'Priority', 'Sales ($)', 'YoY Growth %', 'Units', 'ACV %', 'TDP', 'Promo %', 'Stores']

            st.dataframe(
                scorecard_display.style.format({
                    'Performance Score': '{:.0f}',
                    'Sales ($)': '${:,.0f}',
                    'Units': '{:,.0f}',
                    'YoY Growth %': '{:.1f}%',
                    'ACV %': '{:.1f}',
                    'TDP': '{:.1f}',
                    'Promo %': '{:.1f}%',
                    'Stores': '{:.0f}'
                }).background_gradient(subset=['Performance Score'], cmap='RdYlGn', vmin=0, vmax=100),
                width='stretch',
                height=400
            )

            # Add explanation
            with st.expander("ℹ️ How Performance Score Works"):
                st.markdown("""
                **Performance Score Formula:**
                - 70% weighted on Sales Volume (bigger accounts = higher score)
                - 30% weighted on YoY Growth Rate (faster growth = higher score)

                **Why This Matters:**
                - A retailer with $2M+ sales and 20% growth scores higher than one with $90K and 800% growth
                - Focuses your attention on accounts that drive real business impact
                - Growth is still rewarded, but volume ensures you prioritize the right accounts

                **Priority Tiers:**
                - 🟢 High (70-100): Top accounts - maintain momentum
                - 🟡 Medium (50-69): Important accounts - growth opportunities
                - 🔴 Low (<50): Monitor or consider de-prioritizing
                """)


            st.markdown("---")

            # Quadrant Analysis
            st.subheader("📊 Strategic Quadrant Analysis")
            st.markdown("*Volume vs Growth: Where should you focus your resources?*")

            # Create quadrant scatter plot
            median_sales = scorecard['Dollars'].median()
            median_growth = scorecard['Dollars, % Chg, Yago'].median()

            fig = go.Figure()

            # Add scatter points with color by priority
            for priority, color in [('🟢 High', '#28a745'), ('🟡 Medium', '#ffc107'), ('🔴 Low', '#dc3545')]:
                subset = scorecard[scorecard['Priority'] == priority]
                fig.add_trace(go.Scatter(
                    x=subset['Dollars'],
                    y=subset['Dollars, % Chg, Yago'],
                    mode='markers+text',
                    name=priority,
                    text=subset['GEOGRAPHY'].str[:15],  # Truncate long names
                    textposition='top center',
                    marker=dict(size=12, color=color),
                    hovertemplate='<b>%{text}</b><br>Sales: $%{x:,.0f}<br>Growth: %{y:.1f}%<extra></extra>'
                ))

            # Add median lines
            fig.add_hline(y=median_growth, line_dash="dash", line_color="gray", annotation_text="Median Growth")
            fig.add_vline(x=median_sales, line_dash="dash", line_color="gray", annotation_text="Median Sales")

            # Add quadrant labels
            max_sales = scorecard['Dollars'].max()
            max_growth = scorecard['Dollars, % Chg, Yago'].max()
            min_growth = scorecard['Dollars, % Chg, Yago'].min()

            annotations = [
                dict(x=max_sales * 0.75, y=max_growth * 0.9, text="🌟 STARS<br>(High Sales + High Growth)", showarrow=False, font=dict(size=10, color='green')),
                dict(x=max_sales * 0.75, y=min_growth * 0.5, text="💰 CASH COWS<br>(High Sales + Low Growth)", showarrow=False, font=dict(size=10, color='blue')),
                dict(x=median_sales * 0.3, y=max_growth * 0.9, text="🚀 RISING STARS<br>(Low Sales + High Growth)", showarrow=False, font=dict(size=10, color='orange')),
                dict(x=median_sales * 0.3, y=min_growth * 0.5, text="⚠️ QUESTION MARKS<br>(Low Sales + Low Growth)", showarrow=False, font=dict(size=10, color='red'))
            ]

            fig.update_layout(
                title='Retailer Portfolio Matrix',
                xaxis_title='Sales Volume ($)',
                yaxis_title='YoY Growth (%)',
                height=500,
                hovermode='closest',
                annotations=annotations,
                showlegend=True
            )

            st.plotly_chart(fig, width='stretch')

            # Add interpretation guide
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("**🌟 Stars**")
                stars = scorecard[(scorecard['Dollars'] > median_sales) & (scorecard['Dollars, % Chg, Yago'] > median_growth)]
                st.markdown(f"**{len(stars)} retailers**")
                st.markdown("*Invest & grow*")

            with col2:
                st.markdown("**💰 Cash Cows**")
                cash_cows = scorecard[(scorecard['Dollars'] > median_sales) & (scorecard['Dollars, % Chg, Yago'] <= median_growth)]
                st.markdown(f"**{len(cash_cows)} retailers**")
                st.markdown("*Maintain & optimize*")

            with col3:
                st.markdown("**🚀 Rising Stars**")
                rising = scorecard[(scorecard['Dollars'] <= median_sales) & (scorecard['Dollars, % Chg, Yago'] > median_growth)]
                st.markdown(f"**{len(rising)} retailers**")
                st.markdown("*Invest to scale*")

            with col4:
                st.markdown("**⚠️ Question Marks**")
                question = scorecard[(scorecard['Dollars'] <= median_sales) & (scorecard['Dollars, % Chg, Yago'] <= median_growth)]
                st.markdown(f"**{len(question)} retailers**")
                st.markdown("*Fix or exit*")

            st.markdown("---")

            # Additional visualizations
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Top 10 by Performance Score")
                top_performers = scorecard.head(10)[['GEOGRAPHY', 'Performance Score', 'Dollars', 'Dollars, % Chg, Yago']].copy()

                fig = px.bar(
                    top_performers,
                    x='Performance Score',
                    y='GEOGRAPHY',
                    orientation='h',
                    title='Highest Performing Retailers',
                    labels={'Performance Score': 'Score (0-100)', 'GEOGRAPHY': 'Retailer'},
                    color='Performance Score',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, width='stretch')

            with col2:
                st.subheader("Sales vs Distribution")
                scatter_data = scorecard.dropna(subset=['Max % ACV', 'Dollars']).head(15)

                fig = px.scatter(
                    scatter_data,
                    x='Max % ACV',
                    y='Dollars',
                    size='Units',
                    text='GEOGRAPHY',
                    labels={'Max % ACV': 'Distribution (ACV %)', 'Dollars': 'Sales ($)'},
                    title='Coverage vs Revenue'
                )
                fig.update_traces(textposition='top center', textfont_size=8)
                fig.update_layout(height=400)
                st.plotly_chart(fig, width='stretch')

    elif page == "📉 Trend Analysis":
        st.markdown('<p class="main-header">Trend Analysis</p>', unsafe_allow_html=True)
        st.markdown("---")

        # Geography selector for trends
        geographies = sorted(trend_df['GEOGRAPHY'].dropna().unique())
        selected_geos = st.multiselect(
            "Select Channels to Compare",
            geographies,
            default=['TOTAL US - NATURAL EXPANDED CHANNEL']
        )

        if selected_geos:
            trend_subset = trend_df[trend_df['GEOGRAPHY'].isin(selected_geos)].copy()

            # Sales trend
            st.subheader("Sales Trend (12-Week Rolling)")

            fig = px.line(
                trend_subset,
                x='Date',
                y='Dollars',
                color='GEOGRAPHY',
                markers=True,
                labels={'Dollars': 'Sales ($)', 'Date': 'Period', 'GEOGRAPHY': 'Channel'},
                title='HUMBLE Sales Trend by Channel'
            )
            fig.update_layout(height=400, hovermode='x unified')
            st.plotly_chart(fig, width='stretch')

            # Growth rate trend
            st.subheader("YoY Growth Rate Trend")

            trend_subset_growth = trend_subset.copy()
            trend_subset_growth['Dollars, % Chg, Yago'] = pd.to_numeric(trend_subset_growth['Dollars, % Chg, Yago'], errors='coerce') * 100

            fig = px.line(
                trend_subset_growth,
                x='Date',
                y='Dollars, % Chg, Yago',
                color='GEOGRAPHY',
                markers=True,
                labels={'Dollars, % Chg, Yago': 'YoY Growth %', 'Date': 'Period', 'GEOGRAPHY': 'Channel'},
                title='YoY Growth Rate Trend'
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.update_layout(height=400, hovermode='x unified')
            st.plotly_chart(fig, width='stretch')

            # Multi-metric dashboard
            st.markdown("---")
            st.subheader("Key Metrics Over Time")

            col1, col2 = st.columns(2)

            with col1:
                fig = px.line(
                    trend_subset,
                    x='Date',
                    y='Max % ACV',
                    color='GEOGRAPHY',
                    markers=True,
                    labels={'Max % ACV': 'ACV %', 'Date': 'Period', 'GEOGRAPHY': 'Channel'},
                    title='Distribution (Max % ACV)'
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, width='stretch')

            with col2:
                fig = px.line(
                    trend_subset,
                    x='Date',
                    y='TDP',
                    color='GEOGRAPHY',
                    markers=True,
                    labels={'TDP': 'TDP', 'Date': 'Period', 'GEOGRAPHY': 'Channel'},
                    title='Total Distribution Points (TDP)'
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, width='stretch')

            col1, col2 = st.columns(2)

            with col1:
                trend_subset_promo = trend_subset.copy()
                trend_subset_promo['Promo %'] = (trend_subset_promo['Dollars, Promo'] / trend_subset_promo['Dollars'] * 100)

                fig = px.line(
                    trend_subset_promo,
                    x='Date',
                    y='Promo %',
                    color='GEOGRAPHY',
                    markers=True,
                    labels={'Promo %': 'Promo Sales %', 'Date': 'Period', 'GEOGRAPHY': 'Channel'},
                    title='Promotional Activity (%)'
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, width='stretch')

            with col2:
                fig = px.line(
                    trend_subset,
                    x='Date',
                    y='# of Stores Selling',
                    color='GEOGRAPHY',
                    markers=True,
                    labels={'# of Stores Selling': 'Store Count', 'Date': 'Period', 'GEOGRAPHY': 'Channel'},
                    title='Number of Stores Selling'
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, width='stretch')

    elif page == "🎯 Promotional Analysis":
        st.markdown('<p class="main-header">Promotional Analysis</p>', unsafe_allow_html=True)
        st.markdown(f"**Period:** {selected_period}")
        st.markdown("---")

        # Focus on Humble
        humble_data = filtered_df[filtered_df['DESCRIPTION'] == 'HUMBLE'].copy()

        if not humble_data.empty:
            # Calculate promotional metrics
            humble_data['Promo %'] = (humble_data['Dollars, Promo'] / humble_data['Dollars'] * 100)
            humble_data['Units Promo %'] = (humble_data['Units, Promo'] / humble_data['Units'] * 100)

            # Summary
            total_sales = humble_data['Dollars'].sum()
            promo_sales = humble_data['Dollars, Promo'].sum()
            promo_pct = (promo_sales / total_sales * 100)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Sales", f"${total_sales:,.0f}")
            with col2:
                st.metric("Promo Sales", f"${promo_sales:,.0f}")
            with col3:
                st.metric("Promo %", f"{promo_pct:.1f}%")
            with col4:
                non_promo_sales = total_sales - promo_sales
                st.metric("Non-Promo Sales", f"${non_promo_sales:,.0f}")

            st.markdown("---")

            # Promo effectiveness by retailer
            st.subheader("Promotional Effectiveness by Retailer")

            promo_analysis = humble_data[[
                'GEOGRAPHY', 'Dollars', 'Dollars, Promo', 'Dollars, Non-Promo',
                'Units, Promo', 'Units, Non-Promo', 'Promo %'
            ]].copy()
            promo_analysis = promo_analysis.sort_values('Dollars', ascending=False)

            col1, col2 = st.columns([2, 1])

            with col1:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Promo Sales',
                    x=promo_analysis['GEOGRAPHY'],
                    y=promo_analysis['Dollars, Promo'],
                    marker_color='#ff7f0e'
                ))
                fig.add_trace(go.Bar(
                    name='Non-Promo Sales',
                    x=promo_analysis['GEOGRAPHY'],
                    y=promo_analysis['Dollars, Non-Promo'],
                    marker_color='#1f77b4'
                ))

                fig.update_layout(
                    barmode='stack',
                    title='Sales Mix: Promo vs Non-Promo by Retailer',
                    xaxis_title='Retailer',
                    yaxis_title='Sales ($)',
                    height=400,
                    xaxis={'tickangle': 45}
                )
                st.plotly_chart(fig, width='stretch')

            with col2:
                st.markdown("### Promo % by Retailer")
                promo_pct_data = promo_analysis[['GEOGRAPHY', 'Promo %']].sort_values('Promo %', ascending=False)
                promo_pct_data.columns = ['Retailer', 'Promo %']
                st.dataframe(
                    promo_pct_data.style.format({'Promo %': '{:.1f}%'}).background_gradient(subset=['Promo %'], cmap='Oranges'),
                    height=400,
                    width='stretch'
                )

            st.markdown("---")

            # Promo trends
            st.subheader("Promotional Trends Over Time")

            # Use trend data for time series
            trend_natural = trend_df[trend_df['GEOGRAPHY'] == 'TOTAL US - NATURAL EXPANDED CHANNEL'].copy()

            if not trend_natural.empty:
                trend_natural['Promo %'] = (trend_natural['Dollars, Promo'] / trend_natural['Dollars'] * 100)
                trend_natural['Units Promo %'] = (trend_natural['Units, Promo'] / trend_natural['Units'] * 100)

                col1, col2 = st.columns(2)

                with col1:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=trend_natural['Date'],
                        y=trend_natural['Dollars, Promo'],
                        name='Promo Sales',
                        fill='tonexty',
                        line=dict(color='#ff7f0e')
                    ))
                    fig.add_trace(go.Scatter(
                        x=trend_natural['Date'],
                        y=trend_natural['Dollars, Non-Promo'],
                        name='Non-Promo Sales',
                        fill='tozeroy',
                        line=dict(color='#1f77b4')
                    ))

                    fig.update_layout(
                        title='Promo vs Non-Promo Sales Trend',
                        xaxis_title='Date',
                        yaxis_title='Sales ($)',
                        height=350,
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    fig = px.line(
                        trend_natural,
                        x='Date',
                        y='Promo %',
                        markers=True,
                        labels={'Promo %': 'Promotional Sales %', 'Date': 'Period'},
                        title='Promotional Mix % Over Time'
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, width='stretch')

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Data Refresh")
    st.sidebar.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.markdown("""
    This dashboard analyzes SPINS market data for marketing decision-making.

    **Key Metrics:**
    - **Sales**: Dollar and unit volume
    - **ACV**: All Commodity Volume (store coverage %)
    - **TDP**: Total Distribution Points (weighted distribution)
    - **ARP**: Average Retail Price
    - **YoY**: Year-over-year comparison
    """)

else:
    st.error("Unable to load data. Please ensure the Excel files are in the correct directory.")
