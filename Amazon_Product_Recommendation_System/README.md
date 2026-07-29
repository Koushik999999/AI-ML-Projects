# Amazon Product Recommendation System

## Project Overview

Developed an end-to-end **Product Recommendation System** using Amazon product data to deliver personalized recommendations through **Content-Based Filtering**, **Collaborative Filtering**, and a **Hybrid Recommendation Engine**.

The project follows a real-world machine learning workflow, beginning with data understanding and preprocessing, followed by exploratory data analysis, feature engineering, recommendation modeling, evaluation, and business recommendations.

---

## Business Problem

Large e-commerce platforms contain millions of products, making it difficult for customers to discover relevant items.

The objective of this project is to build an intelligent recommendation system capable of:

- Recommending similar products
- Personalizing recommendations for users
- Handling cold-start products
- Improving product discovery
- Increasing customer engagement and conversion

---

## Dataset

Amazon Product Dataset containing:

- Product Information
- Product Categories
- Product Descriptions
- Product Ratings
- Rating Counts
- User IDs
- Product IDs
- Prices
- Discount Percentages

---

## Project Workflow

```
Data Collection
        │
        ▼
Data Cleaning & Preprocessing
        │
        ▼
Exploratory Data Analysis
        │
        ▼
Feature Engineering
        │
        ▼
Content-Based Filtering
        │
        ▼
Collaborative Filtering
        │
        ▼
Hybrid Recommendation System
        │
        ▼
Evaluation & Business Insights
```

---

# Data Preprocessing

Performed several preprocessing steps including:

- Missing value handling
- Price conversion to numeric values
- Category hierarchy extraction
- Rating normalization
- Outlier detection using IQR
- Feature scaling
- Derived feature generation

Created engineered features such as:

- Price Difference
- Value-for-Money Score
- Normalized Rating
- Discount Percentage
- Category Levels

---

# Exploratory Data Analysis

Performed detailed business analysis including:

- Product distribution across categories
- Most reviewed products
- Average ratings by category
- Discount analysis
- Rating distribution
- Price vs Discount relationship
- Rating vs Review Count correlation
- High-rated but under-reviewed products

Generated multiple visualizations using:

- Bar Charts
- Histograms
- Correlation Analysis
- Box Plots

---

# Recommendation Models

## 1. Content-Based Filtering

Built a recommendation engine using:

- TF-IDF Vectorization
- Product Name
- Product Description
- Cosine Similarity

Capabilities:

- Similar Product Recommendation
- New Product Recommendation
- Cold Start Product Support

---

## 2. Collaborative Filtering

Implemented Item-Based Collaborative Filtering using:

- User-Item Matrix
- Cosine Similarity
- Item Similarity Matrix

Capabilities:

- Personalized User Recommendations
- Top-N Product Recommendation

---

## 3. Hybrid Recommendation System

Combined:

- Content-Based Scores
- Collaborative Filtering Scores

to improve recommendation quality.

The hybrid model helps:

- Reduce cold-start problems
- Improve recommendation accuracy
- Increase recommendation diversity

---

# Model Evaluation

Evaluated recommendation quality using:

- Cosine Similarity
- Recommendation Relevance
- Recommendation Diversity
- User Preference Matching

---

# Technologies Used

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Scikit-learn
- SciPy
- TF-IDF Vectorizer
- Cosine Similarity
- Jupyter Notebook

---

# Business Insights

Some key findings include:

- Product ratings and review counts show only weak correlation.
- Mid-range products often receive competitive discounts.
- Computer accessories attract the highest review volume.
- Content-based filtering effectively recommends similar products.
- Collaborative filtering personalizes recommendations using user interactions.
- Hybrid recommendations improve overall recommendation quality and mitigate cold-start issues.

---

# Skills Demonstrated

- Exploratory Data Analysis
- Data Cleaning
- Feature Engineering
- Recommendation Systems
- Content-Based Filtering
- Collaborative Filtering
- Hybrid Recommender Systems
- Cosine Similarity
- TF-IDF
- Machine Learning
- Business Analytics

---

# Repository Structure

```
Amazon_Product_Recommendation_System/
│
├── Amazon_Recommendation_System.ipynb
├── amazon.csv
├── README.md
```

---

# Future Improvements

- Matrix Factorization (SVD)
- Neural Collaborative Filtering
- Deep Learning Recommenders
- Two-Tower Recommendation Models
- Session-Based Recommendations
- Real-Time Recommendation APIs
- Implicit Feedback Modeling
- Explainable Recommendations

---

# Author

**Koushik Jayanthi**

Software Engineer | AI & Machine Learning | Java Backend Developer

**LinkedIn**: https://www.linkedin.com/in/koushik-jayanthi-2b86b5153/

**GitHub**: https://github.com/Koushik999999