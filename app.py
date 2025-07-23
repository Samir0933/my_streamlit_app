import streamlit as st

# Base packages
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# Plot interactive maps
import geopandas as gpd
from shapely import wkt
import json
import os


st.header("COVID-19 au Sénégal 🇸🇳")

st.sidebar.markdown("*Dernière mise à jour: 13/05/2025*")
st.sidebar.markdown("---")
st.sidebar.header("Ressources utiles")

st.sidebar.markdown("Numéro d'urgence 1: **78 172 10 81**")

# I. Dataframe

df = pd.read_csv("https://raw.githubusercontent.com/maelfabien/COVID-19-Senegal/master/COVID_Senegal.csv", sep=";")
df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%y')

# II. Summary of the number of cases
st.markdown("---")

evol_cases = df[['Date', 'Positif', 'Negatif', 'Décédé', 'Guéri']].groupby("Date").sum().cumsum()

st.subheader("En bref")

total_positif = evol_cases.tail(1)['Positif'].iloc[0]
total_negatif = evol_cases.tail(1)['Negatif'].iloc[0]
total_decede = evol_cases.tail(1)['Décédé'].iloc[0]
total_geuri = evol_cases.tail(1)['Guéri'].iloc[0]

# Define the card template
card_template = """
<div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; min-height: 120px;'>
    <h3 style='color: #262730; margin: 0 0 15px 0; font-size: 16px;'>{title}</h3>
    <p style='font-size: 24px; color: {value_color}; font-weight: bold; margin: 0 0 5px 0;'>{value}</p>
    {subtitle}
</div>
"""

# Create a container for the cards
with st.container():
    # Create 4 columns for the cards with more spacing
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="large")
    
    # Card 1: Active Cases
    with col1:
        st.markdown(card_template.format(
            title="Cas Actifs",
            value=total_positif - total_geuri,
            value_color="#FF4B4B",
            subtitle=""
        ), unsafe_allow_html=True)
    
    # Card 2: Deaths
    with col2:
        st.markdown(card_template.format(
            title="Décès",
            value=total_decede,
            value_color="#262730",
            subtitle=""
        ), unsafe_allow_html=True)
    
    # Card 3: Recovered
    with col3:
        st.markdown(card_template.format(
            title="Guérisons",
            value=total_geuri,
            value_color="#00CC96",
            subtitle=""
        ), unsafe_allow_html=True)
    
    # Card 4: Total Cases
    with col4:
        st.markdown(card_template.format(
            title="Total Cas",
            value=total_positif,
            value_color="#FF4B4B",
            subtitle=""
        ), unsafe_allow_html=True)

# Add some vertical spacing between rows
st.markdown("<br>", unsafe_allow_html=True)

# Additional metrics in a second row
col5, col6, col7, col8 = st.columns([1, 1, 1, 1], gap="large")

# Card 5: Growth Rate
with col5:
    growth_rate = np.round(pd.DataFrame(np.sqrt(evol_cases['Positif'].pct_change(periods=2)+1)-1).tail(1)['Positif'].iloc[0] * 100, 2)
    st.markdown(card_template.format(
        title="Taux de Croissance",
        value=f"{growth_rate}%",
        value_color="#FF4B4B",
        subtitle=""
    ), unsafe_allow_html=True)

# Card 6: Negative Tests
with col6:
    st.markdown(card_template.format(
        title="Tests Négatifs",
        value=total_negatif,
        value_color="#00CC96",
        subtitle=""
    ), unsafe_allow_html=True)

# Card 7: Total Tests
with col7:
    st.markdown(card_template.format(
        title="Total Tests",
        value=total_positif + total_negatif,
        value_color="#262730",
        subtitle=""
    ), unsafe_allow_html=True)

# Card 8: Positive Test Rate
with col8:
    positive_rate = np.round(total_positif / (total_positif + total_negatif) * 100, 1)
    st.markdown(card_template.format(
        title="Taux de Tests Positifs",
        value=f"{positive_rate}%",
        value_color="#FF4B4B",
        subtitle=""
    ), unsafe_allow_html=True)

# III. Interactive map
st.markdown("---")
st.subheader("Carte des cas positifs")

# Create a simple map without the shapefile since it's not available
fig = go.Figure()

# Add points for cities
summary = df[['Positif', 'Ville']].groupby("Ville").sum().reset_index()

# Create a simple scatter plot instead of a map
fig.add_trace(go.Scatter(
    x=summary['Ville'],
    y=summary['Positif'],
    mode='markers',
    marker=dict(
        size=15,
        color='red',
    ),
    text=summary['Ville'] + ': ' + summary['Positif'].astype(str) + ' cas',
    name='Cas positifs'
))

fig.update_layout(
    height=550,
    width=700,
    title="Nombre de cas par ville",
    xaxis_title="Ville",
    yaxis_title="Nombre de cas positifs"
)

st.plotly_chart(fig)

# IV. Evolution of the number of cases in Senegal
st.markdown("---")
st.subheader("Evolution du nombre de cas positifs au Sénégal")

st.write("La courbe 'Positif' représente l'ensemble des cas, et la courbe 'Actifs' élimine les cas guéris et représente le nombre de cas actifs.")
evol_cases['Actifs'] = evol_cases['Positif'] - evol_cases['Guéri']

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=evol_cases.index,
    y=evol_cases['Positif'],
    name='Positif',
    mode='lines+markers'
))
fig.add_trace(go.Scatter(
    x=evol_cases.index,
    y=evol_cases['Actifs'],
    name='Actifs',
    mode='lines+markers'
))

fig.update_layout(
    height=400,
    width=700,
    xaxis_title="Date",
    yaxis_title="Nombre de cas"
)

st.plotly_chart(fig)

# V. Source of infection
st.markdown("---")
st.subheader("Contamination")

st.write("Nous distinguon les cas importés (voyageurs en provenance de l'extérieur) des cas contact qui ont été en contact avec une personne malade. Les cas Communauté sont des cas dont les contacts directs ne peuvent être établis, et donc les plus dangereux.")

facteur = df[['Date', 'Facteur']].dropna()

# Calculate totals correctly
total_importe = len(facteur[facteur['Facteur'] == "Importé"])
total_contact = len(facteur[facteur['Facteur'] == "Contact"])
total_communaute = len(facteur[facteur['Facteur'] == "Communauté"])

st.write("Nombre total de cas importés: ", total_importe)
st.write("Nombre total de cas contact: ", total_contact)
st.write("Nombre total de cas communauté: ", total_communaute)

# Create cumulative counts for the time series
importe = facteur[facteur['Facteur'] == "Importé"].groupby("Date").size().cumsum().reset_index()
voyage = facteur[facteur['Facteur'] == "Contact"].groupby("Date").size().cumsum().reset_index()
communaute = facteur[facteur['Facteur'] == "Communauté"].groupby("Date").size().cumsum().reset_index()

importe.columns = ["Date", "Count"]
voyage.columns = ["Date", "Count"]
communaute.columns = ["Date", "Count"]

df_int = pd.merge(importe, voyage, left_on='Date', right_on='Date', how='outer', suffixes=('_importe', '_contact'))
df_int = pd.merge(df_int, communaute, left_on='Date', right_on='Date', how='outer')
df_int.columns = ["Date", "Importes", "Contact", "Communauté"]

df_int['Date'] = pd.to_datetime(df_int['Date'], format='%d.%m.%y')
df_int = df_int.sort_values("Date").ffill().fillna(0)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_int['Date'],
    y=df_int['Importes'],
    name='Importés',
    mode='lines'
))
fig.add_trace(go.Scatter(
    x=df_int['Date'],
    y=df_int['Contact'],
    name='Contact',
    mode='lines'
))
fig.add_trace(go.Scatter(
    x=df_int['Date'],
    y=df_int['Communauté'],
    name='Communauté',
    mode='lines'
))

fig.update_layout(
    height=500,
    width=700,
    xaxis_title="Date",
    yaxis_title="Nombre de cas"
)

st.plotly_chart(fig)

st.write("Les cas importés, ayant ensuite crée des cas contact, proviennent des pays suivants:")

fig = px.bar(
    df.dropna(subset=['Source/Voyage']),
    x='Source/Voyage',
    title="Provenance des malades"
)
fig.update_layout(height=300, width=700)
st.plotly_chart(fig)

# VI. Insights about the population
st.markdown("---")
st.subheader("Population touchée")
st.write("Les chiffres présentés ci-dessous tiennent compte des publication du Ministère de la Santé et de l'Action Sociale. Certaines données sont manquantes, et nous n'affichons que les valeurs connues à ce jour.")

st.write("1. L'age moyen des patients est de ", round(np.mean(df['Age'].dropna())), " ans")

fig = px.bar(
    df,
    x='Age',
    title="Age des patients"
)
fig.update_layout(height=300, width=700)
st.plotly_chart(fig)

st.write("2. La plupart des patients connus sont des hommes")

st.write(pd.DataFrame(df[['Homme', 'Femme']].dropna().sum()).transpose())

st.write("3. La plupart des cas sont concentrés à Dakar")

fig = px.bar(
    df.dropna(subset=['Ville']),
    x='Ville',
    title="Ville des cas"
)
fig.update_layout(height=300, width=700)
st.plotly_chart(fig)

st.write("4. La plupart des personnes malades résident au Sénégal")

st.write(df['Resident Senegal'].dropna().value_counts())

st.write("5. Le temps d'hospitalisation moyen pour le moment est de : ", np.mean(df['Temps Hospitalisation (j)'].dropna()), " jours")
