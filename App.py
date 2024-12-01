import requests
import streamlit as st
import numpy as np
from datetime import datetime, date, timedelta
import pandas as pd
from io import BytesIO
from deta import Deta
import altair as alt
import re

st.set_page_config(
    page_title="FR case tracker",
    page_icon="🇫🇷"
)

day = timedelta(days=1)


username = 'ananya001'
token = '89da193bf6348e04b4709ff2b891fcab85e00fdd'
host = 'eu.pythonanywhere.com'
file_path = 'home/ananya001/test4/final.csv' 
response = requests.get(
    f'https://{host}/api/v0/user/{username}/files/path/{file_path}',
    headers={'Authorization': f'Token {token}'}
)
csv_data = BytesIO(response.content)
df = pd.read_csv(csv_data)

df['Last_update'] = pd.to_datetime(df['Last_update'], format='%d/%m/%Y')
last_update_date = df['Last_update'].max()  
formatted_date = last_update_date.strftime('%d %B %Y')  

st.write(f'''
# French Merger Case Tracker
This is an automated overview of the French merger control! Stay informed about case developments by exploring the tables below. Click on the URL for direct access to the authority's webpage.
 
 
Last updated: {formatted_date} (source: [FR](https://www.autoritedelaconcurrence.fr/fr/liste-de-controle-des-concentrations)) | Contact: [Joost Dibbits](mailto:joost.dibbits@linklaters.com) or [Ananya Goyal](mailto:ananya.goyal@linklaters.com)
***
''')
#####
df['sens_decision_date'] = pd.to_datetime(df['sens_decision_date'], errors='coerce')
st.sidebar.header('User input features')
st.sidebar.header('Sector')

st.sidebar.caption("Enter keywords or select sectors from the box below. The tables and the graph on the main page will filter the cases based on the sector.")
sector_list = pd.concat([df['Sector 1'], df['Sector 2'], df['Sector 3']]).dropna().unique()
sector_list = sorted(sector_list)

mask_dex_cases = df['Title'].str.contains('DEX', case=False, na=False)
df.loc[mask_dex_cases, 'Phase'] = 'Phase 1'
df.loc[mask_dex_cases, 'Dispositif'] = 'Referred to P2'
# Multiselect widget for sectors
selected_sectors = st.sidebar.multiselect(
    'Sector',
    options=sector_list, 
    default=[],
    placeholder="Enter keywords"
)

# Filter DataFrame based on selected sectors from any of the three columns
if selected_sectors:
    mask = df['Sector 1'].isin(selected_sectors) | df['Sector 2'].isin(selected_sectors) | df['Sector 3'].isin(selected_sectors)
    df = df[mask]

st.sidebar.header('Parties')
st.sidebar.caption("Enter party names in search box below. The tables on the main page and the graph will show all cases pertaining to the party.")
nace_categories = df['parties_concerne'].dropna().unique().tolist()
search_term = st.sidebar.text_input('Search', placeholder='Enter party names') 
if search_term:
    search_terms = search_term.split() 
    search_regex = '|'.join(search_terms)  
    df = df[df['parties_concerne'].str.contains(search_regex, case=False, na=False)]

df_ongoing = df[df['Ongoing'] == 'Yes']
if df_ongoing.empty:
      st.write("There are no ongoing cases")
else:
    grouped_data_combined = df_ongoing.groupby('Phase').size().reset_index(name='Cases')
    
    grouped_data_combined['Phase'] = pd.Categorical(grouped_data_combined['Phase'], categories=['Phase 1', 'Phase 2'], ordered=True)
    
    max_value = int(grouped_data_combined['Cases'].max())
    whole_numbers = list(range(max_value + 5))
    
    chart_combined = alt.Chart(grouped_data_combined).mark_bar(size=20).encode(
        y=alt.Y('Phase:O', axis=alt.Axis(title='')),
        x=alt.X('Cases:Q', axis=alt.Axis(title='', values=whole_numbers, format='.0f')),
        color=alt.Color('Phase:O', legend=None, scale=alt.Scale(
            domain=['Phase 1', 'Phase 2'],
            range=['green', 'red']
        ))
    ).properties(width=500, height=200)
    
    
    #st.subheader('Ongoing cases')
    #st.altair_chart(chart_combined, use_container_width=True)

st.caption('Please select one of the following tabs:')
tabs = st.tabs(["**Phase 1**", "**Phase 1 simplified**","**Phase 2**"])

with tabs[0]:

    st.subheader('Phase 1')
    st.subheader('Ongoing cases')

    df2 = df[(df['Phase'] == 'Phase 1') & (df['Ongoing'] == 'Yes')]
    if df2.empty:
      st.write("There are no ongoing non-simplified P1 cases")
    else:
      df2 = df2.rename(columns={'parties_concerne': 'Parties', 'Notification_date': 'Notification', 'Page URL': '', 'days': 'Days', 'Renvoi': 'Referral'})
      df2['Notification'] = pd.to_datetime(df2['Notification'])
      df2 = df2.sort_values(by='Notification', ascending=False)
      df2['Notification'] = df2['Notification'].dt.strftime('%d/%m/%Y')
      df2.set_index('', inplace=True) 
      df2 = df2[['Parties','Notification','Days', 'Referral']] 
      st.data_editor(
      pd.DataFrame(df2),
        column_config={
          "Parties": st.column_config.Column(width="medium"),
          "Days": st.column_config.Column(help="Calendar days"),
          "": st.column_config.LinkColumn(
            display_text= 'URL',
            validate= 'URL'
          )  
        }
      )
    
    st.caption('The ongoing cases also include simplified cases')
####
    st.subheader('Latest published decisions')

    df2 = df[(df['Phase'] == 'Phase 1') & (df['simplified'] != 'yes')]
    df2 = df2.dropna(subset=['Decision_Link'])
    if df2.empty:
        st.write("There are no non-simplified P1 published decisions")
    else:
        df2 = df2.rename(columns={'Title': 'Case', 'decision_date': 'Publication', 'Link': '', 'parties_concerne': 'Parties', 'Decision_Link': 'Text', 'Dispositif': 'Decision'})
        df2['Publication'] = pd.to_datetime(df2['Publication'])
        df2 = df2.dropna(subset=['Text'])
        df2 = df2.sort_values(by='Publication', ascending=False)
        df2['Publication'] = df2['Publication'].dt.strftime('%d/%m/%Y')

        df2 = df2.head(7)
        df2.set_index('', inplace=True) 
        df2 = df2[['Case','Parties','Publication', 'Decision', 'Text']] 

        st.data_editor(
            pd.DataFrame(df2),
            column_config={
                "Parties": st.column_config.Column(width="medium"),
                "": st.column_config.LinkColumn(
                    display_text= 'URL',
                    validate= 'URL'
                ),
                "Text": st.column_config.LinkColumn(
                    display_text= 'URL',
                    validate= 'URL'
                )  
            }
        )

####
    st.subheader('Latest decisions')

    df2 = df[(df['Phase'] == 'Phase 1') & (df['simplified'] != 'yes')]
    df2 = df2.dropna(subset=['Dispositif'])
    if df2.empty:
        st.write("There are no non-simplified P1 decisions")
    else:
        df2 = df2.rename(columns={'Title': 'Case', 'sens_decision_date': 'Date', 'Link': '', 'parties_concerne': 'Parties', 'Dispositif': 'Decision'})
        df2['Date'] = pd.to_datetime(df2['Date'])
        df2 = df2.sort_values(by='Date', ascending=False)
        df2['Date'] = df2['Date'].dt.strftime('%d/%m/%Y')

        df2 = df2.head(7)
        df2.set_index('', inplace=True) 
        df2 = df2[['Case','Parties','Date', 'Decision']] 

        st.data_editor(
            pd.DataFrame(df2),
            column_config={
                "Parties": st.column_config.Column(width="medium"),
                "": st.column_config.LinkColumn(
                    display_text= 'URL',
                    validate= 'URL'
                )  
            }
        )
#####
with tabs[1]:
    st.subheader('Phase 1 simplified')

    st.subheader('Latest published decisions')

    df2 = df[(df['Phase'] == 'Phase 1') & (df['simplified'] != 'no')]
    df2 = df2.dropna(subset=['Decision_Link'])
    if df2.empty:
        st.write("There are no simplified P1 published decisions")
    else:
        df2 = df2.rename(columns={'Title': 'Case', 'decision_date': 'Publication', 'Link': '', 'parties_concerne': 'Parties', 'Decision_Link': 'Text',  'Dispositif': 'Decision'})
        df2['Publication'] = pd.to_datetime(df2['Publication'])
        df2 = df2.dropna(subset=['Text'])
        df2 = df2.sort_values(by='Publication', ascending=False)
        df2['Publication'] = df2['Publication'].dt.strftime('%d/%m/%Y')

        df2 = df2.head(7)
        df2.set_index('', inplace=True) 
        df2 = df2[['Case','Parties','Publication', 'Decision', 'Text']] 

        st.data_editor(
            pd.DataFrame(df2),
            column_config={
                "Parties": st.column_config.Column(width="medium"),
                "": st.column_config.LinkColumn(
                    display_text= 'URL',
                    validate= 'URL'
                ),
                "Text": st.column_config.LinkColumn(
                    display_text= 'URL',
                    validate= 'URL'
                )  
            }
        )
####
    st.subheader('Latest decisions')

    df2 = df[(df['Phase'] == 'Phase 1') & (df['simplified'] != 'no')]
    df2 = df2.dropna(subset=['Dispositif'])
    if df2.empty:
      st.write("There are no simplified P1 decisions")
    else:
      df2 = df2.rename(columns={'Title': 'Case', 'sens_decision_date': 'Date', 'Link': '', 'parties_concerne': 'Parties', 'Dispositif': 'Decision'})
      df2['Date'] = pd.to_datetime(df2['Date'])
      df2 = df2.sort_values(by='Date', ascending=False)
      df2['Date'] = df2['Date'].dt.strftime('%d/%m/%Y')
      df2 = df2.head(7)
      df2.set_index('', inplace=True) 
      df2 = df2[['Case','Parties','Date', 'Decision']] 

      st.data_editor(
      pd.DataFrame(df2),
        column_config={
          "Parties": st.column_config.Column(width="medium"),
          "": st.column_config.LinkColumn(
            display_text= 'URL',
            validate= 'URL'
          )  
        }
      )
#####

with tabs[2]:
    st.subheader('Phase 2')
    st.subheader('Ongoing cases')

    df2 = df[(df['Phase'] == 'Phase 2') & (df['Ongoing'] == 'Yes')]
    if df2.empty:
      st.write("There are no ongoing P2 cases")
    else:
      df2 = df2.rename(columns={'parties_concerne': 'Parties', 'Notification_date': 'Notification', 'Page URL': '', 'days': 'Days', 'Renvoi': 'Referral'})
      df2['Notification'] = pd.to_datetime(df2['Notification'])
      df2 = df2.sort_values(by='Notification', ascending=False)
      df2['Notification'] = df2['Notification'].dt.strftime('%d/%m/%Y')
      df2.set_index('', inplace=True) 
      df2 = df2[['Parties','Notification','Days', 'Renvoi']] 
      st.data_editor(
      pd.DataFrame(df2),
        column_config={
          "Parties": st.column_config.Column(width="medium"),
          "": st.column_config.LinkColumn(
            display_text= 'URL',
            validate= 'URL'
          )  
        }
      )
    ######
    st.subheader('Latest published decisions')

    df2 = df[(df['Phase'] == 'Phase 2')]
    if df2.empty:
        st.write("There are no P2 published decisions")
    else:
        df2 = df2.rename(columns={'Title': 'Case', 'decision_date': 'Publication', 'Link': '', 'parties_concerne': 'Parties', 'Decision_Link': 'Text',  'Dispositif': 'Decision'})
        df2['Publication'] = pd.to_datetime(df2['Publication'])
        df2 = df2.dropna(subset=['Text'])
        df2 = df2.sort_values(by='Publication', ascending=False)
        df2['Publication'] = df2['Publication'].dt.strftime('%d/%m/%Y')

        df2 = df2.head(7)
        df2.set_index('', inplace=True) 
        df2 = df2[['Case','Parties','Publication', 'Decision', 'Text']] 

        st.data_editor(
            pd.DataFrame(df2),
            column_config={
                "Parties": st.column_config.Column(width="medium"),
                "": st.column_config.LinkColumn(
                    display_text= 'URL',
                    validate= 'URL'
                ),
                "Text": st.column_config.LinkColumn(
                    display_text= 'URL',
                    validate= 'URL'
                )  
            }
        )
    ######
    st.subheader('Latest decisions')

    df2 = df[(df['Phase'] == 'Phase 2')]
    if df2.empty:
      st.write("There are no P2 decisions")
    else:
      df2 = df2.rename(columns={'Title': 'Case', 'sens_decision_date': 'Date', 'Link': '', 'parties_concerne': 'Parties','Dispositif': 'Decision'})
      df2['Date'] = pd.to_datetime(df2['Date'])
      df2 = df2.sort_values(by='Date', ascending=False)
      df2['Date'] = df2['Date'].dt.strftime('%d/%m/%Y')
      df2 = df2.head(7)
      df2.set_index('', inplace=True) 
      df2 = df2[['Case','Parties','Date', 'Decision']] 
      st.data_editor(
      pd.DataFrame(df2),
        column_config={
          "Parties": st.column_config.Column(width="medium"),
          "": st.column_config.LinkColumn(
            display_text= 'URL',
            validate= 'URL'
          )  
        }
      )
