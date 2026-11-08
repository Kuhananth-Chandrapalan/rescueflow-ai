"""RescueFlow AI — transparent, model-assisted food inventory decisions.

Run with `streamlit run app.py`. All built-in sales data are synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from rescueflow.demo import demo_history, inventory_catalog
from rescueflow.decisions import make_recommendations
from rescueflow.forecast import train_and_forecast
from rescueflow.report import impact_summary
from rescueflow.validation import validate_pair
from rescueflow.weather import get_weather
from rescueflow.stockout import calculate_stockout_risk

st.set_page_config(page_title="RescueFlow AI | Decision Intelligence", page_icon="🌱",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
.block-container {padding-top: 1.7rem; max-width: 1440px;}
[data-testid="stMetric"] {background:linear-gradient(145deg,#15253b,#102033);
 border:1px solid #263d4a;border-radius:14px;padding:16px 20px;}
[data-testid="stMetricLabel"] {color:#99b5bb;}
h1,h2,h3 {letter-spacing:-.03em;}
.hero {padding:26px 30px;border-radius:20px;border:1px solid #294452;
 background:radial-gradient(ellipse at 90% 10%,#1a604e 0%,transparent 35%),
 linear-gradient(120deg,#13293a,#102032); margin-bottom:22px;}
.kicker {color:#77e8b8;font-size:.77rem;letter-spacing:.2em;font-weight:800;}
.hero h1 {margin:6px 0 8px;font-size:2.25rem;}
.hero p {color:#b0c8cb;max-width:800px;font-size:1.05rem;}
.note {border-left:3px solid #70cbb2;padding:12px 18px;
 background:#142537;border-radius:0 10px 10px 0;color:#b8cecf;}
</style>""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def get_demo(as_of: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    return demo_history(as_of=as_of), inventory_catalog()

@st.cache_data(show_spinner="Training demand model and backtesting...")
def compute_predictions(history: pd.DataFrame, horizon: int, shift: float,
                        weather: pd.DataFrame | None):
    return train_and_forecast(history, horizon=horizon, temperature_shift=shift, weather=weather)


today = datetime.now(ZoneInfo("Asia/Colombo")).date().isoformat()

st.sidebar.markdown("## 🌱 RescueFlow AI")
st.sidebar.caption("FOOD SYSTEM DECISION INTELLIGENCE")
st.sidebar.markdown("---")
st.sidebar.subheader("Scenario controls")
forecast_days = st.sidebar.slider("Planning horizon (days)", 7, 14, 14)
budget = st.sidebar.slider("Replenishment budget ($)", 100, 3500, 1200, step=50)
safety_days = st.sidebar.slider("Safety stock (days)", 0.0, 5.0, 1.5, step=0.5)
temp_shift = st.sidebar.slider("Temperature scenario (°C)", -3.0, 5.0, 0.0, step=0.5)
st.sidebar.markdown("---")
st.sidebar.subheader("Input data")
mode = st.sidebar.radio("Data source", ["Synthetic demonstration", "Upload business CSVs"], index=0)

if mode == "Synthetic demonstration":
    history, catalog = get_demo(today)
    st.sidebar.success("Reproducible demo dataset")
else:
    history_file = st.sidebar.file_uploader("Demand history (CSV)", type="csv")
    stock_file = st.sidebar.file_uploader("Inventory catalog (CSV)", type="csv")
    if history_file is None or stock_file is None:
        st.info("Upload both the demand history and the inventory catalog, matching the sample schema in Data & Methodology.")
        st.stop()
    try:
        history, catalog = pd.read_csv(history_file), pd.read_csv(stock_file)
    except Exception as exc:
        st.error(f"Unable to read CSV files: {exc}")
        st.stop()

try:
    history, catalog = validate_pair(history, catalog)
except (ValueError, TypeError) as exc:
    st.error(f"Data validation failed: {exc}")
    st.stop()

st.sidebar.markdown("---")
use_weather = st.sidebar.checkbox("Use live Open-Meteo weather forecast", value=False,
                                   help="Non-commercial free API; no key needed. Demo remains illustrative.")
weather = None
if use_weather:
    if st.sidebar.button("Fetch weather for Colombo"):
        try:
            weather = get_weather(days=forecast_days)
            st.session_state["weather"] = weather
            st.sidebar.success("Weather forecast loaded")
        except Exception as exc:
            st.sidebar.warning("Weather unavailable; using last observed weather")
    weather = st.session_state.get("weather")
    if weather is not None and not weather.empty:
        st.sidebar.caption("Source: Open-Meteo, CC BY 4.0. Weather dates may not match a fixed synthetic demonstration period.")

with st.container():
    st.markdown("""<div class="hero">
      <div class="kicker">SUPPLY CHAIN / PREDICTIVE INTELLIGENCE</div>
      <h1>RescueFlow AI <span style="color:#77e8b8">/ Control Tower</span></h1>
      <p>Forecast product demand, prioritize restocking within a fixed budget, and identify potential food rescue opportunities — with measurable model error and transparent reasoning.</p>
    </div>""", unsafe_allow_html=True)

try:
    forecasts = compute_predictions(history, forecast_days, temp_shift, weather)
    decisions = make_recommendations(catalog, forecasts.forecasts, budget, safety_days)
    summary = impact_summary(decisions, budget)
    stockout_risk_df = calculate_stockout_risk(catalog, forecasts.forecasts)
except Exception as exc:
    st.error(f"Forecast or decision engine failed: {exc}")
    st.stop()

if mode == "Synthetic demonstration":
    st.warning("**Demonstration data:** All demand, stock, costs and emissions factors are synthetic. Forecasts and operational recommendations must not be used as real business decisions without validation on real data.", icon="⚠️")

kpis = st.columns(5)
high_risk_count = int((stockout_risk_df.stockout_probability >= 0.75).sum())
for col, label, value, help_text in zip(kpis,
    ["7-day demand", "Suggested units to order", "Order budget", "Rescue opportunity", "Stockout-risk SKUs"],
    [f"{summary['total_forecast_units']:,} units", f"{summary['order_units']:,} units",
     f"${summary['order_spend']:,.0f} / ${budget:,.0f}", f"{summary['donation_kg']:.1f} kg",
     str(high_risk_count)],
    ["*Sum over next 7 days", "Heuristic recommendations", "Estimated cost, not a purchase order",
     "A conservative donation screening proxy", "SKUs with high stockout probability (>= 75%)"]):
    col.metric(label, value, help=help_text)

st.caption("Demand and purchase planning totals cover 7 days; the forecast chart spans the selected 7–14 days. Currency values are illustrative USD equivalents, not live market prices.")

t1, t2, t3, t4, t5, t6 = st.tabs(["📈 Demand Intelligence", "🧭 Replenishment", "⚠️ Stockout Risk", "🥬 Food Rescue",
                                    "🧪 Model Quality", "📚 Data & Methodology"])

with t1:
    left, right = st.columns([1.85, 1])
    with left:
        st.subheader("Forecast trajectory")
        options = catalog.set_index("sku")["product"].to_dict()
        selected = st.selectbox("Inspect SKU", list(options), format_func=lambda x: f"{options[x]}  ·  {x}")
        past = history[history.sku == selected].sort_values("date").tail(45)
        future = forecasts.forecasts[forecasts.forecasts.sku == selected]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=past.date, y=past.units_sold, name="Observed (synthetic)",
                                 line=dict(color="#76a7c9", width=2)))
        # Prediction interval quantile bands (lower and upper)
        fig.add_trace(go.Scatter(x=future.date, y=future.upper_units,
                                 mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=future.date, y=future.lower_units,
                                 mode="lines", line=dict(width=0), fillcolor="rgba(120, 226, 178, 0.2)",
                                 fill="tonexty", name="Empirical band (80%)", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=future.date, y=future.predicted_units,
                                 name="AI forecast", line=dict(color="#78e2b2", width=3)))
        fig.update_layout(height=405, template="plotly_dark", margin=dict(l=5, r=5, t=15, b=5),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          yaxis_title="Units", legend_orientation="h")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Projected demand by category")
        chart = decisions.groupby("category", as_index=False).forecast_7d.sum()
        fig = px.bar(chart, x="forecast_7d", y="category", orientation="h", color="category",
                     labels={"forecast_7d": "Forecast units", "category": ""},
                     color_discrete_sequence=["#76c9a8", "#7ca3e7", "#d5aa77", "#ae8fd8", "#df8997"])
        fig.update_layout(height=405, template="plotly_dark", showlegend=False,
                          margin=dict(l=0, r=0, t=15, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div class="note">Forecasts use a supervised random forest trained on prior demand, calendar and weather features. Shaded empirical quantile bands reflect historical holdout residual spreads scaled by horizon length. External validation is required before relying on intervals for safety stock.</div>', unsafe_allow_html=True)

with t2:
    st.subheader("Replenishment decision queue")
    st.caption("Priority is based on expected avoidable shortage margin per dollar, constrained by available budget and approximate shelf life.")
    shown = decisions[["product", "category", "on_hand", "daily_prediction", "shortage_risk_units",
                       "order_needed", "order_units", "order_cost", "reason"]].copy()
    shown.columns = ["Product", "Category", "In stock", "Demand/day", "Lead-time shortage",
                     "Wanted units", "Suggested order", "Est. spend ($)", "Why this recommendation"]
    st.dataframe(shown, hide_index=True, use_container_width=True, column_config={
        "Demand/day": st.column_config.NumberColumn(format="%.1f"),
        "Lead-time shortage": st.column_config.NumberColumn(format="%.1f"),
        "Est. spend ($)": st.column_config.NumberColumn(format="$%.2f")})
    st.download_button("Download replenishment plan (CSV)", data=shown.to_csv(index=False),
                       file_name="rescueflow_replenishment.csv", mime="text/csv")
    st.markdown(f"**Unspent simulated budget:** ${summary['budget_remaining']:,.2f}")
    st.info("This is a decision-support heuristic—not an optimized procurement plan. Supplier pack sizes, real expiry batches, cold-chain constraints, and actual vendor prices are not yet modeled.")

with t3:
    st.subheader("Stockout Risk Scoring & Priority Badges")
    st.caption("Calibrated proxy risk score estimating stockout probability before supplier lead-time replenishment arrives.")
    risk_view = stockout_risk_df[["product", "category", "stock_units", "lead_days", "daily_demand", "lead_time_demand", "stockout_probability", "risk_badge"]].copy()
    risk_view.columns = ["Product", "Category", "In Stock", "Lead (days)", "Demand/day", "Lead Demand", "Risk Probability", "Priority Badge"]
    st.dataframe(risk_view, hide_index=True, use_container_width=True, column_config={
        "Demand/day": st.column_config.NumberColumn(format="%.1f"),
        "Lead Demand": st.column_config.NumberColumn(format="%.1f"),
        "Risk Probability": st.column_config.NumberColumn(format="%.3f")
    })
    st.markdown('<div class="note"><strong>Probability Disclaimer & Interpretation:</strong> Stockout probabilities are calibrated heuristic proxy scores comparing current stock levels against expected lead-time demand. High Risk (>= 75%) indicates stock is likely to deplete before replenishment; Moderate Risk (40-74%) indicates tight margins; Secure (< 40%) indicates adequate buffer. Probabilities assume stationary demand and must not be used as guaranteed operational failure rates without physical warehouse auditing.</div>', unsafe_allow_html=True)

with t4:
    st.subheader("Potential food rescue opportunities")
    st.caption("Donation screening only: inventory above expected demand before shelf-life expiry plus a safety buffer.")
    donation = decisions[decisions.donation_units > 0][["product", "category", "donation_units", "donation_kg", "avoided_co2_kg_proxy"]]
    if len(donation):
        fig = px.bar(donation.sort_values("donation_kg"), y="product", x="donation_kg",
                     orientation="h", color="category", height=320,
                     labels={"donation_kg": "Potential donation (kg)", "product": ""})
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=5, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(donation, use_container_width=True, hide_index=True)
    else:
        st.info("No donation candidates in this simulated scenario; increase on-hand stock to explore rescue cases.")
    st.metric("Potential carbon impact (illustrative factor only)", f"{summary['proxy_co2_kg']:.1f} kg CO₂e")
    st.warning("Never donate solely based on this estimate. Inspect expiry dates, food handling, allergen labeling, beneficiary demand, transport, and local food-safety law.")

with t5:
    st.subheader("Rolling 1-day MAE vs True 7/14-Day Horizon Backtest")
    a, b, c = st.columns(3)
    a.metric("Rolling 1-day MAE", f"{forecasts.metrics.mae.mean():.2f} units")
    b.metric("7-day Horizon MAE", f"{forecasts.multiday_metrics[forecasts.multiday_metrics.horizon == 7].multiday_mae.mean():.2f} units")
    c.metric("14-day Horizon MAE", f"{forecasts.multiday_metrics[forecasts.multiday_metrics.horizon == 14].multiday_mae.mean():.2f} units")

    st.markdown("### Detailed Horizon Performance Summary")
    st.dataframe(forecasts.multiday_metrics, hide_index=True, use_container_width=True,
                 column_config={"multiday_mae": st.column_config.NumberColumn(format="%.2f")})

    st.markdown("### Rolling 1-Day vs Baseline Holdout Metrics")
    st.dataframe(forecasts.metrics, hide_index=True, use_container_width=True,
                 column_config={"mae": st.column_config.NumberColumn(format="%.2f"),
                                "baseline_mae": st.column_config.NumberColumn(format="%.2f")})

    imp_fig = px.bar(forecasts.feature_importance.sort_values("importance"),
                     y="feature", x="importance", orientation="h", height=380,
                     labels={"importance": "Random forest feature importance", "feature": ""})
    imp_fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(imp_fig, use_container_width=True)
    st.markdown('<div class="note"><strong>Multi-Horizon Backtesting Interpretation & Limits:</strong> True 7- and 14-day horizon evaluations simulate historical cutoffs where multi-day forecasts are rolled out autoregressively using past predictions as lags. Error increases over longer horizons due to compounded error propagation. These evaluations assume stationary demand distributions and should be used alongside rolling 1-day MAE for comprehensive error tracking.</div>', unsafe_allow_html=True)

with t6:
    st.subheader("Reproducible inputs and honest limitations")
    st.markdown("""**Source provenance:** Demo data generated deterministically; no genuine shop sales, donor inventory, or measured emissions are supplied. The optional Open-Meteo API is available for non-commercial demonstration only and requires attribution.\n\n**Stockout Risk Scoring:** Stockout risk is computed as a calibrated sigmoid proxy score measuring the likelihood that lead-time demand will exceed on-hand inventory. Priority badges (High Risk, Moderate Risk, Secure) provide visual triage but require physical inventory verification.\n\n**Prediction intervals & Decision boundaries:** Empirical quantile bands estimate lower and upper demand ranges from holdout validation residuals, scaled across multi-day horizons. Because future supply chains involve shifting patterns, external validation is mandatory before relying on bands for safety buffer sizing. Carbon impacts are illustrative static factors, not verified life-cycle assessments.\n\n**Before real deployment:** Validate customer data, item-level expiry lots, supply constraints, actual lead times, availability of donations, real costs, privacy, bias, and food-safety requirements.\n\n**Minimum CSV schema:** Demand: `date,sku,units_sold,temperature_c,precip_mm,promotion`. Inventory: `sku,product,category,shelf_life_days,unit_cost,unit_price,lead_days,stock_units,co2_kg_per_unit,kg_per_unit`. Requires 80+ consecutive daily rows per SKU and identical SKU sets.""")
    d1, d2 = st.columns(2)
    with d1:
        st.download_button("Download example demand CSV", get_demo(today)[0].to_csv(index=False),
                           "example_demand.csv", "text/csv")
    with d2:
        st.download_button("Download example inventory CSV", get_demo(today)[1].to_csv(index=False),
                           "example_inventory.csv", "text/csv")
    st.caption("Weather attribution: https://open-meteo.com/ — Open-Meteo weather data, CC BY 4.0.")

st.markdown("---")
st.caption("RescueFlow AI · Demonstration / research prototype · All operational decisions require human review")
