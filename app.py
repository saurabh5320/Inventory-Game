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

# ---------------- Session Init ----------------
def init_state():
    if "initialized" in st.session_state and st.session_state.initialized:
        return
    st.session_state.initialized = True
    st.session_state.day = 1
    st.session_state.inv_start = 0
    st.session_state.records = []  # list of dict rows
    st.session_state.demand = None
    st.session_state.params = dict(
        days=DEFAULT_DAYS,
        product_cost=DEFAULT_PRODUCT_COST,
        holding_rate=DEFAULT_HOLDING_RATE,
        shortage_cost=DEFAULT_SHORTAGE_COST,
    )

def reset_game():
    st.session_state.day = 1
    st.session_state.inv_start = 0
    st.session_state.records = []

def set_demand_from_series(series):
    st.session_state.demand = list(series)

def ensure_demand():
    # If demand not set yet, generate with seed and bounds
    if st.session_state.demand is None:
        seed = st.session_state.get("seed", 42)
        low = st.session_state.get("rand_low", 30)
        high = st.session_state.get("rand_high", 100)
        rng = np.random.default_rng(seed)
        dem = rng.integers(low, high+1, size=st.session_state.params["days"])
        set_demand_from_series(dem)

def holding_cost_per_day(product_cost, holding_rate):
    return (product_cost * holding_rate) / 365.0

# ---------------- Sidebar ----------------
init_state()
with st.sidebar:
    st.header("⚙️ Game Settings")
    days = st.number_input("Total days", 5, 120, st.session_state.params["days"], 1)
    product_cost = st.number_input("Product cost (₹/unit)", 1.0, 1e6, st.session_state.params["product_cost"], 1.0)
    holding_rate = st.number_input("Holding cost rate (per year)", 0.0, 1.0, st.session_state.params["holding_rate"], 0.01, format="%.2f")
    shortage_cost = st.number_input("Shortage (lost sales) cost (₹/unit)", 0.0, 1e6, st.session_state.params["shortage_cost"], 1.0)

    st.session_state.params.update(dict(
        days=int(days),
        product_cost=float(product_cost),
        holding_rate=float(holding_rate),
        shortage_cost=float(shortage_cost),
    ))

    st.divider()
    st.subheader("Demand Input")
    up = st.file_uploader("Upload demand CSV (one column named 'demand')", type=["csv"])
    seed = st.number_input("Or use random demand — Seed", 0, 10**9, int(st.session_state.get("seed", 42)))
    rand_low = st.number_input("Random min demand", 0, 100000, int(st.session_state.get("rand_low", 30)))
    rand_high = st.number_input("Random max demand", 0, 100000, int(st.session_state.get("rand_high", 100)))

    st.session_state.seed = int(seed)
    st.session_state.rand_low = int(rand_low)
    st.session_state.rand_high = int(rand_high)

    colb1, colb2 = st.columns(2)
    with colb1:
        if st.button("🔄 Reset Game", use_container_width=True):
            reset_game()
    with colb2:
        if st.button("🎲 Regenerate Demand", use_container_width=True):
            st.session_state.demand = None
            reset_game()

# Handle demand source
if up is not None:
    try:
        df_up = pd.read_csv(up)
        if "demand" not in df_up.columns:
            st.error("CSV must have a column named 'demand'.")
        else:
            dser = df_up["demand"].astype(int).values.tolist()
            if len(dser) < st.session_state.params["days"]:
                st.warning(f"Uploaded demand has {len(dser)} rows, but days={st.session_state.params['days']}. "
                           "Remaining days will be filled by repeating last value.")
                last = dser[-1] if len(dser) > 0 else 0
                dser = dser + [last] * (st.session_state.params["days"] - len(dser))
            elif len(dser) > st.session_state.params["days"]:
                st.info(f"Truncating uploaded demand from {len(dser)} to days={st.session_state.params['days']}.")
                dser = dser[:st.session_state.params["days"]]
            set_demand_from_series(dser)
    except Exception as e:
        st.error(f"Failed to parse CSV: {e}")
else:
    ensure_demand()

days = st.session_state.params["days"]
product_cost = st.session_state.params["product_cost"]
holding_rate = st.session_state.params["holding_rate"]
shortage_cost = st.session_state.params["shortage_cost"]
hcost_day = holding_cost_per_day(product_cost, holding_rate)

# ---------------- Main UI ----------------
st.title("📦 Single-Item Inventory Game")
st.caption("Each day, decide how much to order before demand is revealed. Holding cost is 20%/year of unit cost by default; shortage cost is per unit of lost sales.")

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
        inv_end = inv_before_sales - sales  # if no backorders, this equals max(inv_before_sales - demand, 0)

        purchase_cost = order_qty * product_cost
        holding_cost = inv_end * hcost_day
        shortage_penalty = shortage_units * shortage_cost
        day_cost = purchase_cost + holding_cost + shortage_penalty

        st.success(f"Demand today: {today_demand} | Sold: {sales} | Shortage: {shortage_units} | End Inv: {inv_end}")
        st.info(f"Costs → Purchase ₹{purchase_cost:.2f} + Holding ₹{holding_cost:.2f} + Shortage ₹{shortage_penalty:.2f} = **₹{day_cost:.2f}**")

        # Save record
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

        # Move to next day
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

    # Totals
    total_cost = float(df["day_cost"].sum())
    left, right = st.columns(2)
    with left:
        st.metric("Total Cost (₹)", value=round(total_cost, 2))
    with right:
        st.download_button("⬇️ Download Results (CSV)", data=df.to_csv(index=False).encode("utf-8"), file_name="results.csv", mime="text/csv")

else:
    st.info("Place your first order to begin. Upload a demand CSV in the sidebar or use the random generator.")
