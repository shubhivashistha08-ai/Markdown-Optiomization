import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Retail Markdown Optimization Assistant",
    page_icon="🛍️",
    layout="wide"
)

# --------------------------------------------------
# Load data
# --------------------------------------------------
@st.cache_data
def load_data():
    csv_path = Path(__file__).parent / "src" / "synthetic_markdown_dataset.csv"
    df = pd.read_csv(csv_path)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ Failed to load the dataset: {e}")
    st.stop()

# --------------------------------------------------
# App title
# --------------------------------------------------
st.title("🛍️ Retail Markdown Optimization Assistant")

# --------------------------------------------------
# Problem statement - Collapsible
# --------------------------------------------------
show_info = st.checkbox("ℹ️ Show Problem Statement", value=False)

if show_info:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Business Problem**")
        st.markdown("""
        Retailers often apply discounts without knowing:
        - How deep to markdown
        - Which markdown stage (M1–M4) balances clearance and profit
        - Which products respond best to discounts
        """)

    with col2:
        st.markdown("**This App Helps You Answer:**")
        st.markdown("""
        - Which **categories and seasons** respond best to deeper markdowns  
        - Which **markdown stage** maximizes revenue for each product
        - What is the **optimal discount** to maximize both sales and profit
        """)

st.divider()

# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("🔍 Filters")

categories = sorted(df["Category"].unique())
seasons = sorted(df["Season"].unique())
brands = sorted(df["Brand"].unique())

selected_categories = st.sidebar.multiselect(
    "Category",
    categories,
    default=categories
)

selected_seasons = st.sidebar.multiselect(
    "Season",
    seasons,
    default=seasons
)

selected_brands = st.sidebar.multiselect(
    "Brand",
    brands,
    default=brands[:3] if len(brands) > 3 else brands
)

# Filter data
filtered_df = df[
    df["Category"].isin(selected_categories) &
    df["Season"].isin(selected_seasons) &
    df["Brand"].isin(selected_brands)
].copy()

if len(filtered_df) == 0:
    st.warning("⚠️ No data matches the selected filters. Please adjust your filters.")
    st.stop()

# --------------------------------------------------
# Reshape data for markdown analysis
# --------------------------------------------------
markdown_data = []
for _, row in filtered_df.iterrows():
    for i in range(1, 5):
        markdown_col = f"Markdown_{i}"
        sales_col = f"Sales_After_M{i}"
        
        if markdown_col in row and sales_col in row:
            revenue = row["Original_Price"] * (1 - row[markdown_col]) * row[sales_col]
            markdown_data.append({
                "Product_ID": row["Product_ID"],
                "Category": row["Category"],
                "Season": row["Season"],
                "Brand": row["Brand"],
                "Stage": f"M{i}",
                "Markdown": row[markdown_col],
                "Sales": row[sales_col],
                "Revenue": revenue,
                "Original_Price": row["Original_Price"]
            })

markdown_df = pd.DataFrame(markdown_data)

# --------------------------------------------------
# KPIs
# --------------------------------------------------
st.subheader("📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

# Find best markdown stage per product
best_per_product = markdown_df.loc[markdown_df.groupby("Product_ID")["Revenue"].idxmax()]

with col1:
    total_revenue = best_per_product["Revenue"].sum()
    st.metric("💰 Max Potential Revenue", f"${total_revenue:,.0f}")

with col2:
    avg_optimal_discount = best_per_product["Markdown"].mean() * 100
    st.metric("🎯 Avg Optimal Discount", f"{avg_optimal_discount:.1f}%")

with col3:
    products_analyzed = len(best_per_product)
    st.metric("📦 Products Analyzed", f"{products_analyzed:,}")

with col4:
    historical_sales = filtered_df["Historical_Sales"].mean()
    optimal_sales = best_per_product["Sales"].mean()
    sales_lift = ((optimal_sales / historical_sales) - 1) * 100
    st.metric("📈 Avg Sales Lift", f"+{sales_lift:.1f}%")

st.divider()

# --------------------------------------------------
# Revenue by Markdown Stage
# --------------------------------------------------
st.subheader("💵 Revenue by Markdown Stage")

col1, col2 = st.columns([2, 1])

with col1:
    revenue_by_stage = markdown_df.groupby(["Stage", "Category"])["Revenue"].sum().reset_index()
    
    fig = px.bar(
        revenue_by_stage,
        x="Stage",
        y="Revenue",
        color="Category",
        title="Revenue Performance Across Markdown Stages",
        barmode="group",
        color_discrete_sequence=["#FF6B6B", "#4ECDC4", "#45B7D1"],
        text_auto='.2s'
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Find best stage overall
    stage_totals = markdown_df.groupby("Stage")["Revenue"].sum()
    best_stage = stage_totals.idxmax()
    
    # Create styled box with same height as chart
    st.markdown(f"""
    <div style="background-color: #1e1e1e; 
                padding: 20px; 
                border-radius: 10px; 
                height: 360px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                border: 1px solid #333;">
        <h3 style="color: white; margin-bottom: 20px;">📊 Key Insights</h3>
        <ul style="color: white; font-size: 16px; line-height: 2;">
            <li><strong>Best Overall Stage:</strong> {best_stage}</li>
            <li><strong>Total Revenue:</strong> ${stage_totals[best_stage]:,.0f}</li>
        </ul>
        <p style="color: #cccccc; margin-top: 20px; font-size: 14px;">
            The optimal markdown stage varies by category and product. Use the chart to identify patterns.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --------------------------------------------------
# Category Performance
# --------------------------------------------------
st.subheader("🏆 Category Performance Analysis")

col1, col2 = st.columns(2)

with col1:
    category_revenue = best_per_product.groupby("Category")["Revenue"].sum().reset_index()
    category_revenue = category_revenue.sort_values("Revenue", ascending=False)
    
    # Create pie chart for revenue distribution
    fig = px.pie(
        category_revenue,
        values="Revenue",
        names="Category",
        title="Revenue Distribution by Category (at Optimal Markdown)",
        color_discrete_sequence=["#FF6B6B", "#4ECDC4", "#45B7D1"],
        hole=0.4
    )
    fig.update_traces(textposition='outside', textinfo='percent+label+value', 
                      texttemplate='%{label}<br>%{percent:.1%}<br>$%{value:.2s}')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    category_discount = best_per_product.groupby("Category")["Markdown"].mean().reset_index()
    category_discount["Markdown"] = category_discount["Markdown"] * 100
    category_discount = category_discount.sort_values("Markdown", ascending=False)
    
    fig = px.bar(
        category_discount,
        x="Category",
        y="Markdown",
        title="Average Optimal Discount by Category",
        color="Markdown",
        color_continuous_scale=["#00D9FF", "#FFB800", "#FF6B6B"],
        text_auto='.1f'
    )
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    fig.update_layout(height=400, yaxis_title="Discount (%)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------------------------
# Seasonal Analysis
# --------------------------------------------------
st.subheader("🌤️ Seasonal Markdown Performance")

season_stage = markdown_df.groupby(["Season", "Stage"])["Revenue"].sum().reset_index()

fig = px.line(
    season_stage,
    x="Stage",
    y="Revenue",
    color="Season",
    markers=True,
    title="Revenue by Season Across Markdown Stages",
    color_discrete_sequence=["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFB800"],
    text="Revenue"
)
fig.update_traces(texttemplate='$%{text:.2s}', textposition='top center')
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------------------------
# Best Markdown Stage per Product
# --------------------------------------------------
st.subheader("🎯 Optimal Markdown Strategy per Product")

# Show top products with their optimal strategy
top_products = best_per_product.nlargest(20, "Revenue")[
    ["Product_ID", "Category", "Season", "Brand", "Stage", "Markdown", "Revenue"]
].copy()

top_products["Markdown %"] = (top_products["Markdown"] * 100).round(1)
top_products["Revenue"] = top_products["Revenue"].round(0)

st.dataframe(
    top_products[["Product_ID", "Category", "Season", "Brand", "Stage", "Markdown %", "Revenue"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Revenue": st.column_config.NumberColumn(
            "Revenue",
            format="$%.0f"
        ),
        "Markdown %": st.column_config.NumberColumn(
            "Optimal Discount",
            format="%.1f%%"
        )
    }
)

# Download option
csv = best_per_product.to_csv(index=False)
st.download_button(
    label="📥 Download Full Analysis (CSV)",
    data=csv,
    file_name="optimal_markdown_strategy.csv",
    mime="text/csv"
)

st.divider()

# --------------------------------------------------
# Markdown vs Revenue Scatter
# --------------------------------------------------
st.subheader("📉 Markdown Depth vs Revenue Relationship")

fig = px.scatter(
    markdown_df,
    x="Markdown",
    y="Revenue",
    color="Category",
    size="Sales",
    hover_data=["Product_ID", "Stage"],
    title="Relationship between Discount Depth and Revenue",
    labels={"Markdown": "Discount Level", "Revenue": "Revenue Generated"},
    color_discrete_sequence=["#FF6B6B", "#4ECDC4", "#45B7D1"]
)
# Format x-axis as percentage without using tickformat
fig.update_layout(
    height=400,
    xaxis=dict(
        tickformat='.0%'
    )
)
st.plotly_chart(fig, use_container_width=True)

st.caption("💡 Each point represents a product at a specific markdown stage. Larger bubbles indicate higher sales volume.")

st.divider()

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.caption("Built with Streamlit • Retail Markdown Optimization Assistant")
st.caption(f"📊 Analyzing {len(filtered_df)} products across {len(selected_categories)} categories")
