import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("🍓 Fruit Nutrition Explorer")
st.write("Explore and compare the nutritional content of fruits using the Fruityvice API.")

# ── Fetch data ─────────────────────────────────────────────────────────────────
@st.cache_data
def fetch_all_fruits():
    response = requests.get("https://www.fruityvice.com/api/fruit/all", timeout=10)
    response.raise_for_status()
    data = response.json()

    rows = []
    for fruit in data:
        nutritions = fruit.get("nutritions", {})
        rows.append({
            "Name":          fruit.get("name", "Unknown"),
            "Family":        fruit.get("family", "Unknown"),
            "Calories":      nutritions.get("calories", 0),
            "Fat":           nutritions.get("fat", 0),
            "Sugar":         nutritions.get("sugar", 0),
            "Carbohydrates": nutritions.get("carbohydrates", 0),
            "Protein":       nutritions.get("protein", 0),
        })

    df = pd.DataFrame(rows)
    numeric_cols = ["Calories", "Fat", "Sugar", "Carbohydrates", "Protein"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    return df.sort_values("Name").reset_index(drop=True)

try:
    df = fetch_all_fruits()
except Exception as e:
    st.error(f"Could not fetch data from the Fruityvice API: {e}")
    st.stop()

NUTRIENTS = ["Calories", "Sugar", "Carbohydrates", "Fat", "Protein"]
all_names = sorted(df["Name"].tolist())

# ── Sidebar inputs ─────────────────────────────────────────────────────────────
st.sidebar.header("Filters")

# Input 1 – nutrient to rank by
rank_nutrient = st.sidebar.selectbox("Rank fruits by", NUTRIENTS)

# Input 2 – slider to filter by nutrient range
col_min = float(df[rank_nutrient].min())
col_max = float(df[rank_nutrient].max())
nutrient_range = st.sidebar.slider(
    f"{rank_nutrient} range (per 100g)",
    min_value=col_min,
    max_value=col_max,
    value=(col_min, col_max),
    step=0.1,
)

st.sidebar.markdown("---")

# Input 3 – pick fruits to compare
default_picks = [n for n in ["Banana", "Apple", "Mango", "Strawberry", "Blueberry"] if n in all_names]
selected_fruits = st.sidebar.multiselect("Compare fruits", all_names, default=default_picks)

# Input 4 – pick fruit for pie chart
pie_fruit = st.sidebar.selectbox(
    "Macronutrient breakdown for",
    all_names,
    index=all_names.index("Banana") if "Banana" in all_names else 0
)

# ── Section 1: Rankings bar chart ──────────────────────────────────────────────
st.subheader(f"🏆 Fruit Rankings by {rank_nutrient}")

filtered_df = df[
    (df[rank_nutrient] >= nutrient_range[0]) &
    (df[rank_nutrient] <= nutrient_range[1])
].sort_values(rank_nutrient, ascending=False).reset_index(drop=True)

if filtered_df.empty:
    st.warning("No fruits match the current filter. Try widening the slider.")
else:
    top_n = min(20, len(filtered_df))
    fig_rank = px.bar(
        filtered_df.head(top_n),
        x="Name",
        y=rank_nutrient,
        color=rank_nutrient,
        color_continuous_scale="Greens",
        labels={rank_nutrient: f"{rank_nutrient} (per 100g)", "Name": "Fruit"},
        title=f"Top {top_n} fruits by {rank_nutrient} (filtered)"
    )
    fig_rank.update_layout(xaxis_tickangle=-40, coloraxis_showscale=False)
    st.plotly_chart(fig_rank, use_container_width=True)

    st.write(f"Showing {len(filtered_df)} fruits in the selected range.")
    st.dataframe(filtered_df[["Name", "Family", rank_nutrient]], use_container_width=True)

# ── Section 2: Multi-fruit comparison ─────────────────────────────────────────
st.subheader("🍊 Compare Selected Fruits")

if not selected_fruits:
    st.info("Select fruits in the sidebar to compare them.")
else:
    compare_df = df[df["Name"].isin(selected_fruits)]
    melted = compare_df.melt(id_vars="Name", value_vars=NUTRIENTS,
                              var_name="Nutrient", value_name="Amount")

    fig_compare = px.bar(
        melted,
        x="Nutrient",
        y="Amount",
        color="Name",
        barmode="group",
        labels={"Amount": "Amount (g or kcal)", "Nutrient": "Nutrient"},
        title="Side-by-side nutritional comparison (per 100g)"
    )
    st.plotly_chart(fig_compare, use_container_width=True)

# ── Section 3: Macronutrient pie chart ────────────────────────────────────────
st.subheader(f"🥧 Macronutrient Breakdown — {pie_fruit}")

pie_row = df[df["Name"] == pie_fruit].iloc[0]
macro_labels = ["Carbohydrates", "Fat", "Protein", "Sugar"]
macro_values = [pie_row[m] for m in macro_labels]

if sum(macro_values) == 0:
    st.warning(f"No macronutrient data available for {pie_fruit}.")
else:
    col1, col2 = st.columns([2, 1])

    with col1:
        fig_pie = go.Figure(go.Pie(
            labels=macro_labels,
            values=macro_values,
            hole=0.4,
            textinfo="label+percent",
        ))
        fig_pie.update_layout(title=f"{pie_fruit} macronutrients (per 100g)")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown(f"**{pie_fruit} nutrition facts (per 100g)**")
        st.write(f"- Calories: {pie_row['Calories']} kcal")
        st.write(f"- Carbohydrates: {pie_row['Carbohydrates']} g")
        st.write(f"- Sugar: {pie_row['Sugar']} g")
        st.write(f"- Fat: {pie_row['Fat']} g")
        st.write(f"- Protein: {pie_row['Protein']} g")
        st.write(f"- Family: {pie_row['Family']}")
