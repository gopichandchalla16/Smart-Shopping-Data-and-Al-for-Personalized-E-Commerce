import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import ast
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

# --- Data Loading and Preprocessing ---
@st.cache_data
def load_data():
    customer_df = pd.read_csv("customer_data_collection.csv")
    product_df = pd.read_csv("product_recommendation_data.csv")
    customer_df = customer_df.loc[:, ~customer_df.columns.str.contains('^Unnamed')]
    product_df = product_df.loc[:, ~product_df.columns.str.contains('^Unnamed')]
    return customer_df, product_df

# --- Load Embedding Model ---
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

embedder = load_model()
customer_df, product_df = load_data()

# --- Agents ---
class CustomerAgent:
    def __init__(self, customer_df):
        self.df = customer_df

    def get_profile(self, customer_id):
        try:
            return self.df[self.df['Customer_ID'] == customer_id].iloc[0].to_dict()
        except IndexError:
            return None

class ProductAgent:
    def __init__(self, product_df, embedder):
        self.df = product_df.copy()
        self.df['embedding'] = self.df['Category'] + " " + self.df['Subcategory'] + " " + self.df['Similar_Product_List'].astype(str)
        self.df['vector'] = self.df['embedding'].apply(lambda x: embedder.encode(x))

    def get_top_similar(self, interests, top_n=5):
        interest_text = " ".join(interests)
        interest_vector = embedder.encode([interest_text])[0].reshape(1, -1)
        all_vectors = np.stack(self.df['vector'].values)
        similarities = cosine_similarity(interest_vector, all_vectors)[0]
        top_indices = similarities.argsort()[-top_n:][::-1]
        return self.df.iloc[top_indices]

class RecommenderAgent:
    def __init__(self, customer_agent, product_agent):
        self.customer_agent = customer_agent
        self.product_agent = product_agent

    def recommend(self, customer_id):
        profile = self.customer_agent.get_profile(customer_id)
        if profile is None:
            return None

        try:
            interests = ast.literal_eval(profile['Browsing_History']) + ast.literal_eval(profile['Purchase_History'])
        except Exception as e:
            st.error(f"Error parsing customer history: {e}")
            return None

        products = self.product_agent.get_top_similar(interests)
        return products[['Product_ID', 'Category', 'Subcategory', 'Price', 'Product_Rating']]

class InteractionAgent:
    def __init__(self, recommender):
        self.recommender = recommender

    def run(self, customer_id):
        return self.recommender.recommend(customer_id)

# --- Streamlit App UI ---
st.set_page_config(page_title="Smart Shopping Recommender", layout="wide")
st.title("🛒 Smart Shopping: AI-Based Product Recommender")

# Sidebar
with st.sidebar:
    st.header("Customer Input")
    customer_id = st.text_input("Enter Customer ID:", "C1001")
    if st.button("Get Recommendations"):
        try:
            customer_agent = CustomerAgent(customer_df)
            product_agent = ProductAgent(product_df, embedder)
            recommender_agent = RecommenderAgent(customer_agent, product_agent)
            interaction_agent = InteractionAgent(recommender_agent)
            recommendations = interaction_agent.run(customer_id)
            st.session_state.recommendations = recommendations
            st.session_state.customer_agent = customer_agent
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Main Section
if "recommendations" in st.session_state:
    recommendations = st.session_state.recommendations
    if recommendations is not None:
        st.subheader("Recommended Products")
        st.write(recommendations)

        with st.expander("Customer Profile"):
            profile = st.session_state.customer_agent.get_profile(customer_id)
            if profile:
                st.json(profile)
            else:
                st.warning("Customer profile not found.")

        with st.expander("Visualizations"):
            # Customer Segment Distribution
            plt.figure(figsize=(10, 6))
            sns.countplot(data=customer_df, x='Customer_Segment', palette='coolwarm')
            plt.title("Customer Segment Distribution")
            plt.xticks(rotation=45)
            plt.ylabel("Number of Customers")
            st.pyplot(plt.gcf())
            plt.clf()

            # Top Purchased Products
            all_purchases = customer_df['Purchase_History'].apply(ast.literal_eval).sum()
            purchase_counts = Counter(all_purchases)
            top_purchases = dict(purchase_counts.most_common(10))

            plt.figure(figsize=(12, 6))
            sns.barplot(x=list(top_purchases.keys()), y=list(top_purchases.values()), palette='viridis')
            plt.title("Top 10 Purchased Products")
            plt.ylabel("Frequency")
            plt.xlabel("Product IDs")
            st.pyplot(plt.gcf())
            plt.clf()

        with st.expander("Advanced Options"):
            st.info("Advanced features coming soon!")

    else:
        st.warning(f"No recommendations found for Customer ID: {customer_id}")
else:
    st.info("Enter a Customer ID and click 'Get Recommendations' to start.")
