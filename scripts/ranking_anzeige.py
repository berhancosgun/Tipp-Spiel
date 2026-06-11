# ranking_anzeige.py

import pandas as pd
import os
import streamlit as st
import gspread
import time  # ← NEU
from google.oauth2.service_account import Credentials

# =========================================================
# 📁 Konstanten (für lokale Dateien wie spiele.csv)
# =========================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TIPPS_DIR = os.path.join(BASE_DIR, 'tipps')

SPIELE_DATEI = os.path.join(DATA_DIR, 'spiele.csv')
ERGEBNISSE_DATEI = os.path.join(DATA_DIR, 'ergebnisse.csv')

SPIELID_COL        = 'Spiel_ID'
HEIMTEAM_COL       = 'Heimteam'
AUSWAERTSTE_COL    = 'Auswärtsteam'
HEIM_TORE_COL      = 'Heim_Tore'
AUSWAERTS_TORE_COL = 'Auswärts_Tore'

# =========================================================
# 🔗 Google Sheets Verbindung
# =========================================================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_google_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open(st.secrets["sheet_name"])
    return sheet

def get_worksheet(tab_name: str):
    sheet = get_google_sheet()
    try:
        return sheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=tab_name, rows=500, cols=20)
        return ws

# =========================================================
# 🔁 Hilfsfunktion: API Call mit Retry bei 429
# =========================================================
def api_call_with_retry(func, *args, retries=5, wait=15, **kwargs):
    """Führt eine API-Funktion aus und wiederholt bei 429-Fehler."""
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ Rate Limit! Warte {wait}s... (Versuch {attempt+1}/{retries})")
                time.sleep(wait)
                wait *= 2  # Exponential Backoff
            else:
                raise e
    raise Exception("❌ Google Sheets API Limit dauerhaft überschritten. Bitte später versuchen.")

# =========================================================
# 📥 Spiele laden
# =========================================================
@st.cache_data(ttl=30)
def load_games():
    if not os.path.exists(SPIELE_DATEI):
        return pd.DataFrame(
            columns=[SPIELID_COL, HEIMTEAM_COL, AUSWAERTSTE_COL]
        ).set_index(SPIELID_COL)
    df = pd.read_csv(SPIELE_DATEI, index_col=SPIELID_COL)
    return df

# =========================================================
# 📥 Ergebnisse laden (Google Sheets)
# =========================================================
def load_results():
    try:
        ws = get_worksheet("Ergebnisse")
        data = api_call_with_retry(ws.get_all_records)
        if not data:
            return pd.DataFrame(
                columns=[SPIELID_COL, HEIM_TORE_COL, AUSWAERTS_TORE_COL]
            ).set_index(SPIELID_COL)
        df = pd.DataFrame(data)
        df[SPIELID_COL] = pd.to_numeric(df[SPIELID_COL], errors='coerce')
        df = df.dropna(subset=[SPIELID_COL])
        df[SPIELID_COL] = df[SPIELID_COL].astype(int)
        df = df.set_index(SPIELID_COL)
        return df
    except Exception as e:
        print(f"Fehler beim Laden der Ergebnisse: {e}")
        return pd.DataFrame(
            columns=[SPIELID_COL, HEIM_TORE_COL, AUSWAERTS_TORE_COL]
        ).set_index(SPIELID_COL)

# =========================================================
# 📥 ALLE Tipps auf einmal laden ← NEU (1 API Call statt N)
# =========================================================
@st.cache_data(ttl=60)
def load_all_tips_from_sheet():
    """Lädt ALLE Tipps in einem einzigen API Call."""
    try:
        ws = get_worksheet("Tipps")
        data = api_call_with_retry(ws.get_all_records)
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Fehler beim Laden aller Tipps: {e}")
        return pd.DataFrame()

# =========================================================
# 📥 Spieler-Tipps laden (aus gecachtem DataFrame)
# =========================================================
def load_player_tips(player_name: str):
    try:
        df = load_all_tips_from_sheet()
        if df.empty or 'Spieler' not in df.columns:
            return pd.DataFrame()

        player_df = df[df['Spieler'].str.lower() == player_name.lower()].copy()
        if player_df.empty:
            return pd.DataFrame()

        # ← NEU: Leere Spiel_ID Zeilen entfernen
        player_df = player_df[player_df[SPIELID_COL].astype(str).str.strip() != '']
        player_df[SPIELID_COL] = pd.to_numeric(player_df[SPIELID_COL], errors='coerce')
        player_df = player_df.dropna(subset=[SPIELID_COL])
        player_df[SPIELID_COL] = player_df[SPIELID_COL].astype(int)
        player_df = player_df.set_index(SPIELID_COL)
        player_df = player_df.drop(columns=['Spieler'], errors='ignore')
        return player_df

    except Exception as e:
        print(f"Fehler beim Laden der Tipps für {player_name}: {e}")
        return pd.DataFrame()

# =========================================================
# 💾 Spieler-Tipps speichern (Google Sheets)
# =========================================================
def save_player_tips_to_sheet(player_name: str, tips_df: pd.DataFrame):
    """Speichert die Tipps eines Spielers in Google Sheets."""
    try:
        ws = get_worksheet("Tipps")
        data = api_call_with_retry(ws.get_all_records)  # ← Mit Retry
        df = pd.DataFrame(data) if data else pd.DataFrame()

        new_df = tips_df.copy()
        if new_df.index.name != SPIELID_COL:
            if SPIELID_COL in new_df.columns:
                new_df = new_df.set_index(SPIELID_COL)
        new_df = new_df.reset_index()
        new_df.insert(0, 'Spieler', player_name)
        new_df = new_df.fillna("")

        if df.empty:
            ws.clear()
            api_call_with_retry(
                ws.update,
                [new_df.columns.tolist()] + new_df.values.tolist()
            )
        else:
            df_others = df[df['Spieler'].str.lower() != player_name.lower()]
            combined = pd.concat([df_others, new_df], ignore_index=True)
            combined = combined.fillna("")
            ws.clear()
            api_call_with_retry(
                ws.update,
                [combined.columns.tolist()] + combined.values.tolist()
            )

        # Cache leeren nach dem Speichern ← NEU
        load_all_tips_from_sheet.clear()

    except Exception as e:
        raise Exception(f"Fehler beim Speichern der Tipps: {e}")

# =========================================================
# 💾 Ergebnis speichern (Google Sheets)
# =========================================================
def save_result(spiel_id: int, heim_tore: int, auswaerts_tore: int):
    try:
        ws = get_worksheet("Ergebnisse")
        data = api_call_with_retry(ws.get_all_records)
        df = pd.DataFrame(data) if data else pd.DataFrame()

        if df.empty:
            new_df = pd.DataFrame([{
                SPIELID_COL:        spiel_id,
                HEIM_TORE_COL:      heim_tore,
                AUSWAERTS_TORE_COL: auswaerts_tore
            }])
            ws.clear()
            api_call_with_retry(
                ws.update,
                [new_df.columns.tolist()] + new_df.values.tolist()
            )
        else:
            df[SPIELID_COL] = pd.to_numeric(df[SPIELID_COL], errors='coerce')
            if spiel_id in df[SPIELID_COL].values:
                df.loc[df[SPIELID_COL] == spiel_id, HEIM_TORE_COL]      = heim_tore
                df.loc[df[SPIELID_COL] == spiel_id, AUSWAERTS_TORE_COL] = auswaerts_tore
            else:
                new_row = pd.DataFrame([{
                    SPIELID_COL:        spiel_id,
                    HEIM_TORE_COL:      heim_tore,
                    AUSWAERTS_TORE_COL: auswaerts_tore
                }])
                df = pd.concat([df, new_row], ignore_index=True)

            ws.clear()
            api_call_with_retry(
                ws.update,
                [df.columns.tolist()] + df.values.tolist()
            )

    except Exception as e:
        raise Exception(f"Fehler beim Speichern des Ergebnisses: {e}")

# =========================================================
# 🧮 Punkte berechnen
# =========================================================
def calculate_points_for_player(player_tips, all_games, results):
    points = 0
    for game_id, tip in player_tips.iterrows():
        if game_id not in results.index:
            continue
        actual_result = results.loc[game_id]
        if pd.isna(tip.get(HEIMTEAM_COL + '_Tipp')) or \
           pd.isna(tip.get(AUSWAERTSTE_COL + '_Tipp')):
            continue

        tipped_heim      = int(tip[HEIMTEAM_COL     + '_Tipp'])
        tipped_auswaerts = int(tip[AUSWAERTSTE_COL  + '_Tipp'])
        actual_heim      = int(actual_result[HEIM_TORE_COL])
        actual_auswaerts = int(actual_result[AUSWAERTS_TORE_COL])

        if tipped_heim == actual_heim and tipped_auswaerts == actual_auswaerts:
            points += 4
        else:
            tipped_diff = tipped_heim - tipped_auswaerts
            actual_diff = actual_heim - actual_auswaerts
            if (tipped_diff > 0 and actual_diff > 0) or \
               (tipped_diff < 0 and actual_diff < 0) or \
               (tipped_diff == 0 and actual_diff == 0):
                points += 1
                if tipped_diff == actual_diff:
                    points += 2
    return points

# =========================================================
# 🏆 Ranking berechnen ← FIXED
# =========================================================
def get_all_player_rankings():
    all_games = load_games()
    results   = load_results()

    try:
        df = load_all_tips_from_sheet()
        if df.empty or 'Spieler' not in df.columns:
            return pd.DataFrame(columns=['Rang', 'Spieler', 'Punkte'])

        # ← NEU: Leere Spiel_ID Zeilen entfernen
        df = df[df[SPIELID_COL].astype(str).str.strip() != '']
        df = df.dropna(subset=[SPIELID_COL])

        player_names = df['Spieler'].str.lower().unique()
    except Exception as e:
        print(f"Fehler beim Laden des Rankings: {e}")
        return pd.DataFrame(columns=['Rang', 'Spieler', 'Punkte'])

    player_points = {}
    for player in player_names:
        try:
            tips = load_player_tips(player)
            if not tips.empty:
                pts = calculate_points_for_player(tips, all_games, results)
                player_points[player.capitalize()] = pts
        except Exception as e:
            print(f"Fehler bei Spieler {player}: {e}")
            continue  # ← Spieler überspringen, nicht abstürzen!

    if not player_points:
        return pd.DataFrame(columns=['Rang', 'Spieler', 'Punkte'])

    ranking_df = pd.DataFrame(
        list(player_points.items()), columns=['Spieler', 'Punkte']
    )
    ranking_df = ranking_df.sort_values(
        by='Punkte', ascending=False
    ).reset_index(drop=True)
    ranking_df['Rang'] = ranking_df.index + 1
    return ranking_df[['Rang', 'Spieler', 'Punkte']]