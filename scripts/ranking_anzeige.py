#ranking_anzeige.py

import pandas as pd
import os

# --- Konstanten (sollten am Anfang der Datei stehen) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TIPPS_DIR = os.path.join(BASE_DIR, 'tipps')

SPIELE_DATEI = os.path.join(DATA_DIR, 'spiele.csv')
ERGEBNISSE_DATEI = os.path.join(DATA_DIR, 'ergebnisse.csv')

# Spaltennamen (falls noch nicht definiert)
SPIELID_COL = 'Spiel_ID'
HEIMTEAM_COL = 'Heimteam'
AUSWAERTSTE_COL = 'Auswärtsteam'
HEIM_TORE_COL = 'Heim_Tore'
AUSWAERTS_TORE_COL = 'Auswärts_Tore'
# --- Ende Konstanten ---

# --- Vorhandene Funktionen (load_games, load_results, etc.) ---
def load_games():
    """Lädt die Spieldaten aus der spiele.csv."""
    if not os.path.exists(SPIELE_DATEI):
        print(f"Warnung: {SPIELE_DATEI} nicht gefunden.")
        return pd.DataFrame(columns=[SPIELID_COL, HEIMTEAM_COL, AUSWAERTSTE_COL]).set_index(SPIELID_COL)
    df = pd.read_csv(SPIELE_DATEI, index_col=SPIELID_COL)
    return df

def load_results():
    """Lädt die Spielergebnisse aus der ergebnisse.csv."""
    if not os.path.exists(ERGEBNISSE_DATEI):
        print(f"Warnung: {ERGEBNISSE_DATEI} nicht gefunden.")
        return pd.DataFrame(columns=[SPIELID_COL, HEIM_TORE_COL, AUSWAERTS_TORE_COL]).set_index(SPIELID_COL)
    df = pd.read_csv(ERGEBNISSE_DATEI, index_col=SPIELID_COL)
    return df

def load_player_tips(player_name):
    """Lädt die Tipps eines Spielers."""
    file_path = os.path.join(TIPPS_DIR, f'{player_name.lower()}.csv')
    if not os.path.exists(file_path):
        return pd.DataFrame()
    return pd.read_csv(file_path, index_col=SPIELID_COL)

def calculate_points_for_player(player_tips, all_games, results):
    """Berechnet die Punkte für einen Spieler."""
    points = 0
    for game_id, tip in player_tips.iterrows():
        if game_id not in results.index:
            continue # Kein Ergebnis für dieses Spiel vorhanden

        actual_result = results.loc[game_id]
        
        # Sicherstellen, dass die Tipps existieren und keine NaN sind
        if pd.isna(tip.get(HEIMTEAM_COL + '_Tipp')) or pd.isna(tip.get(AUSWAERTSTE_COL + '_Tipp')):
            continue

        tipped_heim_tore = int(tip[HEIMTEAM_COL + '_Tipp'])
        tipped_auswaerts_tore = int(tip[AUSWAERTSTE_COL + '_Tipp'])
        
        actual_heim_tore = int(actual_result[HEIM_TORE_COL])
        actual_auswaerts_tore = int(actual_result[AUSWAERTS_TORE_COL])

        # Exakter Tipp (4 Punkte)
        if tipped_heim_tore == actual_heim_tore and tipped_auswaerts_tore == actual_auswaerts_tore:
            points += 4
        else:
            # Richtiger Spielausgang (1 Punkt)
            tipped_diff = tipped_heim_tore - tipped_auswaerts_tore
            actual_diff = actual_heim_tore - actual_auswaerts_tore

            if (tipped_diff > 0 and actual_diff > 0) or \
               (tipped_diff < 0 and actual_diff < 0) or \
               (tipped_diff == 0 and actual_diff == 0):
                points += 1
                # Richtige Tordifferenz (zusätzliche 2 Punkte)
                if tipped_diff == actual_diff:
                    points += 2
    return points

def get_all_player_rankings():
    """Berechnet das Ranking für alle Spieler."""
    all_games = load_games()
    results = load_results()
    
    player_points = {}
    
    # Durchsuche den tipps-Ordner nach Spieler-CSV-Dateien
    if os.path.exists(TIPPS_DIR):
        for filename in os.listdir(TIPPS_DIR):
            if filename.endswith('.csv'):
                player_name = os.path.splitext(filename)[0]
                player_tips = load_player_tips(player_name)
                
                if not player_tips.empty:
                    points = calculate_points_for_player(player_tips, all_games, results)
                    player_points[player_name.capitalize()] = points # Namen kapitalisieren für Anzeige

    if not player_points:
        return pd.DataFrame(columns=['Rang', 'Spieler', 'Punkte'])

    ranking_df = pd.DataFrame(list(player_points.items()), columns=['Spieler', 'Punkte'])
    ranking_df = ranking_df.sort_values(by='Punkte', ascending=False).reset_index(drop=True)
    ranking_df['Rang'] = ranking_df.index + 1
    return ranking_df[['Rang', 'Spieler', 'Punkte']]

# --- NEUE / Angepasste Funktion zum Speichern der Ergebnisse ---
def save_result(spiel_id: int, heim_tore: int, auswaerts_tore: int):
    """
    Speichert das Ergebnis eines Spiels in der ergebnisse.csv.
    Aktualisiert ein bestehendes Ergebnis oder fügt ein neues hinzu.
    """
    # Sicherstellen, dass der DATA_DIR existiert
    os.makedirs(DATA_DIR, exist_ok=True)

    # KORREKTUR Bug 1: ERGEBNISSE_DATEI enthält bereits den vollen Pfad!
    df_ergebnisse = load_results()

    if spiel_id in df_ergebnisse.index:
        # Ergebnis aktualisieren
        df_ergebnisse.loc[spiel_id, HEIM_TORE_COL] = heim_tore
        df_ergebnisse.loc[spiel_id, AUSWAERTS_TORE_COL] = auswaerts_tore
        print(f"Ergebnis für Spiel ID {spiel_id} aktualisiert: {heim_tore}:{auswaerts_tore}")
    else:
        # Neues Ergebnis hinzufügen
        new_row_df = pd.DataFrame([{
            SPIELID_COL: spiel_id,
            HEIM_TORE_COL: heim_tore,
            AUSWAERTS_TORE_COL: auswaerts_tore
        }]).set_index(SPIELID_COL)
        df_ergebnisse = pd.concat([df_ergebnisse, new_row_df])
        print(f"Neues Ergebnis für Spiel ID {spiel_id} hinzugefügt: {heim_tore}:{auswaerts_tore}")

    # KORREKTUR Bug 2: index_label setzen, damit 'Spiel_ID' als Spaltenname gespeichert wird!
    df_ergebnisse.index.name = SPIELID_COL
    df_ergebnisse.to_csv(ERGEBNISSE_DATEI, index=True)
    print(f"Ergebnisse gespeichert in: {ERGEBNISSE_DATEI}")