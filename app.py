# ===========================
# Nutrition Paradox Dashboard
# ===========================

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

# ---------------------------
# SQL Connection (Read-Only Recommended)
# ---------------------------
host = 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com'
user = '3qKZvyc8Bw7Ckf1.root'
password = 'ixPIapSBo4owm2Qf'
db = 'Nutrition_Paradox'

engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{db}")

# ---------------------------
# Function to safely fetch data
# ---------------------------
@st.cache_data
def get_data(query):
    return pd.read_sql(query, engine)

# ---------------------------
# App Setup
# ---------------------------
st.set_page_config(layout="wide", page_title="Nutrition Paradox Dashboard")
st.title("🌍 Nutrition Paradox Dashboard")
st.markdown("Interactive dashboards showing global **Obesity** and **Malnutrition** trends")

# ---------------------------
# Sidebar Filters
# ---------------------------
st.sidebar.header("Filters")
selected_region = st.sidebar.selectbox("Select Region", ["All"] + list(get_data("SELECT DISTINCT Region FROM obesity")["Region"]))
selected_country = st.sidebar.selectbox("Select Country", ["All"] + list(get_data("SELECT DISTINCT Country FROM obesity")["Country"]))
selected_year = st.sidebar.selectbox("Select Year", ["All"] + list(map(int, get_data("SELECT DISTINCT Year FROM obesity")["Year"])))
selected_gender = st.sidebar.selectbox("Select Gender", ["All", "Male", "Female", "Both"])
selected_age = st.sidebar.selectbox("Select Age Group", ["All", "adults", "child/adolescent"])

# ---------------------------
# Helper: Build WHERE clause
# ---------------------------
def build_where(df_name="obesity"):
    conditions = []
    if selected_region != "All":
        conditions.append(f"Region='{selected_region}'")
    if selected_country != "All":
        conditions.append(f"Country='{selected_country}'")
    if selected_year != "All":
        conditions.append(f"Year={selected_year}")
    if selected_gender != "All":
        conditions.append(f"Gender='{selected_gender}'")
    if selected_age != "All":
        conditions.append(f"age_group='{selected_age}'")
    if conditions:
        return "WHERE " + " AND ".join(conditions)
    else:
        return ""

# ---------------------------
# Obesity Section
# ---------------------------
st.header("📊 Obesity Analysis")

query_obesity = f"""
SELECT * FROM obesity {build_where()}
"""
df_obesity = get_data(query_obesity)

if not df_obesity.empty:
    st.subheader("Obesity Data Preview")
    st.dataframe(df_obesity)

    fig1 = px.bar(df_obesity.groupby("Region")["Mean_Estimate"].mean().reset_index(),
                  x="Region", y="Mean_Estimate",
                  color="Mean_Estimate",
                  color_continuous_scale=px.colors.sequential.Viridis,
                  title="Average Obesity by Region")
    st.plotly_chart(fig1)

    fig2 = px.line(df_obesity.groupby("Year")["Mean_Estimate"].mean().reset_index(),
                   x="Year", y="Mean_Estimate",
                   markers=True,
                   line_shape='spline',
                   color_discrete_sequence=px.colors.qualitative.Bold,
                   title="Global Obesity Trend Over Years")
    st.plotly_chart(fig2)
else:
    st.info("No obesity data for the selected filters.")

# ---------------------------
# Malnutrition Section
# ---------------------------
st.header("🥗 Malnutrition Analysis")

query_malnutrition = f"""
SELECT * FROM malnutrition {build_where(df_name='malnutrition')}
"""
df_malnutrition = get_data(query_malnutrition)

if not df_malnutrition.empty:
    st.subheader("Malnutrition Data Preview")
    st.dataframe(df_malnutrition)

    fig3 = px.bar(df_malnutrition.groupby("Region")["Mean_Estimate"].mean().reset_index(),
                  x="Region", y="Mean_Estimate",
                  color="Mean_Estimate",
                  color_continuous_scale=px.colors.sequential.Plasma,
                  title="Average Malnutrition by Region")
    st.plotly_chart(fig3)

    fig4 = px.line(df_malnutrition.groupby("Year")["Mean_Estimate"].mean().reset_index(),
                   x="Year", y="Mean_Estimate",
                   markers=True,
                   line_shape='spline',
                   color_discrete_sequence=px.colors.qualitative.Bold,
                   title="Global Malnutrition Trend Over Years")
    st.plotly_chart(fig4)
else:
    st.info("No malnutrition data for the selected filters.")

# ---------------------------
# Comparison Section
# ---------------------------
st.header("⚖️ Obesity vs Malnutrition Comparison")

if not df_obesity.empty and not df_malnutrition.empty:
    df_cmp_ob = df_obesity.groupby(["Country","Year"])["Mean_Estimate"].mean().reset_index().rename(columns={"Mean_Estimate":"avg_obesity"})
    df_cmp_mal = df_malnutrition.groupby(["Country","Year"])["Mean_Estimate"].mean().reset_index().rename(columns={"Mean_Estimate":"avg_malnutrition"})
    df_cmp = pd.merge(df_cmp_ob, df_cmp_mal, on=["Country","Year"])
    fig_cmp = px.line(df_cmp, x="Year", y=["avg_obesity","avg_malnutrition"],
                      color="Country", markers=True,
                      title="Obesity vs Malnutrition Comparison")
    st.plotly_chart(fig_cmp)

# ---------------------------
# ---------------------------
# Query Section (All 25 Queries)
# ---------------------------
st.header("🔍 Query Explorer")

queries = {
    # --- Obesity Queries ---
    "Obesity - Top 5 regions (2022)": """SELECT Region, AVG(Mean_Estimate) as avg_obesity FROM obesity WHERE Year=2022 GROUP BY Region ORDER BY avg_obesity DESC LIMIT 5""",
    "Obesity - Top 5 countries": """SELECT Country, AVG(Mean_Estimate) as avg_obesity FROM obesity GROUP BY Country ORDER BY avg_obesity DESC LIMIT 5""",
    "Obesity - Trend India": """SELECT Year, AVG(Mean_Estimate) as avg_obesity FROM obesity WHERE Country='India' GROUP BY Year ORDER BY Year""",
    "Obesity - Average by Gender": """SELECT Gender, AVG(Mean_Estimate) as avg_obesity FROM obesity GROUP BY Gender""",
    "Obesity - Country count by obesity_level & age_group": """SELECT obesity_level, age_group, COUNT(DISTINCT Country) as country_count FROM obesity GROUP BY obesity_level, age_group""",
    "Obesity - Top 5 least reliable countries": """SELECT Country, AVG(CI_Width) as avg_ci FROM obesity GROUP BY Country ORDER BY avg_ci DESC LIMIT 5""",
    "Obesity - Average by Age Group": """SELECT age_group, AVG(Mean_Estimate) as avg_obesity FROM obesity GROUP BY age_group""",
    "Obesity - Top 10 low consistent countries": """SELECT Country, AVG(Mean_Estimate) as avg_obesity, AVG(CI_Width) as avg_ci FROM obesity GROUP BY Country HAVING avg_obesity < 10 AND avg_ci < 3 ORDER BY avg_obesity ASC LIMIT 10""",
    "Obesity - Female vs Male diff": """SELECT o_f.Country, o_f.Mean_Estimate - o_m.Mean_Estimate as diff FROM obesity o_f JOIN obesity o_m ON o_f.Country=o_m.Country AND o_f.Year=o_m.Year WHERE o_f.Gender='Female' AND o_m.Gender='Male' ORDER BY diff DESC LIMIT 10""",
    "Obesity - Global avg per year": """SELECT Year, AVG(Mean_Estimate) as avg_obesity FROM obesity GROUP BY Year ORDER BY Year""",
    
    # --- Malnutrition Queries ---
    "Malnutrition - Avg by Age Group": """SELECT age_group, AVG(Mean_Estimate) as avg_malnutrition FROM malnutrition GROUP BY age_group""",
    "Malnutrition - Top 5 countries": """SELECT Country, AVG(Mean_Estimate) as avg_malnutrition FROM malnutrition GROUP BY Country ORDER BY avg_malnutrition DESC LIMIT 5""",
    "Malnutrition - Trend Africa": """SELECT Year, AVG(Mean_Estimate) as avg_malnutrition FROM malnutrition WHERE Region='Africa' GROUP BY Year ORDER BY Year""",
    "Malnutrition - Average by Gender": """SELECT Gender, AVG(Mean_Estimate) as avg_malnutrition FROM malnutrition GROUP BY Gender""",
    "Malnutrition - Level-wise avg CI_Width": """SELECT malnutrition_level, age_group, AVG(CI_Width) as avg_ci FROM malnutrition GROUP BY malnutrition_level, age_group""",
    "Malnutrition - Yearly change India/Nigeria/Brazil": """SELECT Country, Year, AVG(Mean_Estimate) as avg_malnutrition FROM malnutrition WHERE Country IN ('India','Nigeria','Brazil') GROUP BY Country, Year ORDER BY Country, Year""",
    "Malnutrition - Regions lowest avg": """SELECT Region, AVG(Mean_Estimate) as avg_malnutrition FROM malnutrition GROUP BY Region ORDER BY avg_malnutrition ASC LIMIT 5""",
    "Malnutrition - Countries increasing": """SELECT Country, MIN(Mean_Estimate) as min_val, MAX(Mean_Estimate) as max_val FROM malnutrition GROUP BY Country HAVING MAX(Mean_Estimate)-MIN(Mean_Estimate)>0 ORDER BY max_val-min_val DESC LIMIT 10""",
    "Malnutrition - Min/Max year-wise": """SELECT Year, MIN(Mean_Estimate) as min_malnutrition, MAX(Mean_Estimate) as max_malnutrition FROM malnutrition GROUP BY Year ORDER BY Year""",
    "Malnutrition - High CI_Width flags": """SELECT Country, Year, CI_Width FROM malnutrition WHERE CI_Width>5 ORDER BY CI_Width DESC LIMIT 20""",
    
    # --- Combined Queries ---
    "Combined - Obesity vs Malnutrition (5 countries)": """SELECT o.Country, AVG(o.Mean_Estimate) AS avg_obesity, AVG(m.Mean_Estimate) AS avg_malnutrition FROM obesity o JOIN malnutrition m ON o.Country=m.Country AND o.Year=m.Year WHERE o.Country IN ('India','USA','Nigeria','Brazil','China') GROUP BY o.Country""",
    "Combined - Gender disparity both": """SELECT o.Gender, AVG(o.Mean_Estimate) AS avg_obesity, AVG(m.Mean_Estimate) AS avg_malnutrition FROM obesity o JOIN malnutrition m ON o.Country=m.Country AND o.Year=m.Year AND o.Gender=m.Gender GROUP BY o.Gender""",
    "Combined - Region avg Africa vs America": """SELECT o.Region, AVG(o.Mean_Estimate) AS avg_obesity, AVG(m.Mean_Estimate) AS avg_malnutrition FROM obesity o JOIN malnutrition m ON o.Country=m.Country AND o.Year=m.Year WHERE o.Region IN ('Africa','America') GROUP BY o.Region""",
    "Combined - Countries obesity up & malnutrition down": """SELECT o.Country, (MAX(o.Mean_Estimate)-MIN(o.Mean_Estimate)) AS obesity_change, (MAX(m.Mean_Estimate)-MIN(m.Mean_Estimate)) AS malnutrition_change FROM obesity o JOIN malnutrition m ON o.Country=m.Country AND o.Year=m.Year GROUP BY o.Country HAVING obesity_change>0 AND malnutrition_change<0 ORDER BY obesity_change DESC""",
    "Combined - Age-wise trend analysis": """SELECT o.age_group, o.Year, AVG(o.Mean_Estimate) AS avg_obesity, AVG(m.Mean_Estimate) AS avg_malnutrition FROM obesity o JOIN malnutrition m ON o.Country=m.Country AND o.Year=m.Year AND o.age_group=m.age_group GROUP BY o.age_group,o.Year ORDER BY o.age_group,o.Year"""
}

selected_query = st.selectbox("Select a Query to Run", list(queries.keys()))

if selected_query:
    df_query = get_data(queries[selected_query])
    st.subheader(f"Query Result: {selected_query}")
    st.dataframe(df_query)

    # Auto-chart if numeric exists
    numeric_cols = df_query.select_dtypes(include=["float","int"]).columns
    if len(numeric_cols) > 0:
        if len(numeric_cols) == 1:
            fig_query = px.bar(df_query, x=df_query.columns[0], y=numeric_cols[0],
                               color=numeric_cols[0],
                               color_continuous_scale=px.colors.sequential.Viridis,
                               title=f"Visualization: {selected_query}")
        else:
            fig_query = px.bar(df_query, x=df_query.columns[0], y=numeric_cols,
                               barmode='group',
                               color_discrete_sequence=px.colors.qualitative.Pastel,
                               title=f"Visualization: {selected_query}")
        st.plotly_chart(fig_query)
    else:
        st.info("This query does not have numeric data for charting.")
