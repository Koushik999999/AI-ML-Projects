# YouTube Shorts Performance Prediction
### Predicting YouTube Shorts Engagement Using Machine Learning

## Project Overview

Content creators upload thousands of YouTube Shorts every day, but predicting which videos will achieve high engagement remains a significant challenge. Understanding how factors such as video duration, upload timing, category, hashtags, and title characteristics influence engagement enables creators to optimize content strategy before publishing.

This project develops an end-to-end **Supervised Machine Learning Pipeline** to predict the engagement performance of YouTube Shorts. Multiple classification models are trained to categorize videos into **Low**, **Medium**, or **High** engagement groups based on video metadata and engineered features, providing actionable recommendations for maximizing audience reach and channel growth. :contentReference[oaicite:0]{index=0}

---

# Business Problem

Content creators often rely on intuition when deciding how to publish Shorts, leading to inconsistent performance.

This project addresses three primary objectives:

- Predict whether a YouTube Short will achieve Low, Medium, or High engagement before publishing.
- Identify the most influential content and publishing factors affecting engagement.
- Provide data-driven recommendations to improve video performance and audience growth. :contentReference[oaicite:1]{index=1}

---

# Dataset

The dataset contains metadata and engagement statistics collected from **300 YouTube Shorts**.

## Features

| Feature | Description |
|----------|-------------|
| Video ID | Unique identifier |
| Title | Video title |
| Duration | Length of the Short (seconds) |
| Hashtags Count | Number of hashtags used |
| Views | Total video views |
| Likes | Number of likes |
| Comments | Number of comments |
| Shares | Number of shares |
| Upload Hour | Hour when the Short was published |
| Category | Video category |

The target variable (**Performance Engagement Tertile**) is created using the Engagement Rate:

**Engagement Rate = (Likes + Comments + Shares) / Views**

Videos are classified into **Low**, **Medium**, or **High** engagement using quantile-based thresholds. :contentReference[oaicite:2]{index=2}

---

# Project Workflow

```
YouTube Shorts Dataset
          │
          ▼
Data Inspection
          │
          ▼
Data Cleaning
          │
          ▼
Feature Engineering
          │
          ▼
Exploratory Data Analysis
          │
          ▼
Feature Transformation
          │
          ▼
Data Preprocessing Pipeline
          │
          ▼
Model Training
          │
          ▼
Hyperparameter Tuning
          │
          ▼
Model Evaluation
          │
          ▼
Feature Importance
          │
          ▼
Business Recommendations
```

---

# Exploratory Data Analysis

A comprehensive exploratory analysis was performed to understand factors influencing video engagement.

The analysis included:

- Engagement rate distribution
- Category-wise engagement comparison
- Duration vs engagement analysis
- Upload hour performance analysis
- Correlation heatmap
- Title feature analysis
- Question mark impact analysis
- Feature relationship visualization

These analyses helped identify patterns and guided feature engineering for the predictive models. :contentReference[oaicite:3]{index=3}

---

# Data Preprocessing

The preprocessing pipeline includes:

- Missing value handling
- Numerical feature scaling
- Categorical feature encoding
- Stratified train-test split
- ColumnTransformer pipelines
- Feature normalization

Separate preprocessing pipelines were created for numerical and categorical features to improve model performance. :contentReference[oaicite:4]{index=4}

---

# Feature Engineering

Several informative features were engineered to improve predictive accuracy, including:

- Engagement Rate calculation
- Performance tertile creation
- Title length (characters)
- Title word count
- Question mark detection
- Likes per second
- Comments per second
- Shares per second
- Log transformation of views, likes, comments, and shares
- Peak upload hour indicator

These engineered features capture both content characteristics and publishing behavior that influence engagement. :contentReference[oaicite:5]{index=5}

---

# Machine Learning Models

Multiple supervised classification algorithms were implemented and compared:

### Logistic Regression

- Baseline linear classification model

### Random Forest Classifier

- Ensemble learning using decision trees
- Feature importance analysis

### K-Nearest Neighbors (KNN)

- Instance-based classification

### Support Vector Machine (SVM)

- Margin-based classifier for multi-class prediction

Model performance was compared to identify the best predictor of engagement categories. :contentReference[oaicite:6]{index=6}

---

# Model Evaluation

The models were evaluated using multiple classification metrics:

- Accuracy
- Precision
- Recall
- F1-Score (Macro)
- Confusion Matrix
- ROC-AUC (One-vs-Rest)
- Cross Validation

Hyperparameter tuning was performed using GridSearch/RandomizedSearch to optimize model performance. :contentReference[oaicite:7]{index=7}

---

# Key Insights

The analysis revealed several important observations:

- Video engagement depends on a combination of content characteristics and publishing behavior.
- Upload timing significantly influences engagement performance.
- Engineered textual features provide additional predictive value.
- Log transformation reduces skewness in highly imbalanced engagement metrics.
- Tree-based models help identify the most influential factors affecting YouTube Shorts performance.

---

# Business Recommendations

Based on the analysis:

- Publish Shorts during high-engagement hours.
- Optimize video duration based on engagement trends.
- Write concise and engaging titles.
- Use effective hashtag strategies.
- Focus on content categories with consistently higher engagement.
- Apply predictive modeling before publishing to estimate expected performance and improve content planning. :contentReference[oaicite:8]{index=8}

---

# Technologies Used

- Python
- Pandas
- NumPy
- Scikit-Learn
- Matplotlib
- Seaborn

---

# Repository Structure

```
Youtube_Shorts_Performance/
│
├── Youtube_Shorts_Performance.ipynb
├── Youtube_Shorts_Performance.html
├── youtube_shorts_performance_dataset.csv
├── YouTube Shorts Performance Prediction - Approach Document.pdf
└── README.md
```

---

# Skills Demonstrated

- Exploratory Data Analysis (EDA)
- Feature Engineering
- Data Preprocessing Pipelines
- Feature Scaling
- One-Hot Encoding
- Supervised Machine Learning
- Logistic Regression
- Random Forest
- K-Nearest Neighbors (KNN)
- Support Vector Machine (SVM)
- Hyperparameter Tuning
- Cross Validation
- Model Evaluation
- Feature Importance Analysis
- Business Analytics

---

# Future Improvements

- XGBoost and LightGBM implementation
- NLP-based title sentiment analysis
- Thumbnail feature extraction using Computer Vision
- Deep Learning models for engagement prediction
- SHAP explainability for model interpretation
- Streamlit dashboard for real-time prediction
- Deployment as a REST API for content creators

---

# Author

**Koushik Jayanthi**

Software Engineer | AI & Machine Learning | Java Backend Developer

**GitHub**: https://github.com/Koushik999999

**LinkedIn**: https://www.linkedin.com/in/koushik-jayanthi-2b86b5153/