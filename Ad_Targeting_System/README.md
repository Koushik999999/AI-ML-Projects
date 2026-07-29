# Ad Targeting Optimization Using User Segmentation
### Unsupervised Machine Learning & Deep Learning for Intelligent Digital Advertising

## Project Overview

Digital advertising platforms often display the same advertisements to all users, resulting in inefficient budget allocation and lower Click-Through Rates (CTR).

This project develops an intelligent audience segmentation system that groups users based on demographic and behavioral characteristics using **Unsupervised Machine Learning** and **Deep Learning**. The discovered customer segments are then evaluated using actual click behavior to identify high-value audiences and recommend optimized advertising strategies.

The project compares a traditional clustering approach (**K-Means**) against a representation-learning approach (**Autoencoder + K-Means**) to determine which produces more meaningful customer segments.

---

## Business Problem

A digital advertising company currently serves advertisements uniformly across all users, regardless of their interests or browsing behavior.

This leads to:

- Inefficient advertising spend
- Poor audience targeting
- Lower Click-Through Rates (CTR)
- Reduced Return on Advertising Spend (ROAS)

The objective is to automatically discover meaningful customer segments without using labeled data during training and then evaluate which segments generate the highest advertising engagement.

---

## Dataset

The project uses a customer advertising dataset containing **10,000 user records**.

### Features

| Feature | Description |
|----------|-------------|
| Age | User age |
| Gender | Male, Female, Non-Binary |
| Device Type | Desktop, Mobile, Tablet |
| Ad Position | Top, Side, Bottom |
| Browsing History | Shopping, News, Entertainment, Education, Social Media |
| Time of Day | Morning, Afternoon, Evening, Night |
| Click | Binary target (Used **only** for evaluation) |

**Important:**  
The `click` column is **never used while training the clustering models**. It is reserved exclusively for measuring cluster quality from a business perspective after segmentation.

---

# Project Workflow

```
Dataset
     │
     ▼
Data Cleaning
     │
     ▼
Missing Value Treatment
     │
     ▼
One-Hot Encoding
     │
     ▼
Feature Scaling
     │
     ├──────────────┐
     ▼              ▼
 K-Means      Autoencoder
     │              │
     │        Latent Features
     │              │
     └──────► K-Means
                     │
                     ▼
          Customer Segmentation
                     │
                     ▼
      Cluster Evaluation using CTR
                     │
                     ▼
      Business Recommendations
```

---

# Data Preprocessing

The following preprocessing pipeline was implemented:

- Removed non-predictive columns (`id`, `full_name`)
- Median imputation for numerical features
- "Unknown" category for missing categorical values
- One-Hot Encoding of categorical features
- StandardScaler for feature normalization

---

# Machine Learning Approach

## 1. Traditional K-Means

The baseline model performs clustering directly on the engineered feature space.

### Model Selection

Different values of **K** were evaluated using:

- Silhouette Score
- Davies-Bouldin Index

The optimal number of clusters was selected based on clustering quality and business interpretability.

---

# Deep Learning Approach

## Autoencoder + K-Means

Instead of clustering the original feature space, an Autoencoder learns a compressed latent representation of customer behavior.

Architecture:

```
Input
   ↓
Dense (64)
   ↓
Dense (32)
   ↓
Latent Space (8)
   ↓
Dense (32)
   ↓
Dense (64)
   ↓
Output
```

The learned latent vectors are then clustered using K-Means.

This approach captures hidden relationships between demographic and behavioral variables that traditional clustering may overlook.

---

# Evaluation Metrics

Both approaches are evaluated using internal clustering metrics and business metrics.

### Internal Metrics

- Silhouette Score
- Davies-Bouldin Index

### Business Metric

- Click-Through Rate (CTR)

The best model should maximize the separation between high-value and low-value customer segments.

---

# Model Performance

| Metric | K-Means | Autoencoder + K-Means |
|---------|---------|-----------------------|
| Silhouette Score | 0.136 | **0.428** |
| Davies-Bouldin Index | 2.523 | **0.984** |
| Maximum CTR Gap | 7.78% | **9.32%** |

### Result

The Autoencoder-based approach produced:

- Better cluster separation
- More compact customer segments
- Higher business value
- Better discrimination between high-CTR and low-CTR users

---

# Key Business Insights

The discovered customer segments reveal significant differences in user engagement.

High-performing segments should receive:

- Increased advertising budget
- Premium ad inventory
- Personalized creatives
- Higher retargeting frequency

Low-performing segments should receive:

- Reduced advertising spend
- Lower bidding strategy
- Contextual advertising only

This enables more efficient budget allocation while maximizing advertising ROI.

---

# Technologies Used

- Python
- Pandas
- NumPy
- Scikit-Learn
- TensorFlow / Keras
- Matplotlib

---

# Repository Structure

```
Ad_Targeting_System/
│
├── Ad_Targeting_System.ipynb
├── Ad_Targeting_System.html
├── Ad_Targeting_System.pdf
├── ad_click_dataset.csv
├── Ad Targeting Optimization - Approach Document.pdf
├── Dataset Overview.pdf
└── README.md
```

---

# Future Improvements

- Gaussian Mixture Models
- DBSCAN Clustering
- HDBSCAN
- PCA / t-SNE / UMAP Visualization
- Real-time User Segmentation
- Production Deployment using FastAPI
- Online Learning for Dynamic User Profiles

---

# Skills Demonstrated

- Data Cleaning
- Feature Engineering
- Unsupervised Machine Learning
- Deep Learning
- Representation Learning
- Customer Segmentation
- Model Evaluation
- Business Analytics
- Marketing Analytics

---

# Author

**Koushik Jayanthi**

Software Engineer | AI & Machine Learning | Java Backend Developer

[LinkedIn: Koushik Jayanthi](https://www.linkedin.com/in/koushik-jayanthi-2b86b5153/)

[GitHub: Koushik999999](https://github.com/Koushik999999)