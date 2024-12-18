import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from io import BytesIO
import requests

st.set_page_config(
    page_title="The Dark Knights",
    page_icon="🏇"
)

username = 'ananya001'
token = '89da193bf6348e04b4709ff2b891fcab85e00fdd'
host = 'eu.pythonanywhere.com'
file_path = 'home/ananya001/Legal_data/Total1.xlsx'
response = requests.get(
    f'https://{host}/api/v0/user/{username}/files/path/{file_path}',
    headers={'Authorization': f'Token {token}'}
)
excel_data = BytesIO(response.content)
df = pd.read_excel(excel_data)
df.loc[df["Case Number"] == "n° 22-81.750", "Court"] = "Aix-en-Provence"
df['Court'] = df['Court'].str.lower()

st.write(f'''
# The Dark Knights welcome you!

This page will help you visualise and understand our final project. 

We sought to analyse the recidivism cases brought to the Cour de cassation. Where did they come from - which “cour d’appel”? Which crimes did they concern? How long did it take for a judgement to be rendered? 

We compared our data with the population of each cour d’appel. Are they correlated? The more people, the more cases?

(source : [FR](https://www.courdecassation.fr/recherche-judilibre?search_api_fulltext=En+r%C3%A9cidive&op=Rechercher&date_du=2014-01-01&date_au=&judilibre_juridiction=cc&judilibre_chambre%5B%5D=cr&page=42&previousdecisionpage=42&previousdecisionindex=0&nextdecisionpage=42&nextdecisionindex=2)) Contact: [Ananya Goyal](mailto:ananya.goyal@sciencespo.fr) , [Pauline Piketty](mailto:pauline.piketty@sciencespo.fr) or [Laila Abdalaziz](mailto:laila.abdalaziz@sciencespo.fr)

***
''')

##### Dataframe

df0 = df.copy()
df0 = df0[[
    "Case Number", "Court", "Decision_date", "Appeal_Date", "Crime_cleaned", 
    "Contains_aggravé", "Review_Duration", "Gender", "Decision"
]].rename(columns={
    "Case Number": "Case number",
    "Court": "Appeal court",
    "Decision_date": "Decision date",
    "Appeal_Date": "Appeal date",
    "Crime_cleaned": "Crime",
    "Contains_aggravé": "Aggravé",
    "Review_Duration": "Review duration",
    "Gender": "Gender",
    "Decision": "Decision"
})
df0 = df0.set_index("Case number")

df0["Crime"] = df0["Crime"].fillna("")
st.title("The Victory Table")
st.dataframe(df0)

#### Cour d'appel 

df1 = df.copy()

court_counts = df1['Court'].value_counts().reset_index()
court_counts.columns = ['Court', 'Count']

st.sidebar.title("Filter Courts")
filter_option = st.sidebar.radio(
    "Choose a filter:",
    options=["All Courts", "Top 5 Courts", "Bottom 5 Courts"]
)

if filter_option == "Top 5 Courts":
    filtered_counts = court_counts.nlargest(5, "Count")
elif filter_option == "Bottom 5 Courts":
    filtered_counts = court_counts.nsmallest(5, "Count")
else:
    filtered_counts = court_counts

st.title("Big Reveal")

st.subheader("Distribution of Recidivism Cases Across Appeal Courts")
st.write("""
Explore the distribution of recidivism cases across appellate courts. Use the sidebar to filter and view 
the top or bottom courts based on case frequency.
""")
if not filtered_counts.empty:
    bar_chart = alt.Chart(filtered_counts).mark_bar().encode(
        x=alt.X('Count:Q', title="Count"),
        y=alt.Y('Court:N', sort='-x', title="Court"),
        color=alt.Color('Court:N', legend=None)
    ).properties(
        title=f"Frequency of Courts ({filter_option})",
        width=700,
        height=400
    )
    st.altair_chart(bar_chart, use_container_width=True)
else:
    st.write("No data to display for the selected filter.")

st.subheader("Treemap of Recidivism Cases by Appeal Courts")
st.write("""
This interactive treemap shows the distribution of recidivism cases across different appellate courts 
("Cour d'Appel") based on the number of cases they handled. Each rectangle represents a court, and its size 
is proportional to the count of cases.
""")
if not filtered_counts.empty:
    treemap = px.treemap(
        filtered_counts,
        path=['Court'],  
        values='Count'
    )
    st.plotly_chart(treemap, use_container_width=True)
else:
    st.write("No data to display for the selected filter.")
## Population
df_population = pd.read_excel("Population.xlsx")
df_population = df_population.dropna(subset=["Population"])

df_population["Population"] = pd.to_numeric(df_population["Population"], errors="coerce")
df_population = df_population.groupby("City", as_index=False)["Population"].sum()

st.subheader("Treemap of Population Across Cities")
st.write("""
This treemap visualizes the population distribution across cities. Each rectangle represents a city, with 
its size proportional to the population of that city. We use this to analyze population data and compare it 
to the frequency of recidivism cases in the appellate courts.
""")

if not df_population.empty:
    treemap = px.treemap(
        df_population,
        path=['City'],  # Hierarchical structure for treemap
        values='Population'
    )
    st.plotly_chart(treemap, use_container_width=True)
else:
    st.write("No data to display.")

####### Average crimes
df_crime_analysis = df.copy()
selected_court = st.sidebar.selectbox(
    "Select Appeal Court",
    ['All'] + list(df['Court'].unique()),
    key="select_court_crime"
)
if selected_court != 'All':
    df_crime_analysis = df_crime_analysis[df_crime_analysis['Court'] == selected_court.lower()]

df2 = df_crime_analysis.copy()

df2['Decision_date'] = pd.to_datetime(df2['Decision_date'], errors='coerce')
df2['Year'] = df2['Decision_date'].dt.year
df2 = df2.dropna(subset=['Year'])

if 'Crime_cleaned' in df2.columns:
    df2['Num_crimes'] = df2['Crime_cleaned'].apply(
        lambda x: len(x.split(', ')) if isinstance(x, str) else 0
    )
else:
    st.write("Error: 'Crime_cleaned' column is missing.")
    df2['Num_crimes'] = 0

filtered_df2 = df2[df2['Num_crimes'] > 0]
avg_crimes_per_year = filtered_df2.groupby('Year')['Num_crimes'].mean().reset_index()

st.subheader("⁠Average Number of Crimes per Recidivism Case Annually")
st.write("""
This section analyzes the average number of crimes per recidivism case for each year. The analysis provides insights 
into trends in recidivism crime intensity over the years. You filter the graph based on the court using the sidebar
""")
if avg_crimes_per_year.empty:
    st.write("No data available for the selected court or year.")
else:
    chart = alt.Chart(avg_crimes_per_year).mark_bar().encode(
        x=alt.X('Year:O', title='Year'),
        y=alt.Y('Num_crimes:Q', title='Average Crimes Per Case'),
        tooltip=['Year', 'Num_crimes']
    ).properties(
        title='Average Number of Crimes Per Case Per Year',
        width=700,
        height=400
    )
    st.altair_chart(chart, use_container_width=True)

df3 = df_crime_analysis.copy()

st.subheader("Most common crimes in recidivism cases")
st.write("""
This section analyzes the frequency of different crimes in the recidivism cases dataset. You can filter the results 
to view the most or least common crimes and also filter the graph by court.
""")

if 'Crime_cleaned' in df3.columns and 'Court' in df3.columns:
    crime_list = [
        crime.strip() for crimes in df3['Crime_cleaned'].dropna() for crime in crimes.split(', ')
    ]
    crime_counts = pd.Series(crime_list).value_counts().reset_index()
    crime_counts.columns = ['Crime', 'Count']

    crime_filter_option = st.sidebar.radio(
        "Choose Crime Filter:",
        options=["All Crimes", "Top 5 Crimes", "Bottom 5 Crimes"],
        key="crime_filter"
    )

    if crime_filter_option == "Top 5 Crimes":
        crime_counts = crime_counts.head(5)
    elif crime_filter_option == "Bottom 5 Crimes":
        crime_counts = crime_counts.tail(5)
    if not crime_counts.empty:
        crime_bar_chart = alt.Chart(crime_counts).mark_bar().encode(
            x=alt.X('Count:Q', title="Frequency"),
            y=alt.Y('Crime:N', sort='-x', title="Crime"),
            tooltip=['Crime', 'Count']
        ).properties(
            title=f"Most Common Crimes ({crime_filter_option})",
            width=700,
            height=400
        )
        st.altair_chart(crime_bar_chart, use_container_width=True)
    else:
        st.write("No data to display for the selected crime filter.")
else:
    st.write("Error: Required columns 'Crime_cleaned' or 'Court' are missing.")


####### Aggrave

df4 = df[df['Contains_aggravé'] == True].copy()

court_aggravé_counts = df4['Court'].value_counts().reset_index()
court_aggravé_counts.columns = ['Court', 'Count']
st.sidebar.title("Courts involving aggravated cases")
aggravé_filter_option = st.sidebar.radio(
    "Choose a filter:",
    options=["All Courts", "Top 10 Courts", "Bottom 10 Courts"],
    key="aggravé_filter"
)

if aggravé_filter_option == "Top 10 Courts":
    filtered_aggravé_counts = court_aggravé_counts.nlargest(10, "Count")
elif aggravé_filter_option == "Bottom 10 Courts":
    filtered_aggravé_counts = court_aggravé_counts.nsmallest(10, "Count")
else:
    filtered_aggravé_counts = court_aggravé_counts

st.subheader("Distribution of Recidivism Cases Involving Aggravated Crimes across Appeal Court")
st.write("""
This section focuses on recidivism cases that involve aggravating circumstances. Using the sidebar, you can 
filter the data to view the top or bottom courts handling such cases. This analysis highlights which courts 
frequently deal with aggravated recidivism cases.
""")

if not filtered_aggravé_counts.empty:
    aggravé_bar_chart = alt.Chart(filtered_aggravé_counts).mark_bar().encode(
        x=alt.X('Count:Q', title="Count of Aggravé Cases"),
        y=alt.Y('Court:N', sort='-x', title="Court"),
        color=alt.Color('Court:N', scale=alt.Scale(scheme='category20'), legend=None)
    ).properties(
        title=f"Aggravé Cases by Court ({aggravé_filter_option})",
        width=700,
        height=400
    )
    st.altair_chart(aggravé_bar_chart, use_container_width=True)
else:
    st.write("No data to display for the selected filter.")
    
###### Review

st.subheader("Review Duration Analysis")
st.write("""
This section provides insights into the time taken to review recidivism cases. The analysis includes average 
and median review durations, expressed in both calendar days and weeks. Use the sidebar to filter by the 
decision year range to focus on specific periods.
""")

df["Decision_date"] = pd.to_datetime(df["Decision_date"], errors="coerce")
df5 = df.copy()

st.sidebar.title("Decision Year")
year_range = st.sidebar.slider("Select Year Range", min_value=2015, max_value=2024, value=(2015, 2024))

df5_filtered = df5[(df5["Decision_date"].dt.year >= year_range[0]) & (df5["Decision_date"].dt.year <= year_range[1])]
average_days = df5_filtered["Review_Duration"].mean()
median_days = df5_filtered["Review_Duration"].median()
average_weeks = average_days / 7
median_weeks = median_days / 7

summary_data = {
    "Metric": ["Average", "Median"],
    "Calendar Days": [average_days, median_days],
    "Weeks": [average_weeks, median_weeks]
}
summary_df = pd.DataFrame(summary_data).set_index("Metric")
st.caption(f"Filtered by Decision Years: {year_range[0]} - {year_range[1]}")
st.write("This DataFrame summarizes the review duration in calendar days and weeks:")
st.dataframe(summary_df)
