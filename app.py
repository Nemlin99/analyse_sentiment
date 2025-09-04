import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import numpy as np
import json
from PIL import Image
import base64
import datetime as dt
import subprocess

df_postes = pd.read_csv("postes.csv")
# ========================
# 1. Chargement des données
# ========================
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
        # Encodage en base64 pour affichage dans Dash
        import io
        buf = io.BytesIO()
        wordcloud_img.save(buf, format="PNG")
        wordcloud_base64 = base64.b64encode(buf.getvalue()).decode()
    except:
        wordcloud_base64 = None
    return df, kpis, absa_df, df_postes, wordcloud_base64

df, kpis, absa_df, df_postes, wordcloud_base64 = load_data()
df["date"] = pd.to_datetime(df["date"], errors="coerce")
absa_df["date"] = pd.to_datetime(absa_df["date"], errors="coerce")

# ========================
# 2. Fonction LLaMA
# ========================
def query_llama(prompt, model="llama3"):
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=30
        )
        output = result.stdout.decode("utf-8").strip()
        return output
    except Exception as e:
        return f"⚠️ Erreur LLaMA : {e}"

# ========================
# 3. Application Dash
# ========================
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# Menu principal
app.layout = html.Div([
    dcc.Tabs(id="tabs", value="home", children=[
        dcc.Tab(label="🏠 Accueil", value="home"),
        dcc.Tab(label="📈 Statistiques Générales", value="stats"),
        dcc.Tab(label="📊 Visualisations", value="viz"),
        dcc.Tab(label="🔍 Détails des commentaires", value="details"),
        dcc.Tab(label="📝 Posts divers", value="posts"),
    ]),
    html.Div(id="content")
])

# ========================
# 4. Callbacks pour pages
# ========================
@app.callback(
    Output("content", "children"),
    Input("tabs", "value")
)
def render_page(tab):
    global df_postes
    if tab == "home":
        return html.Div([
            html.Div([
                # Logo à gauche
                html.Div([
                    html.Img(src="assets/logo.png", style={"width": "200px"})
                ], style={"display": "inline-block", "verticalAlign": "top", "marginRight": "20px"}),

                # Titre à droite
                html.Div([
                    html.H1("🕷️ SpyMarketBank-SG")
                ], style={"display": "inline-block", "verticalAlign": "top"})
            ], style={"marginBottom": "20px"}),

            # Texte descriptif en dessous
            html.Div([
                html.P("Bienvenue dans notre thermomètre d'analyse de l'image de marque sur les réseaux sociaux (Facebook)."),
                html.P("Utilisez le menu à gauche pour explorer :"),
                html.Ul([
                    html.Li("Les Statistiques Générales et la visualisation de différents KPIs"),
                    html.Li("L’analyse des sentiments par produits"),
                    html.Li("Les posts récents sur les réseaux sociaux")
                ])
            ])
        ])

    elif tab == "stats":
        if df.empty:
            return html.Div("⚠️ Aucune donnée disponible.")

        # === Layout avec filtres interactifs ===
        return html.Div([
            html.H2("📈 Statistiques Générales"),

            html.Div([
                html.Label("Filtrer par source :"),
                dcc.Dropdown(
                    id="filtre-source",
                    options=[{"label": s, "value": s} for s in df["source"].unique()],
                    value=list(df["source"].unique()),  # sélectionne tout par défaut
                    multi=True
                ),
                html.Label("Filtrer par date :"),
                dcc.DatePickerRange(
                    id="filtre-date",
                    start_date=dt.date(2025, 1, 1),
                    end_date=df["date"].max().date()
                )
            ], style={"width": "40%", "margin": "20px"}),

            html.Div(id="stats-metrics", style={"display":"flex","flex-wrap":"wrap"})
        ])

    elif tab == "viz":
        if df.empty or absa_df.empty:
            return html.Div("⚠️ Pas de données pour les visualisations.")

        return html.Div([
            html.H2("📊 Visualisations du ressenti des clients"),

            html.Div([
                html.Label("Filtrer par source :"),
                dcc.Dropdown(
                    id="viz-filtre-source",
                    options=[{"label": s, "value": s} for s in absa_df["source"].unique()],
                    value=list(absa_df["source"].unique()),
                    multi=True
                ),
                html.Label("Filtrer par date :"),
                dcc.DatePickerRange(
                    id="viz-filtre-date",
                    start_date=dt.date(2025, 1, 1),
                    end_date=df["date"].max().date()
                )
            ], style={"width": "40%", "margin": "20px"}),

            html.H3("📉 Évolution des sentiments"),
            dcc.Graph(id="viz-sentiments"),
            # Div vide pour le nouveau graphique créé au clic
            html.Div(id="nouveau-graphique"),

            html.H3("📉 Évolution du proxy NPS"),
            dcc.Graph(id="viz-nps"),

            html.H3("📊 Répartition des aspects par source"),
            dcc.Graph(id="viz-aspects"),

            html.H3("☁️ Nuage de mots"),
            html.Img(
                src="data:image/png;base64," + wordcloud_base64,
                style={"width": "50%", "border": "1px solid #ddd"}
            ) if wordcloud_base64 else "Pas d'image"
        ])

    elif tab == "details":
        absa_df["date"] = absa_df["date"].sort_values(ascending=False)
        if absa_df.empty:
            return html.Div("⚠️ Pas de commentaires disponibles.")

        return html.Div([
            html.H2("🔍 Exploration des commentaires"),

            html.H4("🔍 Filtrer les commentaires"),
            html.Div([
                # Date
                html.Div([
                    html.Label("Date"),
                    dcc.Dropdown(
                        id="details-date",
                        options=[{"label": "Toutes", "value": "Toutes"}] +
                                [{"label": d, "value": d} for d in sorted(absa_df['date'].unique())],
                        value="Toutes",
                        clearable=False,
                        style={"width": "100%"}
                    )
                ], style={"width": "24%", "display": "inline-block", "padding": "0 5px"}),

                # Source
                html.Div([
                    html.Label("Source"),
                    dcc.Dropdown(
                        id="details-source",
                        options=[{"label": "Toutes", "value": "Toutes"}] +
                                [{"label": s, "value": s} for s in sorted(absa_df['source'].unique())],
                        value="Toutes",
                        clearable=False,
                        style={"width": "100%"}
                    )
                ], style={"width": "24%", "display": "inline-block", "padding": "0 5px"}),

                # Aspect
                html.Div([
                    html.Label("Aspect"),
                    dcc.Dropdown(
                        id="details-aspect",
                        options=[{"label": "Tous", "value": "Tous"}] +
                                [{"label": a, "value": a} for a in sorted(absa_df['aspect'].unique())],
                        value="Tous",
                        clearable=False,
                        style={"width": "100%"}
                    )
                ], style={"width": "24%", "display": "inline-block", "padding": "0 5px"}),

                # Sentiment
                html.Div([
                    html.Label("Sentiment"),
                    dcc.Dropdown(
                        id="details-sentiment",
                        options=[
                            {"label": "Tous", "value": "Tous"},
                            {"label": "positif", "value": "positif"},
                            {"label": "negatif", "value": "negatif"}
                        ],
                        value="Tous",
                        clearable=False,
                        style={"width": "100%"}
                    )
                ], style={"width": "24%", "display": "inline-block", "padding": "0 5px"}),
            ], style={"margin-bottom": "20px"}),

            html.H4("📝 Commentaires filtrés"),
            dash_table.DataTable(
                id="details-table",
                columns=[{"name": i, "id": i} for i in absa_df[["date", "auteur", "phrase", "aspect"]].columns],
                page_size=10,
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "5px"},
            )
        ])

    elif tab == "posts":
        if df_postes.empty:
            return html.Div("⚠️ Aucun post trouvé.")

        # Préparer les dates
        df_postes['date_post'] = pd.to_datetime(df_postes['date_post'], errors='coerce').dt.date
        df_postes = df_postes.dropna(subset=['date_post'])

        content = [html.H2("📝 Posts récents sur la SGCI dans le groupe Observatoire Libre des Banques")]

        for source in df_postes['source'].unique():
            content.append(html.H3(f"📢 {source}"))

            posts = df_postes[df_postes['source'] == source].groupby('poste').first().reset_index()
            posts = posts.sort_values(by='date_post', ascending=False)

            for _, row in posts.iterrows():
                content.append(
                    html.Div([
                        html.P(f"**{row['date_post']} - Auteur: {row['auteur']} 📝 Post :** {row['poste']}", style={"fontWeight": "bold"}),
                    ], style={"marginBottom": "5px"})
                )

                coms = df_postes[(df_postes['source'] == source) & (df_postes['poste'] == row['poste'])]
                if not coms.empty:
                    content.append(html.P("💬 Commentaires associés :"))
                    content.append(
                        dash_table.DataTable(
                            data=coms[['date','auteur_com', 'commentaire']].to_dict("records"),
                            columns=[{"name": i, "id": i} for i in ['date','auteur_com', 'commentaire']],
                            page_size=5,
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "left", "padding": "5px"},
                        )
                    )
                else:
                    content.append(html.P("💬 Aucun commentaire associé.", style={"fontStyle": "italic"}))

                content.append(html.Hr())  # séparation entre posts

        return html.Div(content)

@app.callback(
    Output("stats-metrics", "children"),
    Input("filtre-source", "value"),
    Input("filtre-date", "start_date"),
    Input("filtre-date", "end_date")
)

def maj_stats(sources, start_date, end_date):
    if not sources:
        return [html.P("⚠️ Aucune source sélectionnée.")]

        # Filtrage
    dff = df[df["source"].isin(sources)]
    dff = dff[(dff["date"].dt.date >= pd.to_datetime(start_date).date()) &
                (dff["date"].dt.date <= pd.to_datetime(end_date).date())]

    if dff.empty:
            return [html.P("⚠️ Aucune donnée après filtrage.")]

        # Calculs
    total_counts = dff.groupby("source").size()
    pos_counts = dff[dff["sentiment"] == "POSITIVE"].groupby("source").size()
    neg_counts = dff[dff["sentiment"] == "NEGATIVE"].groupby("source").size()

    all_dates = pd.date_range(start=dff["date"].min().date(), end=dff["date"].max().date(), freq="D")
    multi_index = pd.MultiIndex.from_product([all_dates, dff["source"].unique()], names=["date", "source"])

    daily_counts = dff.groupby([dff["date"].dt.date, "source"]).size().reindex(multi_index, fill_value=0).unstack()
    daily_neg_counts = dff[dff["sentiment"] == "NEGATIVE"].groupby([dff["date"].dt.date, "source"]).size().reindex(multi_index, fill_value=0).unstack()

    avg_comments = round(daily_counts.mean(), 2)
    avg_neg = round(daily_neg_counts.mean(), 2)
    neg_ratio = round((avg_neg / avg_comments * 100).fillna(0), 2)

        # Affichage des métriques (cartes flexbox)
    metrics = []
    for src in total_counts.index:
        metrics.append(html.Div([
                html.H4(f"Commentaires {src}"),
                html.P(f"Total: {total_counts[src]}"),
                html.P(f"😍😊💕: {pos_counts.get(src, 0)}"),
                html.P(f"🤬😡🥵: {neg_counts.get(src, 0)}"),
                html.P(f"% Négatifs: {neg_ratio.get(src, 0)}%"),
                html.P(f"Moy./jour: {avg_comments[src]}"),
                html.P(f"Moy.Négatifs/jour: {avg_neg[src]}")
            ], style={"border": "1px solid #ccc", "padding": "10px", "margin": "5px"}))

    return metrics

# === Callback interconnecté avec clics ===
@app.callback(
    [Output("viz-sentiments", "figure"),
     Output("viz-nps", "figure"),
     Output("viz-aspects", "figure")],
    [Input("viz-filtre-source", "value"),
     Input("viz-filtre-date", "start_date"),
     Input("viz-filtre-date", "end_date")]
)
def maj_viz(sources, start_date, end_date):
    if not sources:
        return {}, {}, {}

    # Filtrage par source et date
    dff = df[df["source"].isin(sources)]
    dff = dff[(dff["date"].dt.date >= pd.to_datetime(start_date).date()) &
              (dff["date"].dt.date <= pd.to_datetime(end_date).date())]

    if dff.empty:
        return {}, {}, {}

    # === Graphique sentiments ===
    tot_count = absa_df[absa_df['source'].isin(sources)].groupby(['date', 'sentiment']).size().reset_index(name='tot_count')
    couleurs_fixes = {"negatif": "red", "positif": "green"}
    fig_sentiments = px.bar(tot_count, x="date", y="tot_count", color="sentiment",
                            barmode="group", color_discrete_map=couleurs_fixes)

    # === Proxy NPS ===
    all_dates = pd.date_range(start=dff["date"].min().date(), end=dff["date"].max().date(), freq="D")
    multi_index = pd.MultiIndex.from_product([all_dates, dff["source"].unique()], names=["date", "source"])
    daily_counts = dff.groupby([dff["date"].dt.date, "source"]).size().reindex(multi_index, fill_value=0).unstack()
    daily_neg_counts = dff[dff["sentiment"] == "NEGATIVE"].groupby([dff["date"].dt.date, "source"]).size().reindex(multi_index, fill_value=0).unstack()
    detra = daily_neg_counts / daily_counts.replace(0, np.nan)
    promo = 1 - detra
    nps = promo - detra
    nps_reset = nps.reset_index().melt(id_vars="date", var_name="source", value_name="NPS").dropna()
    fig_nps = px.line(nps_reset, x="date", y="NPS", color="source")

    # === Graphique aspects ===
    absa_grouped = absa_df[absa_df["source"].isin(sources)].groupby(["source", "aspect", "sentiment"]).size().reset_index(name="count")
    fig_aspects = px.bar(absa_grouped, x="aspect", y="count", color="sentiment",
                         barmode="group", facet_col="source",
                         color_discrete_map={"negatif": "red", "positif": "green"})

    return fig_sentiments, fig_nps, fig_aspects

@app.callback(
    Output("nouveau-graphique", "children"),
    [Input("viz-sentiments", "clickData"),
     Input("viz-filtre-source", "value")]
)
def creer_nouveau_graph(clickData, sources):
    if not clickData or not sources:
        return html.Div("📌 Cliquez sur une barre pour afficher les aspects de cette date.")

    # Récupère la date cliquée
    selected_date = clickData['points'][0]['x']
    filtered_absa = absa_df[(absa_df['source'].isin(sources)) & (absa_df['date'] == selected_date)]

    if filtered_absa.empty:
        return html.Div(f"Aucun commentaire trouvé pour le {selected_date}.")

    # Regrouper par aspect
    aspect_count = filtered_absa.groupby('aspect').size().reset_index(name='nb_commentaires')

    # Crée un nouveau graphique
    fig_aspects = px.bar(aspect_count, x='aspect', y='nb_commentaires', color='aspect',
                         title=f"Commentaires par aspect le {selected_date}")

    return dcc.Graph(figure=fig_aspects)

@app.callback(
    Output("details-table", "data"),
    [Input("details-date", "value"),
     Input("details-source", "value"),
     Input("details-aspect", "value"),
     Input("details-sentiment", "value")]
)
def filter_details(date_filter, source_filter, aspect_filter, sentiment_filter):
    filtered_df = absa_df.copy()

    if source_filter != "Toutes":
        filtered_df = filtered_df[filtered_df['source'] == source_filter]
    if aspect_filter != "Tous":
        filtered_df = filtered_df[filtered_df['aspect'] == aspect_filter]
    if sentiment_filter != "Tous":
        filtered_df = filtered_df[filtered_df['sentiment'] == sentiment_filter]
    if date_filter != "Toutes":
        filtered_df = filtered_df[filtered_df["date"] == date_filter]

    return filtered_df[["date", "auteur", "phrase", "aspect"]].to_dict("records")


# 5. Lancement
# ========================
if __name__ == "__main__":
    app.run(debug=True, port=8050)


# # ----------- PAGE CHATBOT --------
# elif page == "🤖 Chatbot IA":
#     st.title("🤖 Assistant Marketing IA")

#     # ---- État de la conversation ----
#     if "chat_history" not in st.session_state:
#         st.session_state.chat_history = []

#     # Zone de saisie utilisateur
#     user_input = st.chat_input("💬 Posez votre question :")

#     if user_input:
#         # Stocker immédiatement la question de l’utilisateur
#         st.session_state.chat_history.append(("user", user_input))
        
#         # Générer une réponse contextualisée (toujours en français)
#         prompt = f"""
#         Tu es un assistant virtuel spécialisé en **marketing bancaire et digital**. 
#         Tes réponses doivent être **en français**, claires et pédagogiques. 
#         Sois structuré et donne des exemples concrets quand c’est pertinent. 
#         Voici la question de l’utilisateur : {user_input}
#         """

#         response = query_llama(prompt)

#         # Stocker la réponse
#         st.session_state.chat_history.append(("assistant", response))

#     # Affichage du chat avec bulles
#     for role, msg in st.session_state.chat_history:
#         if role == "user":
#             with st.chat_message("user"):
#                 st.markdown(msg)
#         else:
#             with st.chat_message("assistant"):
#                 st.markdown(msg)


