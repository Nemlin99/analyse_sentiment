
import streamlit as st
import pandas as pd
import json
from PIL import Image
import plotly.express as px
import numpy as np
from datetime import datetime
from streamlit_plotly_events import plotly_events
import base64

st.set_page_config(page_title="Analyse des Ressentis clients sur les RS", layout="wide")

# ----------- MENU --------
st.sidebar.title("📚 Navigation")
page = st.sidebar.radio("Aller à", [
    "🏠 Accueil",
    "📈 Statistiques Générales",
    "📊 Visualisations",
    "🔍 Détails des commentaires",
    "📝 Posts divers sur nos produits/services"
])

# ----------- CHARGEMENT DES DONNÉES -----------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("resultats_sentiments.csv")
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df.dropna(subset=['date'], inplace=True)
    except:
        df = pd.DataFrame()
    try:
        with open("kpis.json") as f:
            kpis = json.load(f)
    except:
        kpis = {}
    try:
        absa_df = pd.read_csv("absa_df.csv")
    except:
        absa_df = pd.DataFrame()
    try:
        df_postes = pd.read_csv("postes.csv")
    except:
        df_postes = pd.DataFrame()
    try:
        wordcloud_img = Image.open("wordcloud.png")
    except:
        wordcloud_img = Image.open("wordcloud.png")
    return df, kpis, absa_df, df_postes,wordcloud_img

df, kpis, absa_df, df_postes,wordcloud_img = load_data()
df, kpis, absa_df, df_postes,wordcloud_img = load_data()
# df = df[
#     (df['date'].dt.date >= datetime(2025, 1, 1).date()) &
#     (df['date'].dt.date <= datetime(2025, 6, 30).date())
# ]
# ----------- PAGE ACCUEIL -----------
if page == "🏠 Accueil":
    col1, col2 = st.columns([2, 6])
    with col1:
        st.image("logo.png", width=200)  # Mets ton propre logo
    with col2:
        st.title("Analyse du Ressenti des Clients sur les Réseaux Sociaux")

    st.markdown("""
Bienvenue dans votre tableau de bord d'analyse de l'image de marque sur les réseaux sociaux(Facebook).
Utilisez le menu à gauche pour explorer :
- Les Statistiques Générales et la visulisation de différents KPIs
- L’analyse des sentiments par produits
- Les posts récents sur les réseaux sociaux
""")
    
    # def get_base64_image(image_path):
    #     with open(image_path, "rb") as f:
    #         data=f.read()
    #     return base64.b64encode(data).decode("utf-8")
    
    # logo = get_base64_image("qr_code_lien.png")
    # st.markdown(f"""
    #             <div style="texte-align: center; margin-top: 40px;">
    #                 <img src="data:image/png;base64,{logo}" width="200">
    #             </div>
    #             """, unsafe_allow_html=True
    #             )

# ----------- PAGE DASHBOARD SENTIMENTS -----------
elif page == "📈 Statistiques Générales":

    st.title("📈 Statistiques Générales")

    if not df.empty:
        sources = df['source'].unique().tolist()
        source_select = st.sidebar.multiselect("Filtrer par source :", options=sources, default=sources)
        df = df[df['source'].isin(source_select)]

        st.sidebar.write("### Filtrer par date")
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        start_date = st.sidebar.date_input("Date de début", min_date)
        end_date = st.sidebar.date_input("Date de fin", max_date)
        df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]

        # Métriques globales
        st.subheader("📌 Analyse Concurrentielle Digitale: Statistiques Globales")
            # Calcul des ratios
        total_counts = df.groupby('source').size()
        pos_counts = df[df['sentiment'] == 'POSITIVE'].groupby('source').size()
        neg_counts = df[df['sentiment'] == 'NEGATIVE'].groupby('source').size()
        all_dates = pd.date_range(start=df['date'].min().date(), end=df['date'].max().date(), freq='D')
        multi_index = pd.MultiIndex.from_product([all_dates, df['source'].unique()], names=['date', 'source'])
        daily_counts = df.groupby([df['date'].dt.date, 'source']).size().reindex(multi_index, fill_value=0).unstack()
        daily_neg_counts = df[df['sentiment'] == 'NEGATIVE'].groupby([df['date'].dt.date, 'source']).size().reindex(multi_index, fill_value=0).unstack()

        detra = daily_neg_counts / daily_counts.replace(0, np.nan)
        promo = 1 - detra
        nps = promo - detra

        avg_comments = round(daily_counts.mean(), 2)
        avg_neg = round(daily_neg_counts.mean(), 2)
        neg_ratio = round((avg_neg / avg_comments * 100).fillna(0), 2)

        for source in total_counts.index:
            col1, col2, col3, col4,col5,col6 = st.columns(6)
            col1.metric(f"{source} - Total", f"{total_counts[source]}")
            col2.metric(" - 😍😊💕", f"{pos_counts.get(source, 0)}")
            col3.metric(" - 🤬😡🥵", f"{neg_counts.get(source, 0)}")
            col4.metric(" % Négatifs", f"{neg_ratio.get(source, 0)}%")
            col5.metric("Moy./jour", f"{avg_comments[source]}")
            col6.metric(" Moy.Négatifs/jour", f"{avg_neg.get(source, 0)}")



        # st.subheader("📊 Moyenne des commentaires par Banque")
        # for source in avg_comments.index:
        #     col1, col2, col3 = st.columns(3)
        #     col1.metric(f"{source} - /jour", f"{avg_comments[source]}")
        #     col2.metric(f"{source} - Négatifs /jour", f"{avg_neg.get(source, 0)}")
            



    else:
        st.warning("Aucune donnée chargée.")

# ----------- PAGE VISUALISATION GLOBALE -----------
elif page == "📊 Visualisations":
    st.title("📊 Visualisations du ressenti des clients")
    absa_grouped = absa_df.groupby(['source', 'aspect', 'sentiment']).size().reset_index(name='count')

    if not df.empty:
        sources = df['source'].unique().tolist()
        source_select = st.sidebar.multiselect("Filtrer par source :", options=sources, default=sources)
        df = df[df['source'].isin(source_select)]

        st.sidebar.write("### Filtrer par date")
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        start_date = st.sidebar.date_input("Date de début", min_date)
        end_date = st.sidebar.date_input("Date de fin", max_date)
        df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]
       # Calcul des ratios
        all_dates = pd.date_range(start=df['date'].min().date(), end=df['date'].max().date(), freq='D')
        multi_index = pd.MultiIndex.from_product([all_dates, df['source'].unique()], names=['date', 'source'])
        daily_counts = df.groupby([df['date'].dt.date, 'source']).size().reindex(multi_index, fill_value=0).unstack()
        daily_neg_counts = df[df['sentiment'] == 'NEGATIVE'].groupby([df['date'].dt.date, 'source']).size().reindex(multi_index, fill_value=0).unstack()

        # st.subheader("📉 Commentaires totaux par source et jour")
        # couleurs_fixes = {"NEGATIVE": "red","POSITIVE": "green"}
        # tot_count = df[df['source']=="page_sgci"].groupby(['date', 'sentiment']).size().reset_index(name='tot_count')
        # fig_tot = px.bar(tot_count, x='date', y='tot_count', color='sentiment',color_discrete_map=couleurs_fixes, barmode='group')
        # st.plotly_chart(fig_tot, use_container_width=True)
        detra = daily_neg_counts / daily_counts.replace(0, np.nan)
        promo = 1 - detra
        nps = promo - detra


# Couleurs fixes
        

        st.subheader("📉 Ressenti des clients au cours du temps- Page-SGCI")
        couleurs_fixes = {"negatif": "red", "positif": "green"}

# Données agrégées
        tot_count = absa_df[absa_df['source'] == "page_sgci"].groupby(['date', 'sentiment']).size().reset_index(name='tot_count')

# Premier graphique : sentiment par date
        fig_tot = px.bar(
                tot_count,
                x='date',
                y='tot_count',
                color='sentiment',
                color_discrete_map=couleurs_fixes,
                barmode='group'
                )

# Récupère les clics utilisateur
        selected_points = plotly_events(fig_tot, click_event=True, select_event=False)

# Affiche le premier graphique
        #st.plotly_chart(fig_tot, use_container_width=True)

# Deuxième graphique : aspects pour la date sélectionnée
        if selected_points:
            selected_date = selected_points[0]['x']  # x = date cliquée
            st.info(f"📅 Date sélectionnée : {selected_date}")
            absa_df_sgci = absa_df[absa_df['source'] == "page_sgci"]

    # Filtrage dans absa_df
            filtered_absa = absa_df_sgci[absa_df_sgci['date'] == selected_date]

            if filtered_absa.empty:
                st.warning("Aucun commentaire trouvé pour cette date dans absa_df.")
            else:
        # Regrouper par aspect
                aspect_count = filtered_absa.groupby('aspect').size().reset_index(name='nb_commentaires')

                fig_aspects = px.bar(
            aspect_count,
            x='aspect',
            y='nb_commentaires',
            color='aspect',
            title=f"Commentaires par aspect le {selected_date}"
        )

                st.plotly_chart(fig_aspects, use_container_width=True)

        st.subheader("📉 Évolution du proxy NPS")
        nps_reset = nps.reset_index().melt(id_vars='date', var_name='source', value_name='NPS').dropna()
        fig_nps = px.line(nps_reset, x='date', y='NPS', color='source')
        st.plotly_chart(fig_nps, use_container_width=True)

    if not absa_df.empty:
        # fig = px.histogram(absa_df, x="sentiment", color="sentiment", title="Distribution des sentiments")
        # st.plotly_chart(fig)
        # st.dataframe(absa_df[['phrase', 'source', 'sentiment']])

        # sources = absa_grouped['source'].unique()

        # for src in sources:
        subset = absa_grouped[absa_grouped['source'] == "page_sgci"]

        fig = px.bar(
        subset,
        x="aspect",
        y="count",
        color="sentiment",
        barmode="group",
        title=f"Ressentis clients - Source : page_sgci",
        color_discrete_map={
            "negatif": "red",
            "neutre": "lightblue",
            "positif": "green"
        },
        width=800,
        height=500
    )
    st.plotly_chart(fig, use_container_width=False)

    aspects = absa_grouped['aspect'].unique()

    for asp in aspects:
        subset1 = absa_grouped[absa_grouped['aspect'] == asp]

        fig1 = px.bar(
        subset1,
        x="source",
        y="count",
        color="sentiment",
        barmode="group",
        title=f"Ressentis clients - Aspect : {asp}",
        color_discrete_map={
            "negatif": "red",
            "positif": "green"
        },
        width=800,
        height=500
    )
        st.plotly_chart(fig1, use_container_width=False)

    st.subheader("☁️ Nuage de mots des commentaires")
    st.image(wordcloud_img, use_column_width=True)

# ----------- PAGE ABSA -----------
elif page == "🔍 Détails des commentaires":
    st.title("🔍 Exploration des commentaires")

    #absa_grouped = absa_df.groupby(['source', 'aspect', 'sentiment']).size().reset_index(name='count')

    if not absa_df.empty:
        st.subheader("🔍 Filtrer les commentaires")

    # Interface de filtre
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            date_filter = st.selectbox("Date", ["Toutes"] + sorted(absa_df['date'].unique()), key="filt_date")
        with col2:
            source_filter = st.selectbox("Source", ["Toutes"] + sorted(absa_df['source'].unique()), key="filt_source")
        with col3:
            aspect_filter = st.selectbox("Aspect", ["Tous"] + sorted(absa_df['aspect'].unique()), key="filt_aspect")
        with col4:
            sentiment_filter = st.selectbox("Sentiment", ["Tous", "positif", "negatif"], key="filt_sentiment")

    # Application des filtres (en mémoire uniquement)
        filtered_df = absa_df.copy()
        if source_filter != "Toutes":
            filtered_df = filtered_df[filtered_df['source'] == source_filter]
        if aspect_filter != "Tous":
            filtered_df = filtered_df[filtered_df['aspect'] == aspect_filter]
        if sentiment_filter != "Tous":
            filtered_df = filtered_df[filtered_df['sentiment'] == sentiment_filter]
        if date_filter != "Toutes":
            filtered_df = filtered_df[filtered_df["date"] == date_filter]


    # Partie dynamique uniquement ici
        st.subheader("📝 Commentaires filtrés")
        st.dataframe(filtered_df[["source","date","phrase","aspect"]], use_container_width=True)

# ----------- PAGE POSTS -----------
elif page == "📝 Posts divers sur nos produits/services":
    st.title("📝 Posts récents sur la SGCI dans le groupe Observatoire Libre des Banques")
    if not df_postes.empty:
        #df_postes['date'] = pd.to_datetime(df_postes['date'], errors='coerce')

        # 2. Suppression des lignes avec dates invalides
        df_postes = df_postes.dropna(subset=['date'])
        for source in df_postes['source'].unique():
            st.subheader(f"📢 {source}")
            posts = df_postes[df_postes['source'] == source].groupby('poste').first().reset_index()
            for _, row in posts.iterrows():
                st.markdown(f"** {row['date']}📝 Post :** {row['poste']}")
                coms = df_postes[(df_postes['source'] == source) & (df_postes['poste'] == row['poste'])]
                st.write("💬 Commentaires associés :")
                st.dataframe(coms[['date', 'commentaire']])
    else:
        st.warning("Aucun post trouvé.")