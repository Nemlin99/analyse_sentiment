import streamlit as st
import pandas as pd
import json
from PIL import Image
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Analyse des Ressentis clients sur les RS", layout="wide")

# ----------- MENU --------
st.sidebar.title("📚 Navigation")
page = st.sidebar.radio("Aller à", [
    "🏠 Accueil",
    "📈 Statistiques Générales",
    "📊 Visualisation",
    "🔍 Analyse par produits",
    "📝 Posts"
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

# ----------- PAGE ACCUEIL -----------
if page == "🏠 Accueil":
    st.title("📊 Analyse des ressentis clients sur les réseaux sociaux")
    st.markdown("""
Bienvenue dans votre tableau de bord d'analyse de l'image de marque sur les réseaux sociaux(Facebook).
Utilisez le menu à gauche pour explorer :
- Les KPIs sentimentaux
- L’analyse des sentiments par produits
- Les posts récents sur les réseaux sociaux
""")

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
        st.subheader("📌 Statistiques globales par source")
        total_counts = df.groupby('source').size()
        pos_counts = df[df['sentiment'] == 'POSITIVE'].groupby('source').size()
        neg_counts = df[df['sentiment'] == 'NEGATIVE'].groupby('source').size()

        for source in total_counts.index:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(f"{source} - Total", f"{total_counts[source]}")
            col2.metric(f"{source} - Positifs", f"{pos_counts.get(source, 0)}")
            col3.metric(f"{source} - Négatifs", f"{neg_counts.get(source, 0)}")

        # Calcul des ratios
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

        st.subheader("📊 Moyenne des commentaires par Banque")
        for source in avg_comments.index:
            col1, col2, col3 = st.columns(3)
            col1.metric(f"{source} - /jour", f"{avg_comments[source]}")
            col2.metric(f"{source} - Négatifs /jour", f"{avg_neg.get(source, 0)}")
            col3.metric(f"{source} - % Négatifs", f"{neg_ratio.get(source, 0)}%")



    else:
        st.warning("Aucune donnée chargée.")

# ----------- PAGE VISUALISATION GLOBALE -----------
elif page == "📊 Visualisation":
    st.title("📊 Visualisation des ressentis clients")
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

        st.subheader("📉 Commentaires totaux par source et jour")
        tot_count = df.groupby(['date', 'source']).size().reset_index(name='tot_count')
        fig_tot = px.bar(tot_count, x='date', y='tot_count', color='source', barmode='group')
        st.plotly_chart(fig_tot, use_container_width=True)
        detra = daily_neg_counts / daily_counts.replace(0, np.nan)
        promo = 1 - detra
        nps = promo - detra

        st.subheader("📉 Évolution du proxy NPS")
        nps_reset = nps.reset_index().melt(id_vars='date', var_name='source', value_name='NPS').dropna()
        fig_nps = px.line(nps_reset, x='date', y='NPS', color='source')
        st.plotly_chart(fig_nps, use_container_width=True)

    if not absa_df.empty:
        # fig = px.histogram(absa_df, x="sentiment", color="sentiment", title="Distribution des sentiments")
        # st.plotly_chart(fig)
        # st.dataframe(absa_df[['phrase', 'source', 'sentiment']])

        fig = px.bar(
    absa_grouped,
    x="aspect",
    y="count",
    color="sentiment",
    facet_col="source",
    barmode="group",
    title="Comparaison des ressentis clients par aspect et par source",
    color_discrete_map={
        "negatif": "red",
        "neutre": "lightblue",
        "positif": "green"
    }
)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("☁️ Nuage de mots des commentaires")
    st.image(wordcloud_img, use_column_width=True)

# ----------- PAGE ABSA -----------
elif page == "🔍 Analyse par produits":
    st.title("🔍 Analyse des resentis clients par produits et par banques")

    #absa_grouped = absa_df.groupby(['source', 'aspect', 'sentiment']).size().reset_index(name='count')

    if not absa_df.empty:
        st.subheader("🔍 Filtrer les commentaires")

    # Interface de filtre
        col1, col2, col3 = st.columns(3)
        with col1:
            source_filter = st.selectbox("Source", ["Toutes"] + sorted(absa_df['source'].unique()), key="filt_source")
        with col2:
            aspect_filter = st.selectbox("Aspect", ["Tous"] + sorted(absa_df['aspect'].unique()), key="filt_aspect")
        with col3:
            sentiment_filter = st.selectbox("Sentiment", ["Tous", "positif", "negatif"], key="filt_sentiment")

    # Application des filtres (en mémoire uniquement)
        filtered_df = absa_df.copy()
        if source_filter != "Toutes":
            filtered_df = filtered_df[filtered_df['source'] == source_filter]
        if aspect_filter != "Tous":
            filtered_df = filtered_df[filtered_df['aspect'] == aspect_filter]
        if sentiment_filter != "Tous":
            filtered_df = filtered_df[filtered_df['sentiment'] == sentiment_filter]

    # Partie dynamique uniquement ici
        st.subheader("📝 Commentaires filtrés")
        st.dataframe(filtered_df, use_container_width=True)

# ----------- PAGE POSTS -----------
elif page == "📝 Posts":
    st.title("📝 Posts récents sur la SGCI dans le groupe Observatoire Libre des Banques")
    if not df_postes.empty:
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