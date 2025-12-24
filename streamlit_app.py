import streamlit as st
import pandas as pd
from pathlib import Path

# ---------- Data loading ----------

@st.cache_data
def load_data() -> pd.DataFrame:
    # CSV is in the same folder as this script:
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
        "Explore markdowns, sales after markdown, and the synthetic optimal discount "
        "from the Kaggle retail markdown dataset."
    )

    # Load data
    df = load_data()

    # Sidebar filters
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

    # Dataset preview
    st.subheader("Dataset preview (after filters)")
    st.dataframe(filtered_df.head(20))

    # Basic stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows (filtered)", len(filtered_df))
    with col2:
        st.metric("Unique products", filtered_df["Product_ID"].nunique())
    with col3:
        st.metric("Avg optimal discount", round(filtered_df["Optimal Discount"].mean(), 3))

    st.markdown("---")

    # Markdown vs sales visualization
    st.subheader("Markdown vs Sales After Markdown (M1)")

    if not filtered_df.empty:
        chart_df = filtered_df[["Markdown_1", "Sales_After_M1"]].rename(
            columns={"Markdown_1": "Markdown", "Sales_After_M1": "Sales"}
        )
        st.scatter_chart(chart_df)
    else:
        st.info("No data for selected filters.")

    st.markdown("---")

    # Single-product explorer
    st.subheader("Single Product Markdown Path")

    product_ids = filtered_df["Product_ID"].unique().tolist()
    if len(product_ids) > 0:
        selected_pid = st.selectbox("Select Product_ID", options=product_ids)
        row = filtered_df[filtered_df["Product_ID"] == selected_pid].iloc[0]

        st.write("### Product info")
        st.write(
            f"- **Name**: {row['Product_Name']}\n"
            f"- **Category**: {row['Category']}\n"
            f"- **Brand**: {row['Brand']}\n"
            f"- **Season**: {row['Season']}\n"
            f"- **Original price**: {row['Original_Price']}\n"
            f"- **Competitor price**: {row['Competitor_Price']}\n"
            f"- **Stock level**: {row['Stock_Level']}\n"
            f"- **Customer rating**: {row['Customer Ratings']}\n"
            f"- **Return rate**: {row['Return Rate']}\n"
            f"- **Optimal discount (label)**: {row['Optimal Discount']}"
        )

        # Markdown levels and sales
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
                "Markdown": markdown_levels,
                "Sales": sales_levels,
                "Stage": ["M1", "M2", "M3", "M4"],
            }
        )

        st.write("#### Sales after each markdown level")
        st.dataframe(md_sales_df)

        # Approx revenue per stage
        md_sales_df["Price_after_discount"] = (
            row["Original_Price"] * (1 - md_sales_df["Markdown"])
        )
        md_sales_df["Revenue"] = (
            md_sales_df["Price_after_discount"] * md_sales_df["Sales"]
        )

        st.write("#### Revenue by markdown stage (approx.)")
        st.dataframe(md_sales_df[["Stage", "Markdown", "Sales", "Revenue"]])

        st.write("#### Markdown vs Sales chart (for this product)")
        st.line_chart(md_sales_df.set_index("Markdown")[["Sales"]])
    else:
        st.info("No products available for the selected filters.")


if __name__ == "__main__":
    main()
