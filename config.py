"""
Dashboard Configuration
Modify these settings to customize the dashboard behavior
"""

# Data file paths
BRAND_DATA_FILE = "SPINs Brand and Retailers_110225.xlsx"
TREND_DATA_FILE = "SPINs Humble_Trended Sale_100525.xlsx"

# Dashboard settings
DASHBOARD_TITLE = "SPINS Marketing Intelligence Dashboard"
PAGE_ICON = "📊"

# Default brand for analysis
DEFAULT_BRAND = "HUMBLE"

# Chart color schemes
COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'positive': '#28a745',
    'negative': '#dc3545',
    'neutral': '#6c757d',
    'promo': '#ff7f0e',
    'non_promo': '#1f77b4'
}

# Display settings
CHART_HEIGHT_DEFAULT = 400
CHART_HEIGHT_TALL = 600
CHART_HEIGHT_SHORT = 350

# Number of items to show in rankings
TOP_N_BRANDS = 20
TOP_N_RETAILERS = 10

# Metric formatting
CURRENCY_FORMAT = "${:,.0f}"
PERCENT_FORMAT = "{:.1f}%"
NUMBER_FORMAT = "{:,.0f}"
DECIMAL_FORMAT = "{:.2f}"

# Key metrics to display
KEY_METRICS = [
    'Dollars',
    'Units',
    'Max % ACV',
    'TDP',
    'Dollars, % Chg, Yago',
    'Dollars, Promo',
    'Dollars, Non-Promo'
]

# Geography/Channel preferences
NATURAL_CHANNEL = "TOTAL US - NATURAL EXPANDED CHANNEL"
MULO_CHANNEL = "TOTAL US - MULO"
FOOD_CHANNEL = "TOTAL US - FOOD"

# Trend analysis settings
DEFAULT_TREND_CHANNELS = [NATURAL_CHANNEL]
TREND_PERIOD_TYPE = "12 Weeks"  # Rolling period type in trend data

# Promotional analysis thresholds
HIGH_PROMO_THRESHOLD = 40  # % above which is considered high promotional activity
LOW_PROMO_THRESHOLD = 15   # % below which is considered low promotional activity

# Growth rate thresholds for color coding
HIGH_GROWTH_THRESHOLD = 20  # % YoY growth
MODERATE_GROWTH_THRESHOLD = 10
DECLINE_THRESHOLD = 0

# Data validation settings
REQUIRED_BRAND_SHEETS = ['Raw', 'Pivot']
REQUIRED_TREND_SHEETS = ['Raw']

# Archive settings
ARCHIVE_FOLDER = "archive"
ARCHIVE_ENABLED = True

# Time period preferences (for filtering)
PREFERRED_TIME_PERIODS = [
    "4 Weeks",
    "12 Weeks",
    "24 Weeks",
    "52 Weeks"
]

# Export settings
EXPORT_DATE_FORMAT = "%Y-%m-%d"
EXPORT_FILENAME_PREFIX = "SPINS_Dashboard_Export"

# Custom retail groupings (for aggregated analysis)
RETAIL_GROUPS = {
    'Ahold/Delhaize': [
        'AD - AHOLD CORP - RMA',
        'AD - AHOLD DELHAIZE CORP - RMA',
        'AD - AHOLD GIANT CARLISLE DIV - RMA',
        'AD - AHOLD GIANT LANDOVER DIV - RMA',
        'AD - AHOLD STOP & SHOP DIV - RMA',
        'AD - DELHAIZE CORP - RMA',
        'AD - DELHAIZE FOOD LION CORP - RMA',
        'AD - DELHAIZE HANNAFORD CORP DC1 - RMA'
    ],
    'Natural Specialty': [
        'NATURAL GROCERS BY VC - TOTAL US',
        'SPROUTS FARMERS MARKET - TOTAL US W/O PL',
        'RALEYS - TOTAL US'
    ]
}

# Metric definitions (for help tooltips)
METRIC_DEFINITIONS = {
    'ACV': 'All Commodity Volume - % of stores carrying the product weighted by store size',
    'TDP': 'Total Distribution Points - Sum of ACV across all items/SKUs',
    'ARP': 'Average Retail Price - Dollar sales divided by unit sales',
    'YoY': 'Year-over-year comparison with same period last year',
    'Promo': 'Sales occurring during promotional periods',
    'Non-Promo': 'Baseline sales outside of promotional periods',
    'Units per Store': 'Sales velocity metric - units sold per store carrying the product'
}

# Feature flags (enable/disable dashboard sections)
FEATURES = {
    'executive_overview': True,
    'sales_performance': True,
    'competitive_analysis': True,
    'retailer_performance': True,
    'trend_analysis': True,
    'promotional_analysis': True,
    'export_to_excel': False,  # Future feature
    'automated_insights': False  # Future feature
}

# Alert thresholds (for highlighting significant changes)
ALERTS = {
    'large_sales_decline': -10,  # % YoY
    'distribution_loss': -5,     # ACV point change
    'high_promo_dependency': 50  # % of sales from promo
}
