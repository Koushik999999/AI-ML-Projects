# CO₂ Emission Prediction Using Machine Learning
### Regression Analysis for Sustainable Automotive Design and Policy Decisions

## Project Overview

Reducing vehicle carbon emissions is one of the most important challenges facing the automotive industry. Governments and manufacturers require accurate predictive models to understand how vehicle specifications influence CO₂ emissions and to support environmentally sustainable vehicle design.

This project develops an end-to-end **Machine Learning Regression Pipeline** that predicts vehicle **CO₂ emissions (g/km)** using engine specifications, fuel consumption metrics, transmission characteristics, vehicle class, and fuel type.

Beyond prediction, the project performs extensive exploratory data analysis, feature engineering, multicollinearity detection, model evaluation, and business interpretation to identify the key factors driving vehicle emissions.

---

# Business Problem

The **Global Automotive Council** aims to understand the primary factors influencing vehicle CO₂ emissions and develop data-driven recommendations for reducing environmental impact.

The project addresses three key objectives:

- Predict vehicle CO₂ emissions accurately
- Identify the most influential vehicle characteristics
- Provide actionable recommendations for reducing emissions through vehicle design and policy decisions

---

# Dataset

The dataset contains approximately **7,385 vehicle records** across multiple manufacturers and vehicle categories.

## Features

| Feature | Description |
|----------|-------------|
| Make | Vehicle manufacturer |
| Model | Vehicle model |
| Vehicle Class | Vehicle category (SUV, Compact, Mid-size, etc.) |
| Engine Size (L) | Engine displacement |
| Cylinders | Number of engine cylinders |
| Transmission | Transmission type and number of gears |
| Fuel Type | Regular, Premium, Diesel, Ethanol, Natural Gas |
| Fuel Consumption (City) | City fuel consumption (L/100 km) |
| Fuel Consumption (Highway) | Highway fuel consumption (L/100 km) |
| Fuel Consumption (Combined) | Combined fuel consumption (L/100 km) |
| Fuel Consumption (MPG) | Combined fuel economy (Miles per Gallon) |
| CO₂ Emissions (g/km) | **Target Variable** |

---

# Project Workflow

```
Vehicle Dataset
        │
        ▼
Data Inspection
        │
        ▼
Data Cleaning
        │
        ▼
Exploratory Data Analysis
        │
        ▼
Feature Engineering
        │
        ▼
Correlation Analysis
        │
        ▼
Multicollinearity Detection
        │
        ▼
Regression Model
        │
        ▼
Model Evaluation
        │
        ▼
Business Recommendations
```

---

# Exploratory Data Analysis

Comprehensive EDA was performed to understand vehicle characteristics and emission behavior.

The analysis included:

- Dataset overview
- Missing value analysis
- Duplicate detection
- Distribution analysis
- Outlier identification
- Correlation heatmap
- Feature relationship analysis
- Fuel type comparison
- Vehicle class analysis

Multiple visualizations were created to identify emission patterns across different vehicle categories.

---

# Data Preprocessing

The preprocessing pipeline includes:

- Duplicate record removal
- Data quality assessment
- Categorical feature encoding
- Numerical feature preparation
- Feature scaling (where required)
- Train-Test Split

Special attention was given to preserving meaningful automotive characteristics while preparing the dataset for regression modeling.

---

# Feature Engineering

Several domain-specific preprocessing steps were performed, including:

- Encoding categorical vehicle information
- Handling transmission categories
- Fuel type transformation
- Feature selection
- Numerical feature normalization

---

# Multicollinearity Analysis

One of the key challenges in this dataset is the presence of highly correlated fuel consumption variables.

To ensure a robust regression model:

- Correlation Matrix analysis was performed
- Redundant variables were identified
- Multicollinearity was analyzed
- Feature selection was applied where necessary

This improves model stability and interpretability.

---

# Machine Learning Model

A supervised regression model was developed to estimate vehicle CO₂ emissions.

The workflow includes:

- Data preprocessing pipeline
- Model training
- Cross-validation
- Hyperparameter tuning
- Performance evaluation

---

# Model Evaluation

The regression model was evaluated using multiple metrics:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- R² Score

Additional validation included:

- Predicted vs Actual comparison
- Residual analysis
- Error distribution
- Model interpretation

These evaluation techniques provide a comprehensive understanding of prediction accuracy and generalization performance.

---

# Key Insights

The analysis identified several important observations:

- Fuel consumption is the strongest predictor of CO₂ emissions.
- Larger engine sizes generally produce higher emissions.
- Vehicles with more cylinders tend to emit more CO₂.
- Fuel economy (MPG) has a strong inverse relationship with emissions.
- Vehicle class and fuel type also influence emission levels.

The correlation analysis confirms that improving fuel efficiency is one of the most effective strategies for reducing carbon emissions.

---

# Business Recommendations

Based on the analysis:

- Promote vehicles with improved fuel efficiency.
- Encourage adoption of lower-emission fuel technologies.
- Prioritize lightweight vehicle designs.
- Reduce dependence on large engine configurations where possible.
- Develop policy incentives for low-emission vehicle categories.

These recommendations can help manufacturers and policymakers reduce fleet-wide emissions while maintaining vehicle performance.

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
Carbon_Emission/
│
├── Carbon_Emission.ipynb
├── Carbon_Emission.html
├── Carbon_Emission.pdf
├── carbon_emission_dataset.csv
├── CO2_Emission_Approach_Document.pdf
├── Dataset_Description.pdf
└── README.md
```

---

# Skills Demonstrated

- Exploratory Data Analysis (EDA)
- Data Cleaning
- Feature Engineering
- Regression Modeling
- Correlation Analysis
- Multicollinearity Detection
- Model Evaluation
- Business Analytics
- Data Visualization
- Predictive Modeling

---

# Future Improvements

- Random Forest Regression
- XGBoost Regression
- LightGBM
- Feature Importance using SHAP
- Automated Hyperparameter Optimization
- Model Deployment using FastAPI
- Interactive Dashboard using Streamlit

---

# Author

**Koushik Jayanthi**

Software Engineer | AI & Machine Learning | Java Backend Developer

**LinkedIn**: https://www.linkedin.com/in/koushik-jayanthi-2b86b5153/

**GitHub**: https://github.com/Koushik999999