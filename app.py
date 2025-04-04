import streamlit as st
import pandas as pd
import ast
import plotly.express as px
from io import StringIO

@st.cache_data
def load_data():
    try:
        customers_data = """
Customer_ID,Age,Gender,Location,Browsing_History,Purchase_History,Customer_Segment,Avg_Order_Value,Holiday,Season
C1000,28,Female,Chennai,"['Books', 'Fashion']","['Biography', 'Jeans']",New Visitor,4806.99,No,Winter
C1001,27,Male,Delhi,"['Books', 'Fitness', 'Fashion']","['Biography', 'Resistance Bands', 'T-shirt']",Occasional Shopper,795.03,Yes,Autumn
C1002,34,Other,Chennai,['Electronics'],['Smartphone'],Occasional Shopper,1742.45,Yes,Summer
"""
        customers = pd.read_csv(StringIO(customers_data))

        products_data = """
Product_ID,Category,Subcategory,Price,Brand,Average_Rating_of_Similar_Products,Product_Rating,Customer_Review_Sentiment_Score,Holiday,Season,Geographical_Location,Similar_Product_List,Probability_of_Recommendation
P2000,Fashion,Jeans,1713,Brand B,4.2,2.3,0.26,No,Summer,Canada,"['Jeans', 'Shoes']",0.91
P2001,Beauty,Lipstick,1232,Brand C,4.7,2.1,0.21,Yes,Winter,India,"['Moisturizer', 'Lipstick', 'Lipstick']",0.26
P2002,Electronics,Laptop,4833,Brand B,3.5,2.4,0.74,Yes,Spring,Canada,"['Headphones', 'Headphones', 'Smartphone']",0.6
"""
        products = pd.read_csv(StringIO(products_data))
        customers['Browsing_History'] = customers['Browsing_History'].apply(ast.literal_eval)
        customers['Purchase_History'] = customers['Purchase_History'].apply(ast.literal_eval)
        products['Similar_Product_List'] = products['Similar_Product_List'].apply(ast.literal_eval)

        return customers, products
    except Exception as e:
        st.error(f"🚫 Data loading error: {str(e)}. Using sample data.")
        customers_data = {
            'Customer_ID': ['C1000', 'C1001'],
            'Age': [28, 27],
            'Gender': ['Female', 'Male'],
            'Location': ['Chennai', 'Delhi'],
            'Browsing_History': [['Books', 'Fashion'], ['Books', 'Fitness']],
            'Purchase_History': [['Biography', 'Jeans'], ['Biography', 'Resistance Bands']],
            'Customer_Segment': ['New Visitor', 'Occasional Shopper'],
            'Avg_Order_Value': [4806.99, 795.03],
            'Holiday': ['No', 'Yes'],
            'Season': ['Winter', 'Autumn']
        }
        products_data = {
            'Product_ID': ['P2000', 'P2001'],
            'Category': ['Fashion', 'Beauty'],
            'Subcategory': ['Jeans', 'Lipstick'],
            'Price': [1713, 1232],
            'Brand': ['Brand B', 'Brand C'],
            'Probability_of_Recommendation': [0.91, 0.26],
            'Holiday': ['No', 'Yes'],
            'Season': ['Summer', 'Winter'],
            'Average_Rating_of_Similar_Products': [4.2, 4.7],
            'Customer_Review_Sentiment_Score': [0.26, 0.21]
        }
        return pd.DataFrame(customers_data), pd.DataFrame(products_data)

def recommend_products(customer, products_df, min_price, max_price):
    interests = set(customer['Browsing_History'] + customer['Purchase_History'])
    recommendations = products_df[
        (products_df['Category'].str.lower().isin([i.lower() for i in interests])) |
        (products_df['Subcategory'].isin(customer['Purchase_History'])) &
        (products_df['Price'].between(min_price, max_price))
    ].sort_values('Probability_of_Recommendation', ascending=False)
    
    if len(recommendations) < 3:
        additional = products_df[products_df['Price'].between(min_price, max_price)].sample(min(3 - len(recommendations), len(products_df)))
        recommendations = pd.concat([recommendations, additional])
    return recommendations.head(3)

def get_sentiment_insight(score):
    if score >= 0.7:
        return "Highly Positive Reviews 😊"
    elif score >= 0.4:
        return "Generally Positive Reviews 🙂"
    else:
        return "Mixed or Negative Reviews 😐"

def plot_segment_distribution(customers_df):
    fig = px.pie(customers_df, names='Customer_Segment', title='Customer Segment Distribution',
                 color_discrete_sequence=px.colors.sequential.RdBu)
    return fig

def plot_category_interests(customers_df):
    categories = customers_df['Browsing_History'].explode().value_counts()
    fig = px.bar(x=categories.index, y=categories.values, title='Top Product Categories by Interest',
                 labels={'x': 'Category', 'y': 'Count'}, color=categories.index)
    return fig

def plot_spending_analysis(customers_df):
    fig = px.histogram(customers_df, x='Avg_Order_Value', nbins=20, title='Average Order Value Distribution',
                       color_discrete_sequence=['#00CC96'])
    return fig

def plot_customer_spending(customer, customers_df):
    fig = px.box(customers_df, y='Avg_Order_Value', points="all", title=f"Your Spending vs Others",
                 hover_data=['Customer_ID'])
    fig.add_hline(y=customer['Avg_Order_Value'], line_dash="dash", line_color="red", annotation_text="Your Avg Spending")
    return fig

def main():
    st.set_page_config(page_title="Smart Shopping Hub", page_icon="🛍️", layout="wide", initial_sidebar_state="expanded")

    st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {background-color: #2e86de; color: white; border-radius: 8px; padding: 10px;}
    .product-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin-bottom: 20px;
        border-left: 5px solid #2e86de;
    }
    .sidebar .sidebar-content {
        background-color: #f0f0f5;
        padding: 15px;
        border-radius: 10px;
    }
    .tab {font-size: 18px; font-weight: bold; padding: 10px;}
    .price {color: #16a085; font-weight: bold;}
    .score {color: #2c3e50; font-weight: bold;}
    .holiday {color: #c0392b; font-weight: bold;}
    .rating {color: #d35400; font-weight: bold;}
    .label {color: #2c3e50; font-weight: bold;}
    .insight {color: #8e44ad; font-style: italic;}
    .detail {color: #34495e; font-weight: normal;}
    </style>
    """, unsafe_allow_html=True)

    st.title("🛍️ Smart Shopping Hub")
    st.subheader("Your AI-Powered Shopping Companion")
    st.markdown("Explore personalized recommendations, insights, and more!")

    customers_df, products_df = load_data()

    with st.sidebar:
        st.header("🔍 Filters")
        customer_ids = customers_df['Customer_ID'].tolist()
        selected_id = st.selectbox("Select Customer", customer_ids, key="customer_select")
        location_filter = st.multiselect("Location", customers_df['Location'].unique(), default=customers_df['Location'].unique())
        season_filter = st.multiselect("Season", customers_df['Season'].unique(), default=customers_df['Season'].unique())
        min_price, max_price = st.slider("Price Range ($)", 
                                         int(products_df['Price'].min()), 
                                         int(products_df['Price'].max()), 
                                         (int(products_df['Price'].min()), int(products_df['Price'].max())))
        st.markdown("---")
        st.info("Customize your experience with filters and explore insights!")

    filtered_customers = customers_df[
        (customers_df['Location'].isin(location_filter)) &
        (customers_df['Season'].isin(season_filter))
    ]
    
    selected_customer_df = filtered_customers[filtered_customers['Customer_ID'] == selected_id]
    if selected_customer_df.empty:
        st.warning(f"⚠️ Customer {selected_id} not found in filtered data. Showing unfiltered customer data.")
        selected_customer_df = customers_df[customers_df['Customer_ID'] == selected_id]
        if selected_customer_df.empty:
            st.error(f"🚫 Customer {selected_id} not found in the dataset. Please select a valid customer.")
            return
    selected_customer = selected_customer_df.iloc[0]

    tab1, tab2, tab3 = st.tabs(["Recommendations", "Profile", "Insights"])

    with tab1:
        st.subheader("🎯 Personalized Recommendations")
        recommended = recommend_products(selected_customer, products_df, min_price, max_price)
        for _, product in recommended.iterrows():
            holiday_tag = '<span class="holiday">🎄 Holiday Special</span>' if product['Holiday'] == 'Yes' else ""
            price_diff = product['Price'] - selected_customer['Avg_Order_Value']
            price_comparison = f"{'Above' if price_diff > 0 else 'Below'} your avg spending by <span class='price'>${abs(price_diff):.2f}</span>"
            st.markdown(f"""
            <div class="product-card">
                <h4>🛒 {product['Subcategory']} (ID: {product['Product_ID']}) {holiday_tag}</h4>
                <p><span class="label">Category:</span> {product['Category']}</p>
                <p><span class="label">Price:</span> <span class="price">${product['Price']}</span> ({price_comparison})</p>
                <p><span class="label">Brand:</span> {product['Brand']}</p>
                <p><span class="label">Recommendation Score:</span> <span class="score">{product['Probability_of_Recommendation']:.2f}</span></p>
                <p><span class="label">Avg Rating of Similar Products:</span> <span class="rating">{product['Average_Rating_of_Similar_Products']}/5</span></p>
                <p><span class="label">Sentiment Score:</span> <span class="rating">{product['Customer_Review_Sentiment_Score']:.2f}</span> 
                    <span class="insight">({get_sentiment_insight(product['Customer_Review_Sentiment_Score'])})</span></p>
                <p><span class="label">Season:</span> {product['Season']}</p>
                <p><span class="label">Location:</span> {product['Geographical_Location']}</p>
                <p><span class="label">Similar Products:</span> {', '.join(product['Similar_Product_List'])}</p>
            </div>
            """, unsafe_allow_html=True)
        if st.button("Download Recommendations"):
            csv = recommended.to_csv(index=False)
            st.download_button("Download CSV", csv, "recommendations.csv", "text/csv")

    with tab2:
        st.subheader("👤 Customer Profile")
        with st.expander("View Details", expanded=True):
            st.markdown(f"""
            <p><span class="label">Customer ID:</span> <span class="detail">{selected_customer['Customer_ID']}</span></p>
            <p><span class="label">Age:</span> <span class="detail">{selected_customer['Age']}</span></p>
            <p><span class="label">Gender:</span> <span class="detail">{selected_customer['Gender']}</span></p>
            <p><span class="label">Location:</span> <span class="detail">{selected_customer['Location']}</span></p>
            <p><span class="label">Interests:</span> <span class="detail">{', '.join(selected_customer['Browsing_History'])}</span></p>
            <p><span class="label">Past Purchases:</span> <span class="detail">{', '.join(selected_customer['Purchase_History'])}</span></p>
            <p><span class="label">Segment:</span> <span class="detail">{selected_customer['Customer_Segment']}</span></p>
            <p><span class="label">Avg Order Value:</span> <span class="price">${selected_customer['Avg_Order_Value']:.2f}</span></p>
            <p><span class="label">Holiday Shopper:</span> <span class="detail">{selected_customer['Holiday']}</span></p>
            <p><span class="label">Season:</span> <span class="detail">{selected_customer['Season']}</span></p>
            """, unsafe_allow_html=True)

    with tab3:
        st.subheader("📊 Shopping Insights")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_segment_distribution(filtered_customers), use_container_width=True)
            st.plotly_chart(plot_spending_analysis(filtered_customers), use_container_width=True)
        with col2:
            st.plotly_chart(plot_category_interests(filtered_customers), use_container_width=True)
            st.plotly_chart(plot_customer_spending(selected_customer, customers_df), use_container_width=True)
        st.markdown("""
        **Insight:** Your recommendations are tailored based on your interests, past purchases, and shopping behavior. 
        Check the sentiment scores and ratings to make informed decisions!
        """)

if __name__ == "__main__":
    main()
