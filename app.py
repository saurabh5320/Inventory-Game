import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Inventory Game", page_icon="📦", layout="wide")

# ---------------- Parameters ----------------
DEFAULT_DAYS = 30
DEFAULT_PRODUCT_COST = 100.0
DEFAULT_HOLDING_RATE = 0.20   # 20% per year
DEFAULT_SHORTAGE_COST = 20.0  # per unit

# ---------------- Load Fixed Demand ----------------
@st.cache_data
def load_fixed_demand():
    df = pd.read_csv("sample_demand.csv")
    if "demand" not in df.columns:
        st.stop()
    return df["demand"].astype(int).tolist()

# ---------------- Session Init ----------------
def init_state():
    if "initialized" in st.session_state and st.session_state.initialized:
        return
    st.session_state.initialized = True
    st.session_state.day = 1
    st.session_state.inv_start = 0
    st.session_state.records = []  # list of dict rows
    st.session_state.demand = load_fixed_demand()
    st.session_state.params = dict(
        days=min(len(st.session_state.demand), DEFAULT_DAYS),
        product_cost=DEFAULT_PRODUCT_COST,
        holding_rate=DEFAULT_HOLDING_RATE,
        shortage_cost=DEFAULT_SHORTAGE_COST,
    )

def reset_game():
    st.session_state.day = 1
    st.session_state.inv_start = 0
    st.session_state.records = []

def holding_cost_per_day(product_cost, holding_rate):
    return (product_cost * holding_rate) / 365.0

# ---------------- Sidebar ----------------
init_state()
with st.sidebar:
    st.header("⚙️ Game Settings (Fixed Demand)")
    st.write("Demand is preloaded from **sample_demand.csv** and cannot be changed.")
    st.session_state.params["days"] = len(st.session_state.demand)
    st.metric("Days in Game", value=len(st.session_state.demand))
    st.metric("Product Cost (₹)", value=DEFAULT_PRODUCT_COST)
    st.metric("Holding Rate (per year)", value=f"{DEFAULT_HOLDING_RATE*100:.0f}%")
    st.metric("Shortage Cost (₹/unit)", value=DEFAULT_SHORTAGE_COST)

    if st.button("🔄 Restart Game", use_container_width=True):
        reset_game()

days = st.session_state.params["days"]
product_cost = st.session_state.params["product_cost"]
holding_rate = st.session_state.params["holding_rate"]
shortage_cost = st.session_state.params["shortage_cost"]
hcost_day = holding_cost_per_day(product_cost, holding_rate)

# ---------------- Main UI ----------------
st.title("📦 Single-Item Inventory Game (Fixed Demand)")
st.caption("Each day, decide how much to order before demand is revealed. Holding cost is 20%/year of unit cost; shortage cost is ₹20/unit.")

# Show progress
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Day", value=st.session_state.day, delta=None)
with c2: st.metric("Starting Inventory", value=st.session_state.inv_start)
with c3: st.metric("Unit Cost (₹)", value=product_cost)
with c4: st.metric("Holding/Day (₹)", value=round(hcost_day, 2))

st.divider()

# Game loop (no backorders; lost sales)
if st.session_state.day <= days:
    st.subheader(f"Day {st.session_state.day} — Place Your Order (before demand)")
    order_qty = st.number_input("Order quantity", min_value=0, step=1, value=0)
    place = st.button("✅ Place Order")
    if place:
        d_idx = st.session_state.day - 1
        today_demand = int(st.session_state.demand[d_idx])

        inv_before_sales = int(st.session_state.inv_start) + int(order_qty)
        sales = min(inv_before_sales, today_demand)
        shortage_units = max(0, today_demand - inv_before_sales)
        inv_end = inv_before_sales - sales

        purchase_cost = order_qty * product_cost
        holding_cost = inv_end * hcost_day
        shortage_penalty = shortage_units * shortage_cost
        day_cost = purchase_cost + holding_cost + shortage_penalty

        st.success(f"Demand today: {today_demand} | Sold: {sales} | Shortage: {shortage_units} | End Inv: {inv_end}")
        st.info(f"Costs → Purchase ₹{purchase_cost:.2f} + Holding ₹{holding_cost:.2f} + Shortage ₹{shortage_penalty:.2f} = **₹{day_cost:.2f}**")

        st.session_state.records.append(dict(
            day=st.session_state.day,
            order=int(order_qty),
            demand=today_demand,
            sales=int(sales),
            shortage=int(shortage_units),
            inv_end=int(inv_end),
            purchase_cost=float(purchase_cost),
            holding_cost=float(holding_cost),
            shortage_cost=float(shortage_penalty),
            day_cost=float(day_cost)
        ))

        st.session_state.inv_start = int(inv_end)
        st.session_state.day += 1

# Summary when game ends or in-progress
if len(st.session_state.records) > 0:
    df = pd.DataFrame(st.session_state.records)
    df["cum_cost"] = df["day_cost"].cumsum()
    st.subheader("📊 Daily Results")
    st.dataframe(df, use_container_width=True)

    # Charts
    st.subheader("📈 Trends")
    base = alt.Chart(df).encode(x="day:Q")
    c_orders = base.mark_line(point=True).encode(y=alt.Y("order:Q", title="Order / Demand / Inventory"), color=alt.value("#4e79a7"))
    c_demand = base.mark_line(point=True).encode(y="demand:Q", color=alt.value("#59a14f"))
    c_inv = base.mark_line(point=True).encode(y="inv_end:Q", color=alt.value("#f28e2b"))
    st.altair_chart(alt.layer(c_orders, c_demand, c_inv).properties(width=900, height=350), use_container_width=True)

    c_cost = alt.Chart(df).mark_line(point=True).encode(
        x="day:Q", y=alt.Y("cum_cost:Q", title="Cumulative Cost (₹)")
    ).properties(width=900, height=300)
    st.altair_chart(c_cost, use_container_width=True)

    total_cost = float(df["day_cost"].sum())
    left, right = st.columns(2)
    with left:
        st.metric("Total Cost (₹)", value=round(total_cost, 2))
    with right:
        st.download_button("⬇️ Download Results (CSV)", data=df.to_csv(index=False).encode("utf-8"), file_name="results.csv", mime="text/csv")
else:
    st.info("Place your first order to begin. Demand is fixed and hidden until you order.")
