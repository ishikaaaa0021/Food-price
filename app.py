import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import seaborn as sns

# Set page configuration
st.set_page_config(
    page_title="Food Price Analysis Dashboard",
    page_icon="🍔",
    layout="wide"
)

# Title and description
st.title("🍔 Food Price Analysis Dashboard")
st.markdown("Analyze food price trends, compare items, and track inflation rates")

# Sidebar for navigation and controls
st.sidebar.header("Controls")

# Function to load data (you can replace this with your data source)
@st.cache_data
def load_data():
    # Creating sample data (replace with your actual data source)
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    
    food_items = ['Rice', 'Wheat', 'Milk', 'Eggs', 'Chicken', 'Fish', 
                  'Vegetables', 'Fruits', 'Bread', 'Cheese']
    
    data = []
    for date in dates:
        for item in food_items:
            # Generate realistic price data with trends and seasonality
            base_price = {
                'Rice': 50, 'Wheat': 40, 'Milk': 60, 'Eggs': 5, 'Chicken': 200,
                'Fish': 300, 'Vegetables': 80, 'Fruits': 120, 'Bread': 35, 'Cheese': 400
            }[item]
            
            # Add trend (inflation)
            days_since_start = (date - dates[0]).days
            trend = 1 + (days_since_start / 730) * 0.1  # 10% annual inflation
            
            # Add seasonality
            seasonal = 1 + 0.1 * np.sin(2 * np.pi * date.month / 12)
            
            # Add random noise
            noise = np.random.normal(1, 0.05)
            
            price = base_price * trend * seasonal * noise
            
            data.append({
                'Date': date,
                'Item': item,
                'Category': 'Staple' if item in ['Rice', 'Wheat', 'Bread'] else
                           'Dairy' if item in ['Milk', 'Cheese'] else
                           'Protein' if item in ['Eggs', 'Chicken', 'Fish'] else
                           'Produce',
                'Price': round(price, 2)
            })
    
    return pd.DataFrame(data)

# Load data
with st.spinner("Loading data..."):
    df = load_data()

# Sidebar filters
st.sidebar.subheader("Filters")

# Date range filter
min_date = df['Date'].min()
max_date = df['Date'].max()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Category filter
categories = ['All'] + list(df['Category'].unique())
selected_category = st.sidebar.selectbox("Select Category", categories)

# Item filter
if selected_category != 'All':
    available_items = df[df['Category'] == selected_category]['Item'].unique()
else:
    available_items = df['Item'].unique()

selected_items = st.sidebar.multiselect(
    "Select Items",
    options=available_items,
    default=available_items[:3] if len(available_items) > 2 else available_items
)

# Apply filters
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df['Date'] >= pd.Timestamp(start_date)) & (df['Date'] <= pd.Timestamp(end_date))
    filtered_df = df.loc[mask]
else:
    filtered_df = df.copy()

if selected_category != 'All':
    filtered_df = filtered_df[filtered_df['Category'] == selected_category]

if selected_items:
    filtered_df = filtered_df[filtered_df['Item'].isin(selected_items)]

# Main content area with tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Price Trends", "📊 Statistics", "💰 Inflation Analysis", "📦 Category Analysis"])

# Tab 1: Price Trends
with tab1:
    st.header("Price Trends Over Time")
    
    if not filtered_df.empty:
        # Create line chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for item in filtered_df['Item'].unique():
            item_data = filtered_df[filtered_df['Item'] == item]
            # Resample to weekly averages for cleaner visualization
            weekly_data = item_data.set_index('Date').resample('W')['Price'].mean()
            ax.plot(weekly_data.index, weekly_data.values, label=item, linewidth=2)
        
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price (INR)', fontsize=12)
        ax.set_title('Food Price Trends', fontsize=14, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Show data table
        st.subheader("Raw Data")
        st.dataframe(filtered_df.sort_values('Date'), use_container_width=True)
    else:
        st.warning("No data available for selected filters")

# Tab 2: Statistics
with tab2:
    st.header("Price Statistics")
    
    if not filtered_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate statistics
        stats_df = filtered_df.groupby('Item')['Price'].agg(['mean', 'std', 'min', 'max']).round(2)
        stats_df.columns = ['Mean Price', 'Std Dev', 'Min Price', 'Max Price']
        
        with col1:
            st.metric("Average Price", f"₹{filtered_df['Price'].mean():.2f}")
        
        with col2:
            st.metric("Price Range", f"₹{filtered_df['Price'].min():.2f} - ₹{filtered_df['Price'].max():.2f}")
        
        with col3:
            st.metric("Most Expensive Item", filtered_df.loc[filtered_df['Price'].idxmax(), 'Item'])
        
        with col4:
            st.metric("Cheapest Item", filtered_df.loc[filtered_df['Price'].idxmin(), 'Item'])
        
        # Display statistics table
        st.subheader("Detailed Statistics by Item")
        st.dataframe(stats_df, use_container_width=True)
        
        # Box plot for price distribution
        st.subheader("Price Distribution")
        fig, ax = plt.subplots(figsize=(12, 6))
        
        items_data = [filtered_df[filtered_df['Item'] == item]['Price'].values for item in filtered_df['Item'].unique()]
        ax.boxplot(items_data, labels=filtered_df['Item'].unique(), patch_artist=True)
        
        ax.set_xlabel('Food Item', fontsize=12)
        ax.set_ylabel('Price (INR)', fontsize=12)
        ax.set_title('Price Distribution by Item', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        st.pyplot(fig)

# Tab 3: Inflation Analysis
with tab3:
    st.header("Inflation Analysis")
    
    if not filtered_df.empty:
        # Calculate monthly average prices
        filtered_df['Year-Month'] = filtered_df['Date'].dt.to_period('M')
        monthly_avg = filtered_df.groupby(['Year-Month', 'Item'])['Price'].mean().reset_index()
        
        # Calculate month-over-month inflation for each item
        inflation_data = []
        
        for item in monthly_avg['Item'].unique():
            item_data = monthly_avg[monthly_avg['Item'] == item].sort_values('Year-Month')
            item_data['Price Change'] = item_data['Price'].pct_change() * 100
            item_data['Price Change'] = item_data['Price Change'].round(2)
            inflation_data.append(item_data)
        
        inflation_df = pd.concat(inflation_data, ignore_index=True)
        inflation_df = inflation_df.dropna()
        
        # Display inflation chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for item in inflation_df['Item'].unique():
            item_data = inflation_df[inflation_df['Item'] == item]
            ax.plot(item_data['Year-Month'].astype(str), item_data['Price Change'], 
                   label=item, marker='o', markersize=4)
        
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Month-over-Month Price Change (%)', fontsize=12)
        ax.set_title('Monthly Inflation Rate by Item', fontsize=14, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Overall inflation rate
        total_inflation = inflation_df['Price Change'].mean()
        st.metric("Average Monthly Inflation Rate", f"{total_inflation:.2f}%")
        
        # Items with highest inflation
        st.subheader("Items with Highest Inflation")
        top_inflation = inflation_df.groupby('Item')['Price Change'].mean().sort_values(ascending=False).head(5)
        st.bar_chart(top_inflation)

# Tab 4: Category Analysis
with tab4:
    st.header("Category-wise Analysis")
    
    if not filtered_df.empty:
        # Category statistics
        category_stats = filtered_df.groupby('Category').agg({
            'Price': ['mean', 'std', 'min', 'max'],
            'Item': 'nunique'
        }).round(2)
        
        category_stats.columns = ['Avg Price', 'Price Std', 'Min Price', 'Max Price', 'Number of Items']
        
        st.subheader("Category Statistics")
        st.dataframe(category_stats, use_container_width=True)
        
        # Bar chart of average prices by category
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Average prices by category
        avg_by_category = filtered_df.groupby('Category')['Price'].mean().sort_values()
        colors = plt.cm.viridis(np.linspace(0, 1, len(avg_by_category)))
        ax1.barh(avg_by_category.index, avg_by_category.values, color=colors)
        ax1.set_xlabel('Average Price (INR)', fontsize=12)
        ax1.set_title('Average Price by Category', fontsize=14, fontweight='bold')
        
        # Price distribution by category
        for i, category in enumerate(filtered_df['Category'].unique()):
            category_data = filtered_df[filtered_df['Category'] == category]['Price']
            ax2.boxplot(category_data, positions=[i], widths=0.6, patch_artist=True)
        
        ax2.set_xticks(range(len(filtered_df['Category'].unique())))
        ax2.set_xticklabels(filtered_df['Category'].unique(), rotation=45, ha='right')
        ax2.set_ylabel('Price (INR)', fontsize=12)
        ax2.set_title('Price Distribution by Category', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Category price trends over time
        st.subheader("Category Price Trends")
        category_trends = filtered_df.groupby(['Date', 'Category'])['Price'].mean().reset_index()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for category in category_trends['Category'].unique():
            cat_data = category_trends[category_trends['Category'] == category]
            ax.plot(cat_data['Date'], cat_data['Price'], label=category, linewidth=2)
        
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Average Price (INR)', fontsize=12)
        ax.set_title('Category Price Trends Over Time', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)

# Footer with data summary
st.markdown("---")
st.markdown(f"**Data Summary:** {len(filtered_df)} records | {filtered_df['Item'].nunique()} food items | {filtered_df['Category'].nunique()} categories")

# Optional: Download filtered data
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name=f"food_prices_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)
