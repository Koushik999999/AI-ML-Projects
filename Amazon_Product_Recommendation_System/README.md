# 🛍️ Amazon Recommendation System

A **hybrid recommendation engine** (Content-Based + Collaborative Filtering) designed using publicly available Amazon product and user behavior data.

---

## 📁 Dataset

**Link:** [Download from Google Drive](https://drive.google.com/file/d/1OA0wOG1epBxHAMNXun7kwNr_QsupUMzj/view?usp=sharing)

---

## 🧠 Problem Statement

> Build and evaluate a hybrid recommendation engine for an e-commerce platform using product metadata and user behavior data.

---

## 🧹 Section A: Data Understanding & Cleaning

### 🔍 a) Understand the Dataset

- Total number of unique:
  - Users
  - Products
  - Reviews
- Top 5 categories by number of products
- Price range and discount insights

### 🧽 b) Clean & Preprocess the Data

1. Convert prices to numeric format
2. Parse categories into hierarchy levels (e.g., `category_level_1`, `category_level_2`, ...)
3. Normalize rating scores and count outliers
4. Create derived features:
   - `price_difference`
   - `value_for_money_score`
   - `weighted_rating`
5. Handle:
   - Missing values or anomalies
   - Duplicates or invalid records
   - Missing ratings/reviews with appropriate imputation strategy

---

## 📊 Section B: Exploratory Data Analysis (EDA)

> Think like a **Product Analyst** identifying buying patterns.

### 📈 Visualizations

- Most reviewed products
- Top 10 categories by number of products
- Average rating per category
- Correlation: Discounts vs Actual Price

### 👥 User Engagement Insights

- Which products have high ratings but few reviews?
- Are highly rated products also heavily reviewed?

### 💡 Actionable Insights

Generate 3 strategic insights for **Amazon's product strategy** based on EDA findings.

---

## 🧾 Section C: Content-Based Filtering

> Think like a **Content Engineer** personalizing feeds using product metadata.

### 🧠 Steps

1. Vectorize product text:
   - Use `product_name + about_product`
   - Techniques: **TF-IDF**, **word embeddings**, etc.
2. Build a **product similarity matrix**
3. Recommend top 5 similar products for:
   - A new product with no reviews (cold-start)
   - A poorly-rated product with high dropout

### 🎯 Enhance Content Vectors

Include additional metadata:
- Category
- Price
- Discount

### 📈 Evaluate Recommendations

- Are they diverse and relevant?

---

## 🤝 Section D: Collaborative Filtering (User–Item)

> You're now a **Machine Learning Engineer** leveraging user behavior.

### 🧠 Steps

1. Create a **User–Item matrix** using `user_id`, `product_id`, and `rating`
2. Apply:
   - **User–User Collaborative Filtering** (cosine similarity)
   - OR **Item–Item Collaborative Filtering** (cosine or Pearson)

### 🔄 Recommendations

- Recommend top 5 **unseen products per user**

---

## ⚡ Section E: Hybrid Recommender (Content + Collaborative)

> You're the **Senior ML Engineer** combining strengths of both models.

### 🧪 Strategy

- **Score Fusion**:  
  `Final Score = 0.6 * CollaborativeFiltering + 0.4 * ContentBased`

### 📊 Evaluation

Compare performance across:

- Individual vs. Hybrid methods
- **Cold-start product** (new product)
- **Cold-start user** (very few reviews)

### 🚀 Suggestions for Real-World Optimization

- Incorporate:
  - Product Popularity
  - Recent Purchases
  - Product Availability
