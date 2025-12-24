import streamlit as st
import pandas as pd
from pathlib import Path


# ---------- Data loading ----------

@st.cache_data
def load_data() -> pd.DataFrame:
    # CSV is in the same folder as this script
    csv_path = Path(__file__).parent / "SYNTHETIC Markdown Dataset.csv"
    df = pd.read_csv(csv_path)
    return df


# ---------- App ----------

def main():
    st.set_page_config(
        page_title="Retail Markdown Optimization Assistant",
        layout="wide",
    )

    st.title("Retail Markdown Optimization Assistant")
    st.caption(
        "Per-product view of markdown paths: understand how different markdown "
        "levels impact sales, revenue, and stock clearance using the synthetic "
        "retail markdown dataset."
    )

    df = load_data()

    # --- Sidebar filters ---

    st.sidebar.header("Filters")

    category_options = ["All"] + sorted(df["Category"].unique().tolist())
    season_options = ["All"] + sorted(df["Season"].unique().tolist())

    selected_category = st.sidebar.selectbox("Category", options=category_options)
    selected_season = st.sidebar.selectbox("Season", options=season_options)

    filtered_df = df.copy()
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["Category"] == selected_category]
    if selected_season != "All":
        filtered_df = filtered_df[filtered_df["Season"] == selected_season]

    # --- Single-product markdown analysis ---

    st.subheader("Single Product Markdown Analysis")

    product_ids = filtered_df["Product_ID"].unique().tolist()
    if len(product_ids) == 0:
        st.info("No products available for the selected filters.")
        return

    selected_pid = st.selectbox("Select Product_ID", options=product_ids)
    row = filtered_df[filtered_df["Product_ID"] == selected_pid].iloc[0]

    # -------- Product info in horizontal layout --------
    st.markdown("### Product info")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.write(f"**Name**: {row['Product_Name']}")
        st.write(f"**Category**: {row['Category']}")
        st.write(f"**Brand**: {row['Brand']}")
        st.write(f"**Season**: {row['Season']}")

    with c2:
        st.write(f"**Original price**: {row['Original_Price']:.2f}")
        st.write(f"**Competitor price**: {row['Competitor_Price']:.2f}")
        st.write(f"**Seasonality factor**: {row['Seasonality_Factor']:.2f}")

    with c3:
        st.write(f"**Stock level**: {int(row['Stock_Level'])}")
        st.write(f"**Customer rating**: {row['Customer Ratings']:.1f}")
        st.write(f"**Return rate**: {row['Return Rate']:.2f}")

    with c4:
        st.write(f"**Optimal discount (label)**: {row['Optimal Discount']:.2f}")
        st.write(f"**Promotion type**: {row['Promotion_Type']}")

    st.markdown("---")

    # -------- Markdown stages table + KPIs --------

    markdown_levels = [
        row["Markdown_1"],
        row["Markdown_2"],
        row["Markdown_3"],
        row["Markdown_4"],
    ]
    sales_levels = [
        row["Sales_After_M1"],
        row["Sales_After_M2"],
        row["Sales_After_M3"],
        row["Sales_After_M4"],
    ]

    md_sales_df = pd.DataFrame(
        {
            "Stage": ["M1", "M2", "M3", "M4"],
            "Markdown": markdown_levels,
            "Sales": sales_levels,
        }
    )

    # approximate price after discount and revenue
    md_sales_df["Price_after_discount"] = (
        row["Original_Price"] * (1 - md_sales_df["Markdown"])
    )
    md_sales_df["Revenue"] = (
        md_sales_df["Price_after_discount"] * md_sales_df["Sales"]
    )
    md_sales_df["Sell_through"] = md_sales_df["Sales"] / row["Stock_Level"]

    # identify best stages
    best_rev_stage = md_sales_df.loc[md_sales_df["Revenue"].idxmax(), "Stage"]
    best_sell_stage = md_sales_df.loc[md_sales_df["Sell_through"].idxmax(), "Stage"]

    st.markdown("### Markdown performance by stage")
    st.dataframe(md_sales_df[["Stage", "Markdown", "Sales", "Revenue", "Sell_through"]])

    # -------- More insightful chart: sales + revenue per stage --------

    st.markdown("### Sales and revenue by markdown stage")

    chart_df = md_sales_df.set_index("Stage")[["Sales", "Revenue"]]
    st.bar_chart(chart_df)

    # -------- Textual interpretation --------

    st.markdown("### Interpretation")
    st.write(
        f"- **Best revenue stage** for this product: **{best_rev_stage}**, "
        "the markdown level where total revenue is highest across M1–M4."
    )
    st.write(
        f"- **Best sell-through stage** (stock clearance): **{best_sell_stage}**, "
        "the markdown level where the fraction of stock sold is highest."
    )
    st.write(
        "If both best stages are M4, it implies that the deepest markdown generates "
        "the most revenue and clears stock fastest for this SKU, so more aggressive "
        "discounting is justified for this product within the tested range."
    )


if __name__ == "__main__":
    main()
