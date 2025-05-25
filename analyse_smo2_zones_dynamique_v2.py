
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Analyse interactive de la SmO₂ – TZP")

uploaded_file = st.file_uploader("📂 Importer un fichier Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet = st.selectbox("Choisir la feuille de données", xls.sheet_names)
    df = xls.parse(sheet)

    # Sélection des colonnes
    time_col = st.selectbox("Colonne Temps (s)", [col for col in df.columns if "Time" in col])
    smo2_col = st.selectbox("Colonne SmO₂ (%)", [col for col in df.columns if "SmO2" in col])
    power_col = st.selectbox("Colonne Puissance (W)", [col for col in df.columns if "Power" in col or "Target" in col])
    hr_col = st.selectbox("Colonne Fréquence cardiaque (bpm)", [col for col in df.columns if "HR" in col or "Fréquence" in col])

    df = df[[time_col, smo2_col, power_col, hr_col]].dropna()
    df.columns = ['Time', 'SmO2', 'Power', 'HR']

    # Normalisation SmO2
    smo2_min = df['SmO2'].min()
    smo2_max = df['SmO2'].max()
    df['SmO2_norm'] = 100 * (df['SmO2'] - smo2_min) / (smo2_max - smo2_min)

    # SmO2 max au début du test (dans les 2 premières minutes)
    early_phase = df[df['Time'] <= 120]
    smo2_start_max = early_phase['SmO2'].max()
    smo2_start_max_norm = 100 * (smo2_start_max - smo2_min) / (smo2_max - smo2_min)

    st.subheader("📊 Courbe normalisée de la SmO₂")

    # Choix des seuils
    s1 = st.slider("Position de S1 (s)", int(df['Time'].min()), int(df['Time'].max()), int(df['Time'].min()) + 200)
    s2 = st.slider("Position de S2 (s)", int(df['Time'].min()), int(df['Time'].max()), int(df['Time'].min()) + 600)
    pma = st.slider("Position de la PMA (s)", int(df['Time'].min()), int(df['Time'].max()), int(df['Time'].max()) - 100)

    # Fonction pour récupérer les valeurs au plus proche d'un instant
    def get_values_at(time_val):
        row = df.iloc[(df['Time'] - time_val).abs().argmin()]
        return row['Time'], row['Power'], row['HR'], row['SmO2'], row['SmO2_norm']

    s1_vals = get_values_at(s1)
    s2_vals = get_values_at(s2)
    pma_vals = get_values_at(pma)

    # Affichage graphique avec zones dynamiques
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['Time'], df['SmO2_norm'], label='SmO₂ normalisée (%)', color='blue')

    # Zones d’intensité dynamiques selon les seuils S1 et S2
    ax.axhspan(smo2_start_max_norm, 100, color='lightblue', alpha=0.3, label='Réoxygénation post-effort')
    ax.axhspan(s1_vals[4], smo2_start_max_norm, color='green', alpha=0.2, label='Zone 1 : Faible')
    ax.axhspan(s2_vals[4], s1_vals[4], color='orange', alpha=0.2, label='Zone 2 : Modérée')
    ax.axhspan(0, s2_vals[4], color='red', alpha=0.2, label='Zone 3 : Sévère')

    # Lignes verticales
    ax.axvline(s1, color='green', linestyle='--', label=f'S1 ({int(s1_vals[1])} W, {int(s1_vals[2])} bpm)')
    ax.axvline(s2, color='red', linestyle='--', label=f'S2 ({int(s2_vals[1])} W, {int(s2_vals[2])} bpm)')
    ax.axvline(pma, color='black', linestyle='--', label=f'PMA ({int(pma_vals[1])} W, {int(pma_vals[2])} bpm)')

    # Ligne horizontale SmO2 départ
    ax.axhline(smo2_start_max_norm, color='purple', linestyle='--', linewidth=1, label=f'SmO₂ max départ (~{smo2_start_max:.1f}%)')

    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("SmO₂ normalisée (%)")
    ax.set_title("SmO₂ – Zones d'intensité ajustées dynamiquement")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

    # Tableau récapitulatif
    st.subheader("📋 Données extraites")
    summary_df = pd.DataFrame({
        'Temps (s)': [s1_vals[0], s2_vals[0], pma_vals[0]],
        'Puissance (W)': [s1_vals[1], s2_vals[1], pma_vals[1]],
        'Fréquence cardiaque (bpm)': [s1_vals[2], s2_vals[2], pma_vals[2]],
        'SmO₂ (%)': [s1_vals[3], s2_vals[3], pma_vals[3]],
        'SmO₂ normalisée (%)': [s1_vals[4], s2_vals[4], pma_vals[4]]
    }, index=['Seuil 1', 'Seuil 2', 'PMA'])

    st.dataframe(summary_df)

    # Export CSV
    csv = summary_df.to_csv(index=True).encode('utf-8')
    st.download_button("💾 Télécharger les données (CSV)", data=csv, file_name="smo2_seuils.csv", mime="text/csv")
