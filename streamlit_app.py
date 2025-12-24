import streamlit as st
import pandas as pd
from pathlib import Path


# ---------- Data loading ----------

@st.cache_data
def load_data() -> pd.DataFrame:
    csv_path = Path(__file__).parent / "SYNTHETIC Markdown Dataset.csv"
    df = pd.read_csv(csv_path)
    return df


# ---------- Helper functions ----------

def compute_stage_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute revenue and sell-through for each markdown stage."""
    records = []
    for _, row in df.iterrows():
        stock = row["Stock_Level"]
        for stage, md_col, sales_col in [
            ("M1", "Markdown_1", "Sales_After_M1"),
            ("M2", "Markdown_2", "Sales_After_M2"),
            ("M3", "Markdown_3", "Sales_After_M3"),
            ("M4", "Markdown_4", "Sales_After_M4"),
        ]:
            markdown = row[md_col]
            sales = row[sales_col]
            price_after = row["Original_Price"] * (1 - markdown)
            revenue = price_after * sales
            sell_through = sales / stock if stock > 0 else 0.0

            records.append({
                "Category": row["Category"],
                "Season": row["Season"],
                "Product_Name": row["Product_Name"],
                "Brand": row["Brand"],
                "Stage": stage,
                "Markdown": markdown,
                "Sales": sales,
                "Revenue": revenue,
                "Sell_through": sell_through,
            })
    return pd.DataFrame(records)


# ---------- App ----------

def main():
    st.set_page_config(
        page_title="Retail Markdown Optimization Assistant",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🛒 Retail Markdown Optimization Assistant")
    st.caption(
        "Understand markdown effectiveness by **category** and **season**, "
        "then drill down to **individual products by name**."
    )

    df = load_data()
    metrics_long = compute_stage_metrics(df)

    # ---------- Global sidebar filters ----------
    st.sidebar.header("🔍 Global Filters")
    
    category_options = sorted(df["Category"].unique().tolist())
    season_options = sorted(df["Season"].unique().tolist())
    
    selected_categories = st.sidebar.multiselect(
        "Category", options=category_options, default=category_options
    )
    selected_seasons = st.sidebar.multiselect(
        "Season", options=season_options, default=season_options
    )

    filtered_df = df[
        df["Category"].isin(selected_categories) & 
        df["Season"].isin(selected_seasons)
    ].copy()
    filtered_long = metrics_long[
        (metrics_long["Category"].isin(selected_categories)) &
        (metrics_long["Season"].isin(selected_seasons))
    ].copy()

    # ---------- Tabs ----------
    tab1, tab2 = st.tabs(["📊 Category/Season Dashboard", "🔍 Product Drill-down"])

    # -------------------------------------------------------------------------
    # TAB 1: Category / Season Dashboard
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("Category × Season Performance Overview")

        if filtered_long.empty:
            st.info("No data matches the selected filters.")
        else:
            # Revenue by Category and Stage (pivot table)
            st.markdown("### 💰 Revenue by markdown stage (per category)")
            rev_by_cat_stage = (
                filtered_long.groupby(["Category", "Stage"], as_index=False)["Revenue"]
                .sum()
            )
            rev_pivot = rev_by_cat_stage.pivot(
                index="Category", columns="Stage", values="Revenue"
            ).fillna(0).round(0).astype(int)
            st.dataframe(rev_pivot.style.format("{:,}"))

            # Interactive chart
            st.markdown("#### 📈 Revenue progression by category")
            chart_cats = st.multiselect(
                "Categories to chart", options=category_options,
                default=selected_categories[:min(3, len(selected_categories))]
            )
            if chart_cats:
                chart_data = filtered_long[
                    filtered_long["Category"].isin(chart_cats)
                ].groupby(["Category", "Stage"])["Revenue"].sum().reset_index()
                chart_pivot = chart_data.pivot(
                    index="Stage", columns="Category", values="Revenue"
                ).fillna(0)
                st.bar_chart(chart_pivot)
            
            st.markdown("---")
            
            # Season vs Category heatmap
            st.markdown("### 🌡️ Season × Category: Total Revenue (all stages)")
            heat_data = (
                filtered_long.groupby(["Category", "Season"])["Revenue"]
                .sum().reset_index()
            )
            heat_pivot = heat_data.pivot(
                index="Category", columns="Season", values="Revenue"
            ).fillna(0).round(0).astype(int)
            st.dataframe(heat_pivot.style.format("{:,}"))

            st.markdown("### 💡 Key Insights")
            st.write("✅ **Revenue grows from M1→M4** = Category responds well to deeper markdowns")
            st.write("✅ **High Winter/Summer revenue** = Seasonal opportunity for markdowns")
            st.write("✅ **Compare M4 vs M1 revenue gap** across categories to prioritize")

    # -------------------------------------------------------------------------
    # TAB 2: Product Drill-down (BY NAME, not ID)
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("Product Drill-down")
        
        if filtered_df.empty:
            st.info("No products match the global filters.")
        else:
            # Additional product filters
            st.markdown("#### 🔧 Product filters")
            prod_cat = st.selectbox(
                "Category", options=["All"] + sorted(filtered_df["Category"].unique().tolist())
            )
            prod_brand = st.selectbox(
                "Brand", options=["All"] + sorted(filtered_df["Brand"].unique().tolist())
            )

            prod_subset = filtered_df.copy()
            if prod_cat != "All":
                prod_subset = prod_subset[prod_subset["Category"] == prod_cat]
            if prod_brand != "All":
                prod_subset = prod_subset[prod_subset["Brand"] == prod_brand]

            # Create user-friendly product labels: "Name | Brand | Season"
            prod_subset = prod_subset.copy()
            prod_subset["product_label"] = (
                prod_subset["Product_Name"].str[:30] + "..." 
                if len(prod_subset["Product_Name"].iloc[0]) > 30 else prod_subset["Product_Name"]
            ) + " | " + prod_subset["Brand"] + " | " + prod_subset["Season"]

            product_labels = sorted(prod_subset["product_label"].unique().tolist())
            
            if product_labels:
                selected_label = st.selectbox(
                    "Select product", options=product_labels, 
                    format_func=lambda x: x[:60] + "..." if len(x) > 60 else x
                )
                
                # Get the actual row
                row = prod_subset[
                    prod_subset["product_label"] == selected_label
                ].iloc[0]

                # -------- Product info (horizontal) --------
                st.markdown("### 📋 Product Details")
                c1, c2, c3, c4 = st.columns(4)
                
                with c1:
                    st.metric("Product", row['Product_Name'])
                    st.write(f"**Category**: {row['Category']}")
                    st.write(f"**Brand**: {row['Brand']}")
                
                with c2:
                    st.metric("Original Price", f"${row['Original_Price']:.2f}")
                    st.metric("Competitor Price", f"${row['Competitor_Price']:.2f}")
                
                with c3:
                    st.metric("Stock", f"{int(row['Stock_Level']):,}")
                    st.metric("Rating", f"{row['Customer Ratings']:.1f}/5")
                
                with c4:
                    st.metric("Optimal Discount", f"{row['Optimal Discount']:.1%}")
                    st.write(f"**Season**: {row['Season']}")

                st.markdown("---")

                # -------- Markdown stages table --------
                prod_metrics = filtered_long[
                    filtered_long["Product_Name"] == row["Product_Name"]
                ][["Stage", "Markdown", "Sales", "Revenue", "Sell_through"]].copy()
                
                prod_metrics = prod_metrics.sort_values("Stage").reset_index(drop=True)
                prod_metrics["Markdown %"] = (prod_metrics["Markdown"] * 100).round(1)
                prod_metrics["Revenue $"] = prod_metrics["Revenue"].round(0).astype(int)

                st.markdown("### 📊 Markdown Performance by Stage")
                st.dataframe(
                    prod_metrics[["Stage", "Markdown %", "Sales", "Revenue $", "Sell_through"]],
                    use_container_width=True
                )

                # -------- Charts --------
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 💰 Revenue by Stage")
                    chart_rev = prod_metrics.set_index("Stage")[["Revenue $"]]
                    st.bar_chart(chart_rev)
                
                with col2:
                    st.markdown("#### 📈 Sales by Stage")
                    chart_sales = prod_metrics.set_index("Stage")[["Sales"]]
                    st.bar_chart(chart_sales)

                # -------- Best stages --------
                best_rev_stage = prod_metrics.loc[prod_metrics["Revenue"].idxmax(), "Stage"]
                best_sell_stage = prod_metrics.loc[prod_metrics["Sell_through"].idxmax(), "Stage"]

                st.markdown("### 🎯 Recommendations")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.success(f"**Best Revenue**: {best_rev_stage}")
                with c2:
                    st.success(f"**Best Sell-through**: {best_sell_stage}")
                with c3:
                    st.info(f"**Optimal (label)**: {row['Optimal Discount']:.1%}")

                st.markdown("---")
                
                st.markdown("### 💡 Business Interpretation")
                if best_rev_stage == best_sell_stage == "M4":
                    st.success(
                        "✅ **Aggressive markdown recommended**. This product shows strong "
                        "response to deep discounts (M4 maximizes both revenue and stock clearance)."
                    )
                elif best_rev_stage == "M4":
                    st.warning(
                        "⚠️ **Deep markdown for revenue**. M4 gives highest revenue but "
                        "check if sell-through goal is met at earlier stage."
                    )
                else:
                    st.info(
                        "ℹ️ **Conservative approach works**. Revenue peaks at moderate "
                        "markdown level; deeper discounts may erode margin unnecessarily."
                    )
            else:
                st.info("No products match the product filters.")

if __name__ == "__main__":
    main()
