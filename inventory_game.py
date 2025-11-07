import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
TOTAL_DAYS = 30
PRODUCT_COST = 100
HOLDING_COST_RATE = 0.2
SHORTAGE_COST = 20
HOLDING_COST_PER_DAY = (PRODUCT_COST * HOLDING_COST_RATE) / 365

st.set_page_config(page_title="Inventory Game", layout="centered")

# --- INITIAL SETUP ---
st.title("📦 Multi-Period Inventory Game")

# Initialize session state
if "player" not in st.session_state:
    st.session_state.player = None
if "day" not in st.session_state:
    st.session_state.day = 1
if "inventory" not in st.session_state:
    st.session_state.inventory = 0
if "orders" not in st.session_state:
    st.session_state.orders = []
if "demands" not in st.session_state:
    np.random.seed(42)
    st.session_state.demands = np.random.randint(30, 100, TOTAL_DAYS).tolist()
if "costs" not in st.session_state:
    st.session_state.costs = []

# --- PLAYER NAME ---
if st.session_state.player is None:
    name = st.text_input("Enter your name to start the game:")
    if st.button("Start Game") and name.strip() != "":
        st.session_state.player = name
        st.success(f"Welcome, {name}! Let’s begin Day 1.")
    st.stop()

# --- GAMEPLAY ---
day = st.session_state.day
inventory = st.session_state.inventory
demands = st.session_state.demands

if day <= TOTAL_DAYS:
    st.subheader(f"Day {day} Decision")
    st.write(f"Current inventory: {inventory:.0f} units")

    order_qty = st.number_input("Enter order quantity for today:", min_value=0, step=1)
    if st.button("Submit Order"):
        demand = demands[day - 1]
        new_inventory = inventory + order_qty - demand

        # Calculate cost
        cost = order_qty * PRODUCT_COST
        if new_inventory > 0:
            cost += new_inventory * HOLDING_COST_PER_DAY
        elif new_inventory < 0:
            cost += abs(new_inventory) * SHORTAGE_COST

        st.session_state.orders.append(order_qty)
        st.session_state.inventory = new_inventory
        st.session_state.costs.append(cost)
        st.session_state.day += 1

        st.success(f"Demand was {demand}. End inventory = {new_inventory:.0f}.")
        st.experimental_rerun()
else:
    # --- GAME OVER ---
    st.subheader("✅ Game Over!")
    total_cost = sum(st.session_state.costs)
    st.write(f"**Total cost for 30 days: ₹{total_cost:,.2f}**")

    df = pd.DataFrame({
        "Day": range(1, TOTAL_DAYS + 1),
        "Order": st.session_state.orders,
        "Demand": st.session_state.demands[:len(st.session_state.orders)]
    })
    inv = []
    inv_level = 0
    for o, d in zip(df["Order"], df["Demand"]):
        inv_level += o - d
        inv.append(inv_level)
    df["Inventory"] = inv

    st.line_chart(df.set_index("Day")[["Order", "Demand", "Inventory"]])

    if st.button("Play Again"):
        for k in ["player", "day", "inventory", "orders", "demands", "costs"]:
            del st.session_state[k]
        st.experimental_rerun()
