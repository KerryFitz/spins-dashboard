# SPINS Dashboard - Quick Start Guide

## Start the Dashboard (First Time)

```bash
cd /Users/kerryfitzmaurice/Desktop/SPINS/2025
streamlit run spins_dashboard.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`

## Dashboard Navigation

### 6 Key Views:

1. **🏠 Executive Overview**
   - Quick KPIs: Sales, Units, Distribution, Promo %
   - Top retailers and growth rates
   - Sales trend over time

2. **📈 Sales Performance**
   - Select any brand to analyze
   - Sales by retailer with growth rates
   - Promo vs non-promo mix
   - Distribution and velocity metrics

3. **🏆 Competitive Analysis**
   - Top 20 brands by sales
   - Market share analysis
   - Growth leaders vs declining brands
   - Select any retailer to compare brands

4. **🏪 Retailer Performance**
   - HUMBLE performance across all retailers
   - Comprehensive scorecard with all metrics
   - Sales vs distribution matrix
   - Growth rate comparisons

5. **📉 Trend Analysis**
   - Historical trends from 2022 to present
   - Compare multiple channels
   - Track sales, growth, distribution, and promotions over time

6. **🎯 Promotional Analysis**
   - Promo effectiveness by retailer
   - Promo vs non-promo sales breakdown
   - Promotional trends over time

## Weekly Update Process

### When you receive new SPINS data:

```bash
python3 update_data.py \
  --brand-file "path/to/new/SPINs_Brand_file.xlsx" \
  --trend-file "path/to/new/SPINs_Trend_file.xlsx"
```

Then restart the dashboard to see the new data.

## Key Marketing Insights to Track

### Weekly Checklist:
- [ ] Check total sales trend (Executive Overview)
- [ ] Monitor YoY growth rate
- [ ] Review top performing retailers
- [ ] Identify declining channels for action
- [ ] Track distribution (ACV) changes
- [ ] Analyze promotional effectiveness
- [ ] Compare vs key competitors

### Monthly Deep Dives:
- Review 12-week and 52-week trends
- Analyze seasonal patterns
- Evaluate pricing vs competition
- Assess promotional ROI by retailer
- Track market share changes

## Common Questions

**Q: How do I see HUMBLE's performance?**
A: Go to Executive Overview - it defaults to HUMBLE. Or select "HUMBLE" in Sales Performance view.

**Q: How do I compare HUMBLE to competitors?**
A: Go to Competitive Analysis, select a retailer (like "TOTAL US - NATURAL EXPANDED CHANNEL"), and see the top 20 brands ranked by sales.

**Q: Where can I see historical trends?**
A: Trend Analysis view shows rolling 12-week data from Jan 2022 to present.

**Q: How do I know if promotions are working?**
A: Promotional Analysis shows promo vs non-promo split and trends. Higher promo % means you're driving sales through promotions.

**Q: What's a good ACV %?**
A: Higher is better. ACV shows what % of stores carry your product. 100% = available in all stores in that channel.

## Tips for Presentations

1. **Executive Overview** - Perfect for weekly leadership updates
2. **Take screenshots** - Charts are interactive but can be screenshotted for PowerPoint
3. **Filter by time period** - Use 4-week for recent performance, 52-week for annual trends
4. **Compare periods** - YoY % change shows if you're growing or declining
5. **Use Retailer Performance** - Great for account management meetings

## Need Help?

- **Dashboard won't start**: Check that all packages are installed (`pip install streamlit pandas plotly openpyxl`)
- **No data showing**: Verify Excel files are in the same folder as the dashboard
- **Charts empty**: Check your filter selections in the sidebar
- **See full documentation**: Open `README.md`

---

**Pro Tip**: Keep the dashboard open during planning meetings and filter in real-time to answer questions on the spot!
