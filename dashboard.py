import streamlit as st
import requests
import plotly.graph_objects as go
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import shap
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

# Définition de l'adresse des API :
DATA_API_URL = "https://database-api-p8-5f65595d7f94.herokuapp.com"
PRED_API_URL = "https://credit-scoring-api-p8-5912dd3b3665.herokuapp.com/predict"

# Définition des descriptions et détails des variables :
DESCRIPTIONS = {
    "AGE": ["Âge du souscripteur", "Âge"],
    "AMT_ANNUITY": ["Montant de l'annuité", "Montant de l'annuité"],
    "AMT_CREDIT": ["Montant du crédit", "Montant du crédit"],
    "AMT_GOODS_PRICE": ["Montant des biens concernés", "Montant des biens concernés"],
    "AMT_INCOME_TOTAL": ["Revenu annuel", "Revenu annuel"],
    "CODE_GENDER": ["Sexe (1 pour F, 0 pour M)", "Sexe"],
    "DAYS_EMPLOYED": ["Ancienneté contrat de travail (jours)", "Ancienneté contrat de travail"],
    "DAYS_ID_PUBLISH": ["Ancienneté carte ID (jours)", "Ancienneté carte ID"],
    "DAYS_LAST_PHONE_CHANGE": ["Ancienneté téléphone (jours)", "Ancienneté téléphone"],
    "DAYS_REGISTRATION": ["Jours depuis dernière modification", "Jours depuis dernière modification"],
    "EXT_SOURCE_1": ["Note Source 1", "Note Source 1"],
    "EXT_SOURCE_2": ["Note Source 2", "Note Source 2"],
    "EXT_SOURCE_3": ["Note Source 3", "Note Source 3"],
    "OWN_CAR_AGE": ["Âge du véhicule (années)", "Âge du véhicule"]
}

# Chargement des données statistiques des variables :
STATISTICS = pd.read_csv('statistics.csv')

# Définition des sets de couleurs pour l'accessibilité :
STD_POS_COL = 'ForestGreen'
STD_NEG_COL = 'Crimson'
ACC_POS_COL = 'CornflowerBlue'
ACC_NEG_COL = 'MidnightBlue'

# Configuration de la page Streamlit :
st.set_page_config(
    page_title="Tableau de bord crédit",
    layout="wide",  # Mise en page centrée
    initial_sidebar_state="expanded",  # Garder la sidebar toujours visible
    page_icon=":euro:"  # Icône de la page
)

# Injection de CSS personnalisé pour styliser les boutons :
st.markdown("""
    <style>
    .stButton>button {
        background-color: Navy;
        color: white;
        border-color: Navy;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: lightblue;
        color: black;
        border-color: Navy;
    }
    .stButton>button:focus {
        background-color: Navy;
        color: white !important;
        border-color: Navy !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)


def get_app_data(sk_id_curr):
    response = requests.get(f"{DATA_API_URL}/get_app/{sk_id_curr}")
    return response.json()

def update_app_data(data):
    response = requests.put(f"{DATA_API_URL}/update_app", json=data)
    return response.json()

def create_app_data(data):
    response = requests.post(f"{DATA_API_URL}/create_app", json=data)
    return response.json()

def predict(data):
    response = requests.post(PRED_API_URL, json=data)
    return response.json()

# Fonction pour initialiser les données du dossier
def init_app_data():
    return {key: "" for key in DESCRIPTIONS}

# Initialisation de l'état de session pour le bouton "Couleurs"
if 'colors_toggled' not in st.session_state:
    st.session_state.colors_toggled = False

# Fonction pour basculer l'état des couleurs
def toggle_colors():
    st.session_state.colors_toggled = not st.session_state.colors_toggled

def color_with_alpha(name, alpha):
    # Convertir le nom de couleur en RGB
    rgb_color = mcolors.to_rgb(name)
    # Retourner la couleur en RGBA avec transparence
    return f"rgba({int(rgb_color[0]*255)}, {int(rgb_color[1]*255)}, {int(rgb_color[2]*255)}, {alpha})"

# Menu de navigation entre les pages :
st.sidebar.title("Tableau de bord dossier de prêt")
page = st.sidebar.radio("Sélectionnez une page :", ["Aide", "Analyser le dossier", "Expliquer la décision", "Comparer le dossier"])
st.session_state.page = page

for i in range(5):
    st.sidebar.write("")

# Bouton pour basculer les couleurs
if st.sidebar.button("Changer les couleurs", on_click=toggle_colors):
    pass

# Définir les couleurs en fonction de l'état du bouton
if st.session_state.colors_toggled:
    pos_color = ACC_POS_COL
    neg_color = ACC_NEG_COL
else:
    pos_color = STD_POS_COL
    neg_color = STD_NEG_COL

# Gestion de l'état de session pour suivre les modifications :
if 'current_app_data' not in st.session_state:
    st.session_state.current_app_data = init_app_data()

if 'sk_id_curr' not in st.session_state:
    st.session_state.sk_id_curr = ""

# Initialisation des données :
app_data = st.session_state.current_app_data
sk_id_curr = st.session_state.sk_id_curr

# Création des colonnes pour la mise en page :
col1, col2, col3 = st.columns([1, 0.1, 2])

# Colonne de gauche pour les formulaires et champs de données :
with col1:
    st.image('logo.jpg', use_column_width=True)
    st.write("## Dossier de prêt")
    
    # Formulaire pour le n° de dossier :
    with st.form(key='sk_id_curr_form'):
        st.session_state.sk_id_seek = st.text_input("Inscrire le n° de dossier :", value=st.session_state.sk_id_curr)
        show_app = st.form_submit_button(label='Afficher le dossier')
    
    # Boutons pour enregistrer les données du dossier ou créer un nouveau dossier :
    btn1_col1, btn1_col2 = st.columns(2)
    with btn1_col1:
        submit_button = st.button("Enregistrer le dossier", use_container_width=True)
    with btn1_col2:
        new_app = st.button("Nouveau dossier", use_container_width=True)

    # Actions pour le bouton "Afficher le dossier" :
    if show_app and st.session_state.sk_id_seek:
        
        app_data = get_app_data(st.session_state.sk_id_seek)
        if "error" in app_data:
            st.error(app_data["error"])
        else:
            # Mise à jour les données du client affichées :
            st.session_state.current_app_data = app_data
            st.session_state.sk_id_curr = st.session_state.sk_id_seek

    # Actions pour le bouton 'Nouveau dossier' :
    if new_app:

        # Rénitialisation des données du dossier et des champs du formulaire :
        st.session_state.current_app_data = init_app_data()
        st.session_state.sk_id_curr = ""  
        st.session_state.page = "Aide" 
        st.rerun()

    # Actions pour le bouton "Enregistrer les modifications" :
    if submit_button:
        if st.session_state.sk_id_curr:

            # Si ID du dossier renseigné, mise à jour les données existantes :
            response = update_app_data({
                "SK_ID_CURR": st.session_state.sk_id_curr,
                **st.session_state.current_app_data
                })
            if "error" in response:
                st.error(response["error"])
            else:
                st.success(response["message"])
        else:
            if st.session_state.current_app_data != init_app_data():
                
                # Si ID du dossier non renseigné, création d'un nouveau dossier :
                response = create_app_data(st.session_state.current_app_data)
                if "error" in response:
                    st.error(response["error"])
                else:
                    st.success(f"{response['message']} n° {response['SK_ID_CURR']}")
                    st.session_state.sk_id_curr = response['SK_ID_CURR']

    # Affichage des champs de données pour la modification :
    if "error" in app_data:
        app_data = init_app_data()
    for key in app_data:
        if key == 'SK_ID_CURR':
            continue  # Exclure SK_ID_CURR du formulaire
        st.session_state.current_app_data[key] = st.text_input(
            DESCRIPTIONS[key][0], app_data[key], placeholder="Non renseigné"
            )
            
# Colonne de droite pour l'analyse du dossier :
with col3:
    
    # Page d'Aide par défaut :
    if 'page' not in st.session_state:
        st.session_state.page = "Aide"

    if st.session_state.page == "Aide":
        
        # Contenu de la page "Analyser le dossier" :
        st.markdown("## Tableau de bord dossier de prêt")
        st.write("Bienvenue dans l'application d'analyse de dossier crédit.")
        st.write("Utilisez le menu à gauche de l'écran pour naviguer dans l'application :")
        st.markdown("##### > Aide")
        st.write("Page actuelle")
        st.markdown("##### > Analyser le dossier")
        st.write("Prédiction du risque de défaut de paiement pour le dossier affiché")
        st.markdown("##### > Expliquer la décision")
        st.write("Affichage de l'influence des caractéristiques du dossier dans la prédiction effectuée")
        st.markdown("##### > Comparer le dossier")
        st.write("Permet de comparer les caractéristiques du dossier avec celles de l'ensemble des dossiers")
        st.write("")
        st.markdown("### Accessibilité")
        st.write("-  Le bouton < Changer les couleurs > présent dans le volet de navigation permet de basculer sur un mode adapté aux personnes présentant des difficultés à distinguer les couleurs.")
        st.write("-  Pour agrandir ou réduire la taille des textes, appuyez sur la touche CTRL + molette de la souris.")
        st.write("-  Chaque visuel peut être basculé en mode plein écran en cliquant sur l'icône en haut à droite de celui-ci.")
        
    # Page "Analyser le dossier"
    if st.session_state.page == "Analyser le dossier" and st.session_state.sk_id_curr != "":
        
        # Contenu de la page "Analyser le dossier" :
        st.markdown("## Analyse du dossier")

        prediction_data = {k: v for k, v in st.session_state.current_app_data.items() if k != "SK_ID_CURR"}
        prediction_response = predict(prediction_data)
        
        st.markdown("#### Décision recommandée :")
        if "error" in prediction_response:
            st.error(prediction_response["error"])
        else:
            # Affichage du résultat de la prédiction :
            dossier_result = prediction_response['Dossier']
            if dossier_result == "ACCEPTATION DU DOSSIER":
                st.markdown(f"<h2 style='color: {pos_color};'>{dossier_result}</h2>", unsafe_allow_html=True)
                st.write("")
            else:
                st.markdown(f"<h2 style='color: {neg_color};'>{dossier_result}</h2>", unsafe_allow_html=True)
                st.write("")
            
            # Chargement des probabilité et seuil :
            prob = round(prediction_response['Probabilite'] * 100, 3)
            threshold = round(prediction_response['Seuil'] * 100, 3)
            
            st.write("#### Probabilité de défaut de paiement :")
            st.write(f"##### (seuil de refus du dossier : {threshold} %)")
            
            # Affichage de la jauge de probabilité :
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prob,
                number={'suffix': ' %'},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': neg_color},
                    'steps': [
                        {'range': [0, threshold], 'color': color_with_alpha(pos_color, 0.4)},
                        {'range': [threshold, 100], 'color': color_with_alpha(neg_color, 0.4)}
                    ],
                    'threshold': {
                        'line': {'color': 'black', 'width': 5},
                        'thickness': 1.0,
                        'value': threshold
                    }
                }
            ))
            
            fig.add_annotation(x=0, y=-0.2, text="Risque faible", showarrow=False,
                               xref="paper", yref="paper", align="left", font=dict(size=24, color=pos_color))
            fig.add_annotation(x=1, y=-0.2, text="Risque élevé", showarrow=False,
                               xref="paper", yref="paper", align="right", font=dict(size=24, color=neg_color))
               
            st.plotly_chart(fig)
        
    # Page "Expliquer la décision" :
    elif st.session_state.page == "Expliquer la décision" and st.session_state.sk_id_curr != "":
        
        # Contenu de la page "Expliquer la décision" :
        st.markdown("## Interprétation de la décision")

        prediction_data = {k: v for k, v in st.session_state.current_app_data.items() if k != "SK_ID_CURR"}
        prediction_response = predict(prediction_data)
    
        if "error" in prediction_response:
            st.error(prediction_response["error"])
        else:
            # Chargement des valeurs SHAP :
            shap_values = prediction_response['Shapvals'][0]
            base_values = prediction_response['Basevals'][0]

            # Création du graphique waterfall SHAP :
            fig, ax = plt.subplots()
            shap.waterfall_plot(
                shap.Explanation(values=np.array(shap_values),
                                 base_values=base_values,
                                 feature_names=[DESCRIPTIONS[k][1] for k in list(prediction_data.keys())]),
                max_display=14, show=False
            )
            
            default_pos_color = "#ff0051"
            default_neg_color = "#008bfb"
            positive_color = neg_color
            negative_color = pos_color
            for fc in plt.gcf().get_children():
                for fcc in fc.get_children():
                    if isinstance(fcc, mpatches.FancyArrow):
                        if mcolors.to_hex(fcc.get_facecolor()) == default_pos_color:
                            fcc.set_facecolor(positive_color)
                            fcc.set_edgecolor(positive_color)  # Set edge color for positive bars
                        elif mcolors.to_hex(fcc.get_facecolor()) == default_neg_color:
                            fcc.set_facecolor(negative_color)
                            fcc.set_edgecolor(negative_color)  # Set edge color for negative bars
                    elif isinstance(fcc, plt.Text):
                        if mcolors.to_hex(fcc.get_color()) == default_pos_color:
                            fcc.set_color(positive_color)
                        elif mcolors.to_hex(fcc.get_color()) == default_neg_color:
                            fcc.set_color(negative_color)                
            st.pyplot(fig)
            
        st.write("Les flèches orientées vers la gauche indiquent une réduction du risque de défaut de paiement")
        st.write("Les flèches orientées vers la droite indiquent une agravation du risque de défaut de paiement")
        
    # Page "Comparer le dossier"
    elif st.session_state.page == "Comparer le dossier" and st.session_state.sk_id_curr != "":
        
        # Contenu de la page "Comparer le dossier" :
        st.markdown("## Comparaison avec les autres dossiers")

        with st.form(key='compare_form'):

            # Sélection de la variable dans le formulaire :
            box_features = [DESCRIPTIONS[f][1] for f in STATISTICS['FEATURE'].tolist() if f != "CODE_GENDER"]
            selected_feature = st.selectbox(
                "Sélectionner une caractéristique pour la comparaison :",
                box_features
            )

            # Soumission du formulaire :
            show_button = st.form_submit_button(label='Comparer')            

        # Actions du bouton "Comparer" :
        if show_button:
            for key, value in DESCRIPTIONS.items():
                if value[1] == selected_feature:
                    selected_FEAT = key
                    break

            current_value = st.session_state.current_app_data[selected_FEAT]

            # Chargement des distributions de la variable :
            dist_0 = STATISTICS.loc[STATISTICS['FEATURE'] == selected_FEAT, 'DIST_0'].values[0]
            dist_1 = STATISTICS.loc[STATISTICS['FEATURE'] == selected_FEAT, 'DIST_1'].values[0]
            dist_0 = [float(x) for x in dist_0.strip('[]').split(', ')]
            dist_1 = [float(x) for x in dist_1.strip('[]').split(', ')]

            # Calcul des densités des distributions :
            x_range = np.linspace(min(dist_0 + dist_1), max(dist_0 + dist_1), 100)
            kde_0 = gaussian_kde(dist_0)
            density_0 = kde_0(x_range)
            kde_1 = gaussian_kde(dist_1)
            density_1 = kde_1(x_range)

            # Courbe de densité des dossiers remboursés :
            target_0 = go.Scatter(
                x=x_range,
                y=density_0,
                mode='lines',
                name='Dossiers remboursés',
                line=dict(color=pos_color),
                fill='tozeroy',
                fillcolor=color_with_alpha(pos_color, 0.2)
            )

            # Courbe de densité des dossiers avec difficultés de paiement :
            target_1 = go.Scatter(
                x=x_range,
                y=density_1,
                mode='lines',
                name='Dossiers avec difficultés de paiement',
                line=dict(color=neg_color),
                fill='tozeroy',
                fillcolor=color_with_alpha(neg_color, 0.2)
            )

            # Ligne de valeur du dossier courant :
            line = go.Scatter(
                x=[current_value, current_value],
                y=[0, max(max(density_0), max(density_1)) * 1.1],
                mode='lines',
                name='Dossier actuel',
                line=dict(color='blue', dash='solid')
            )

            # Création de la figure :
            fig = go.Figure(data=[target_0, target_1, line])

            # Mise en forme de la figure :
            fig.update_layout(
                width=800,
                height=600,
                legend=dict(
                    orientation="h", x=0, y=1.2,
                    title=dict(text="Cliquer sur un élément pour le cacher ou l'afficher à nouveau :", font=dict(size=16)),
                    font=dict(size=16)
                ),
                xaxis_title=selected_feature,  # Titre de l'axe x
                yaxis_title="Densité (volume) de dossiers"  # Titre de l'axe y
            )
            
            st.plotly_chart(fig)
            
            # Affichage du tableau des données statistiques :
            stat_vals = STATISTICS[STATISTICS['FEATURE'] == selected_FEAT].iloc[:, 3:]
            stats = pd.DataFrame(
                [stat_vals.iloc[:, :4].values[0], stat_vals.iloc[:, 4:].values[0]],
                index=['Dossiers remboursées', 'Dossiers avec difficulté de paiement'],
                columns=['Minimum', 'Maximum', 'Moyenne', 'Médiane']
            )
            st.write("Dossier actuel : ", current_value)
            
            st.table(stats)
