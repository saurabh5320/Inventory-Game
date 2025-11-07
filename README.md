# 📦 Inventory Game (Streamlit)

A simple multi-period (30-day default) single-item inventory game where each day the player chooses an **order quantity before demand is revealed**. Costs include:
- Purchase cost (₹100 per unit by default)
- Holding cost: **20% per year of unit cost**, applied daily
- Shortage (lost sales) penalty: ₹20 per unit

No backorders: unmet demand incurs penalty and inventory does not go negative.

## ▶️ Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Then open the URL shown in terminal (e.g., http://localhost:8501).

## ☁️ Deploy Free (Streamlit Community Cloud)
1. Push these files to a **public GitHub repo**.
2. Visit https://share.streamlit.io/ → **New app** → Select your repo & branch.
3. Set **App file** = `app.py` → **Deploy**.
4. Share the generated URL with players (works on phones/tablets/PCs).

## Demand Input
- Upload a CSV with one column named `demand` (length ≥ number of days).
- Or use randomly generated demand (set seed & range in the sidebar).

## Game Notes
- No Google login required; enter the site and start placing orders.
- Graphs show **Orders, Demand, Ending Inventory**, and **Cumulative Cost**.
- Download your results as CSV at any time.
