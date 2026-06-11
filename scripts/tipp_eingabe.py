import pandas as pd
import os

# --- NEUE KONSTANTEN FÜR DIE DATEIPFADE ---
# Das Basisverzeichnis des gesamten Projekts (Tippspiel/)
# Wir gehen davon aus, dass dieses Skript aus dem Hauptverzeichnis ausgeführt wird (z.B. python scripts/tipp_eingabe.py)
# Daher ist das aktuelle Arbeitsverzeichnis (os.getcwd()) das Projekt-Root.
BASE_DIR = os.getcwd()

# Pfade zu den Daten- und Tippordnern
DATA_DIR = os.path.join(BASE_DIR, 'data')
TIPPS_DIR = os.path.join(BASE_DIR, 'tipps')

# Dateinamen und Spaltennamen
SPIELE_DATEI = os.path.join(DATA_DIR, 'spiele.csv')
# ERGEBNISSE_DATEI = os.path.join(DATA_DIR, 'ergebnisse.csv') # Wird in diesem Skript nicht direkt verwendet
                                                              # aber gut zu wissen, wo es hingehört

HEIMTEAM_COL = 'Heimteam'
AUSWAERTSTE_COL = 'Auswärtsteam'
SPIELID_COL = 'SpielID'

# --- Funktionen (unverändert, aber nutzen jetzt die neuen Pfad-Konstanten) ---

def get_player_name():
    """Fragt nach dem Spielernamen und gibt ihn zurück."""
    while True:
        name = input("Bitte gib deinen Namen ein: ").strip()
        if name:
            return name
        else:
            print("Der Name darf nicht leer sein. Bitte versuche es erneut.")

def load_games(file_path=SPIELE_DATEI): # Nutzt jetzt SPIELE_DATEI aus den neuen Konstanten
    """Lädt die Spiele aus der CSV-Datei."""
    try:
        df = pd.read_csv(file_path)
        
        if SPIELID_COL not in df.columns:
            df[SPIELID_COL] = range(1, len(df) + 1)
        df = df.set_index(SPIELID_COL)

        required_columns = [HEIMTEAM_COL, AUSWAERTSTE_COL]
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            print(f"Fehler: Die Datei '{file_path}' muss die Spalten '{', '.join(missing_cols)}' enthalten.")
            return pd.DataFrame()
        
        return df
    except FileNotFoundError:
        print(f"Fehler: Die Datei '{file_path}' wurde nicht gefunden.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Fehler beim Laden der Spiele: {e}")
        return pd.DataFrame()

def load_player_tips(player_name):
    file_path = os.path.join(TIPPS_DIR, f'{player_name.lower()}.csv')
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    try:
        # Erst ohne index_col laden um den Header zu prüfen
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # Flexibel: Akzeptiere beide Varianten!
        if 'Spiel_ID' in df.columns:
            df = df.set_index('Spiel_ID')
        elif 'SpielID' in df.columns:
            df = df.set_index('SpielID')
            df.index.name = 'Spiel_ID'  # Umbenennen zur Konsistenz
        else:
            print(f"WARNUNG: Keine Spiel_ID Spalte in {file_path}")
            return pd.DataFrame()
        
        return df
    except Exception as e:
        print(f"FEHLER beim Laden von {file_path}: {e}")
        return pd.DataFrame()

def save_player_tips(player_name, tips_df, tips_dir=TIPPS_DIR):
    """Speichert die Tipps eines Spielers in seiner CSV-Datei."""
    os.makedirs(tips_dir, exist_ok=True)
    file_path = os.path.join(tips_dir, f'{player_name.lower()}.csv')
    try:
        # Sicherstellen dass Spiel_ID korrekt als Index gesetzt ist
        df_to_save = tips_df.copy()
        
        if df_to_save.index.name != SPIELID_COL:
            if SPIELID_COL in df_to_save.columns:
                df_to_save = df_to_save.set_index(SPIELID_COL)  # Spalte → Index
            else:
                print(f"WARNUNG: Spalte '{SPIELID_COL}' nicht gefunden!")
        
        # Jetzt sicher speichern
        df_to_save.to_csv(file_path, index=True)  # index=True schreibt den Index als erste Spalte
        print(f"Deine Tipps wurden erfolgreich in '{file_path}' gespeichert!")
    except Exception as e:
        print(f"Fehler beim Speichern deiner Tipps: {e}")
def get_valid_score_input(team_name):
    """Fordert den Benutzer zur Eingabe einer gültigen Torzahl auf oder 'q' zum Abbrechen."""
    while True:
        score_input = input(f"Tipp für {team_name} (Tore, oder 'q' zum Abbrechen): ").strip()
        if score_input.lower() == 'q':
            return 'q'
        try:
            score = int(score_input)
            if score >= 0:
                return score
            else:
                print("Ungültige Eingabe: Tore können nicht negativ sein. Bitte versuche es erneut.")
        except ValueError:
            print("Ungültige Eingabe: Bitte gib nur ganze Zahlen für die Tore ein oder 'q' zum Abbrechen. Bitte versuche es erneut.")

def main():
    print("⚽ Tippabgabe ⚽")
    print("----------------")

    all_games = load_games() # Ruft load_games ohne Argument auf, da Standardpfad gesetzt ist
    if all_games.empty:
        print("Fehler: Keine Spiele in 'spiele.csv' gefunden. Kann keine Tipps abgeben.")
        return

    player_name = get_player_name()
    player_name_lower = player_name.lower()

    player_tipps = load_player_tips(player_name_lower)

    if player_tipps.empty:
        player_tipps = pd.DataFrame(index=all_games.index)
        player_tipps[HEIMTEAM_COL + '_Tipp'] = pd.NA
        player_tipps[AUSWAERTSTE_COL + '_Tipp'] = pd.NA
        print(f"Neue Tippabgabe für {player_name}.")
    else:
        print(f"Bestehende Tipps für {player_name} geladen.")
    
    for game_id in all_games.index:
        if game_id not in player_tipps.index:
            player_tipps.loc[game_id, HEIMTEAM_COL + '_Tipp'] = pd.NA
            player_tipps.loc[game_id, AUSWAERTSTE_COL + '_Tipp'] = pd.NA

    print("\nGib deine Tipps für die folgenden Spiele ein.")
    print("Du kannst jederzeit 'q' eingeben, um die Tippabgabe zu beenden und zu speichern.")

    games_tipped_this_session = 0
    for game_id, game_row in all_games.iterrows():
        heim_team = game_row[HEIMTEAM_COL]
        auswaerts_team = game_row[AUSWAERTSTE_COL]

        tipp_heim_col = HEIMTEAM_COL + '_Tipp'
        tipp_auswaerts_col = AUSWAERTSTE_COL + '_Tipp'

        current_tipp_heim = player_tipps.loc[game_id, tipp_heim_col]
        current_tipp_auswaerts = player_tipps.loc[game_id, tipp_auswaerts_col]

        if pd.notna(current_tipp_heim) and pd.notna(current_tipp_auswaerts):
            print(f"\nSpiel {game_id}: {heim_team} vs. {auswaerts_team} (Aktueller Tipp: {int(current_tipp_heim)}:{int(current_tipp_auswaerts)})")
        else:
            print(f"\nSpiel {game_id}: {heim_team} vs. {auswaerts_team}")

        heim_score_input = get_valid_score_input(heim_team)
        if heim_score_input == 'q':
            break 

        auswaerts_score_input = get_valid_score_input(auswaerts_team)
        if auswaerts_score_input == 'q':
            break 

        player_tipps.loc[game_id, tipp_heim_col] = heim_score_input
        player_tipps.loc[game_id, tipp_auswaerts_col] = auswaerts_score_input
        games_tipped_this_session += 1
        print(f"Dein Tipp: {heim_score_input}:{auswaerts_score_input} gespeichert.")

    if games_tipped_this_session > 0 or not player_tipps.empty:
        save_player_tips(player_name_lower, player_tipps)
    else:
        print("Keine neuen Tipps abgegeben oder geändert. Keine Speicherung erforderlich.")
    
    print("\n----------------")
    print("Tippabgabe abgeschlossen.")

if __name__ == "__main__":
    main()