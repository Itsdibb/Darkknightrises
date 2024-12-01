import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from io import BytesIO
import requests

# Streamlit page configuration
st.set_page_config(
    page_title="The Dark Knights",
    page_icon="🏇"
)

# Replace with your actual file details
username = 'ananya001'
token = '89da193bf6348e04b4709ff2b891fcab85e00fdd'
host = 'eu.pythonanywhere.com'
file_path = 'home/ananya001/Legal_data/Total1.xlsx'

# Fetch the Excel file
response = requests.get(
    f'https://{host}/api/v0/user/{username}/files/path/{file_path}',
    headers={'Authorization': f'Token {token}'}
)
excel_data = BytesIO(response.content)
df = pd.read_excel(excel_data)

# Preprocess the data
df.loc[df["Case Number"] == "n° 22-81.750", "Court"] = "Aix-en-Provence"

# Convert court names to lowercase
df['Court'] = df['Court'].str.lower()

df1 = df.copy()

# Generate court counts
court_counts = df1['Court'].value_counts().reset_index()
court_counts.columns = ['Court', 'Count']

# Sidebar for selecting a filter
st.sidebar.title("Filter Courts")
filter_option = st.sidebar.radio(
    "Choose a filter:",
    options=["All Courts", "Top 5 Courts", "Bottom 5 Courts"]
)

# Apply the selected filter
if filter_option == "Top 5 Courts":
    filtered_counts = court_counts.nlargest(5, "Count")
elif filter_option == "Bottom 5 Courts":
    filtered_counts = court_counts.nsmallest(5, "Count")
else:
    filtered_counts = court_counts

# Streamlit title
st.title("The Dark Knights")

# Bar Chart using Altair
st.subheader("Cour d'Appel")
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

if not filtered_counts.empty:
    treemap = px.treemap(
        filtered_counts,
        path=['Court'],  # Hierarchical structure for treemap
        values='Count',
        title=f"Court Frequencies Treemap ({filter_option})"
    )
    st.plotly_chart(treemap, use_container_width=True)
else:
    st.write("No data to display for the selected filter.")


df_population = pd.read_excel("Population.xlsx")

# Preprocess the data
# Drop rows where 'Population' is NaN
df_population = df_population.dropna(subset=["Population"])

# Ensure 'Population' is numeric
df_population["Population"] = pd.to_numeric(df_population["Population"], errors="coerce")

# Group and aggregate if needed (optional, if duplicates exist)
df_population = df_population.groupby("City", as_index=False)["Population"].sum()

# Streamlit title
st.title("City Population Treemap")

# Treemap using Plotly
if not df_population.empty:
    treemap = px.treemap(
        df_population,
        path=['City'],  # Hierarchical structure for treemap
        values='Population',
        title="City Population Treemap"
    )
    st.plotly_chart(treemap, use_container_width=True)
else:
    st.write("No data to display.")

#######
# Additional Analysis: Average Crimes Per Case
st.sidebar.title("Crime Analysis")
selected_court = st.sidebar.selectbox("Select Court", ['All'] + list(df['Court'].unique()), key="select_court")

# Apply court filter to both `df2` and `df3`
if selected_court != 'All':
    df = df[df['Court'] == selected_court.lower()]

# Create a copy for crime analysis (df2)
df2 = df.copy()

# Ensure valid data in 'Crime_cleaned' and 'Decision_date'
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

# Filter based on selected court for df2
filtered_df2 = df2[df2['Num_crimes'] > 0]
avg_crimes_per_year = filtered_df2.groupby('Year')['Num_crimes'].mean().reset_index()

# Display Average Crimes Per Case
st.subheader("Average Number of Crimes Per Case Per Year")
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

# Analysis for Most Common Crimes (df3)
df3 = df.copy()

if 'Crime_cleaned' in df3.columns and 'Court' in df3.columns:
    # Generate a list of all crimes
    crime_list = [
        crime.strip() for crimes in df3['Crime_cleaned'].dropna() for crime in crimes.split(', ')
    ]

    # Compute the frequency of each crime
    crime_counts = pd.Series(crime_list).value_counts().reset_index()
    crime_counts.columns = ['Crime', 'Count']

    # Sidebar Filter for Most Common Crimes
    crime_filter_option = st.sidebar.radio(
        "Choose Crime Filter:",
        options=["All Crimes", "Top 5 Crimes", "Bottom 5 Crimes"],
        key="crime_filter"
    )

    # Apply crime filter
    if crime_filter_option == "Top 5 Crimes":
        crime_counts = crime_counts.head(5)
    elif crime_filter_option == "Bottom 5 Crimes":
        crime_counts = crime_counts.tail(5)

    # Display Most Common Crimes
    st.subheader("Most Common Crimes")
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


#######

# Create df4 with only cases where Contains_aggravé is True
df4 = df[df['Contains_aggravé'] == True].copy()

# Group by Court and count the cases
court_aggravé_counts = df4['Court'].value_counts().reset_index()
court_aggravé_counts.columns = ['Court', 'Count']

# Sidebar for selecting a filter specific to aggravé cases
st.sidebar.title("Filter Courts for Aggravé Cases")
aggravé_filter_option = st.sidebar.radio(
    "Choose a filter:",
    options=["All Courts", "Top 10 Courts", "Bottom 10 Courts"],
    key="aggravé_filter"
)

# Apply the selected filter (this does not affect any other part of the app)
if aggravé_filter_option == "Top 10 Courts":
    filtered_aggravé_counts = court_aggravé_counts.nlargest(10, "Count")
elif aggravé_filter_option == "Bottom 10 Courts":
    filtered_aggravé_counts = court_aggravé_counts.nsmallest(10, "Count")
else:
    filtered_aggravé_counts = court_aggravé_counts

# Display the title for the analysis
st.title("Aggravé Case Frequency Analysis")

# Bar Chart using Altair with category20 colors
st.subheader("Bar Chart of Aggravé Cases by Court")
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
######
df["Decision_date"] = pd.to_datetime(df["Decision_date"], errors="coerce")
df5 = df.copy()

# Sidebar: Year filter
st.sidebar.title("Filter by Decision Year")
year_range = st.sidebar.slider("Select Year Range", min_value=2015, max_value=2024, value=(2015, 2024))

# Filter df5 by selected year range
df5_filtered = df5[(df5["Decision_date"].dt.year >= year_range[0]) & (df5["Decision_date"].dt.year <= year_range[1])]

# Calculate statistics
average_days = df5_filtered["Review_Duration"].mean()
median_days = df5_filtered["Review_Duration"].median()
average_weeks = average_days / 7
median_weeks = median_days / 7

# Create a summary DataFrame
summary_data = {
    "Metric": ["Average", "Median"],
    "Calendar Days": [average_days, median_days],
    "Weeks": [average_weeks, median_weeks]
}
summary_df = pd.DataFrame(summary_data)

# Display the summary DataFrame
st.title("Review Duration Analysis")
st.subheader(f"Filtered by Decision Years: {year_range[0]} - {year_range[1]}")
st.write("This DataFrame summarizes the review duration in calendar days and weeks:")
st.dataframe(summary_df)
