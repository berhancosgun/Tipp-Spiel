#ergebnis_eintragen.py

import pandas as pd
import os

# Konstanten für die Dateinamen und Spalten
SPIELE_DATEI = 'spiele.csv'
ERGEBNISSE_DATEI = 'ergebnisse.csv'

SPIELID_COL = 'SpielID'
HEIMTEAM_COL = 'Heimteam'
AUSWAERTSTE_COL = 'Auswärtsteam'
ERGEBNIS_HEIM_COL = 'ErgebnisHeim'
ERGEBNIS_AUSWAERTS_COL = 'ErgebnisAuswaerts'

def load_csv_file(file_path, index_col=None):
    """Lädt eine CSV-Datei und gibt einen DataFrame zurück."""
    try:
        df = pd.read_csv(file_path, index_col=index_col)
        return df
    except FileNotFoundError:
        # Wenn die Datei nicht existiert, gib einen leeren DataFrame zurück
        # mit den erwarteten Spalten, damit wir ihn später füllen können.
        if file_path == ERGEBNISSE_DATEI:
            print(f"Info: '{ERGEBNISSE_DATEI}' nicht gefunden. Wird neu erstellt.")
            # Erstelle einen leeren DataFrame mit den richtigen Spalten und Index-Namen
            return pd.DataFrame(columns=[ERGEBNIS_HEIM_COL, ERGEBNIS_AUSWAERTS_COL]).rename_axis(SPIELID_COL)
        print(f"Fehler: Datei '{file_path}' nicht gefunden.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Fehler beim Laden von '{file_path}': {e}")
        return pd.DataFrame()

def save_csv_file(df, file_path):
    """Speichert einen DataFrame in eine CSV-Datei."""
    try:
        # Stellen Sie sicher, dass der Index einen Namen hat, bevor er gespeichert wird
        if df.index.name is None:
            df.index.name = SPIELID_COL
        df.to_csv(file_path, index=True) # index=True, damit der Index als erste Spalte gespeichert wird
        print(f"'{file_path}' erfolgreich gespeichert.")
    except Exception as e:
        print(f"Fehler beim Speichern von '{file_path}': {e}")

def get_valid_score_input(prompt):
    """Fordert den Benutzer zur Eingabe einer gültigen Torzahl auf."""
    while True:
        score_str = input(prompt).strip()
        if score_str.lower() == 'q':
            return 'q'
        if score_str.isdigit() and int(score_str) >= 0:
            return int(score_str)
        else:
            print("Ungültige Eingabe. Bitte gib eine positive ganze Zahl für die Tore ein oder 'q' zum Abbrechen.")

def main():
    print("⚽ Ergebnisse eintragen ⚽")
    print("--------------------------")

    # 1. Spiele laden
    all_games = load_csv_file(SPIELE_DATEI, index_col=SPIELID_COL)
    if all_games.empty:
        print("Fehler: Keine Spiele in 'spiele.csv' gefunden. Bitte stelle sicher, dass die Datei existiert und Daten enthält.")
        return

    # 2. Bestehende Ergebnisse laden
    all_results = load_csv_file(ERGEBNISSE_DATEI, index_col=SPIELID_COL)
    
    # Sicherstellen, dass die Spalten für Ergebnisse existieren und der Indexname gesetzt ist
    if ERGEBNIS_HEIM_COL not in all_results.columns:
        all_results[ERGEBNIS_HEIM_COL] = pd.NA
    if ERGEBNIS_AUSWAERTS_COL not in all_results.columns:
        all_results[ERGEBNIS_AUSWAERTS_COL] = pd.NA
    
    # Wichtig: Setze den Indexnamen explizit, falls er beim Laden verloren gegangen ist
    all_results.index.name = SPIELID_COL

    # 3. Spiele finden, für die noch keine Ergebnisse eingetragen sind
    games_to_enter = []
    # Iteriere über alle Spiele, um zu prüfen, ob Ergebnisse bereits existieren
    for game_id in all_games.index:
        game_row = all_games.loc[game_id]
        
        # Prüfen, ob das Spiel in all_results ist und ob die Ergebnisspalten NA sind
        if game_id not in all_results.index or \
           pd.isna(all_results.loc[game_id, ERGEBNIS_HEIM_COL]) or \
           pd.isna(all_results.loc[game_id, ERGEBNIS_AUSWAERTS_COL]):
            games_to_enter.append((game_id, game_row[HEIMTEAM_COL], game_row[AUSWAERTSTE_COL]))

    if not games_to_enter:
        print("Alle Spiele haben bereits Ergebnisse. Nichts einzutragen.")
        # Wenn alle Spiele Ergebnisse haben, aber der Benutzer trotzdem etwas ändern will, 
        # kann er eine ID eingeben. Die Liste ist nur für die Übersicht.
        # Wir fahren trotzdem fort, damit man bestehende Ergebnisse überschreiben kann.
        pass # Weitergehen, um manuelle Eingabe zu erlauben

    if games_to_enter: # Nur anzeigen, wenn auch welche fehlen
        print("\nFolgende Spiele warten auf Ergebnisse:")
        for game_id, heim, auswaerts in games_to_enter:
            print(f"  {game_id}: {heim} vs. {auswaerts}")

    print("\nGib die Spiel-ID ein, für die du ein Ergebnis eintragen möchtest.")
    print("Gib 'q' ein, um das Eintragen zu beenden.")

    while True:
        game_id_input = input("\nSpiel-ID eingeben (oder 'q' zum Beenden): ").strip()

        if game_id_input.lower() == 'q':
            break

        try:
            game_id = int(game_id_input)
        except ValueError:
            print("Ungültige Eingabe. Bitte gib eine Zahl für die Spiel-ID ein.")
            continue

        if game_id not in all_games.index:
            print(f"Spiel-ID {game_id} existiert nicht in 'spiele.csv'.")
            continue

        # Prüfen, ob das Spiel bereits ein Ergebnis hat
        # Sicherstellen, dass die Zeile für game_id im all_results DataFrame existiert,
        # bevor auf Spalten zugegriffen wird.
        if game_id in all_results.index:
            current_heim_score = all_results.loc[game_id, ERGEBNIS_HEIM_COL]
            current_auswaerts_score = all_results.loc[game_id, ERGEBNIS_AUSWAERTS_COL]
        else:
            current_heim_score = pd.NA
            current_auswaerts_score = pd.NA

        if pd.notna(current_heim_score) and pd.notna(current_auswaerts_score):
            print(f"Für Spiel {game_id} ({all_games.loc[game_id, HEIMTEAM_COL]} vs. {all_games.loc[game_id, AUSWAERTSTE_COL]})")
            print(f"ist bereits das Ergebnis {int(current_heim_score)}:{int(current_auswaerts_score)} eingetragen.")
            overwrite = input("Möchtest du es überschreiben? (j/n): ").strip().lower()
            if overwrite != 'j':
                continue

        # Ergebnis eingeben
        print(f"\nErgebnis für Spiel {game_id}: {all_games.loc[game_id, HEIMTEAM_COL]} vs. {all_games.loc[game_id, AUSWAERTSTE_COL]}")
        
        heim_score = get_valid_score_input(f"Tore für {all_games.loc[game_id, HEIMTEAM_COL]} (oder 'q' zum Abbrechen): ")
        if heim_score == 'q':
            break

        auswaerts_score = get_valid_score_input(f"Tore für {all_games.loc[game_id, AUSWAERTSTE_COL]} (oder 'q' zum Abbrechen): ")
        if auswaerts_score == 'q':
            break

        # Ergebnis im DataFrame speichern
        # Falls die Spiel-ID noch nicht im Index von all_results ist, füge sie hinzu
        if game_id not in all_results.index:
            all_results.loc[game_id] = [pd.NA, pd.NA] # Füge eine leere Zeile hinzu
        
        all_results.loc[game_id, ERGEBNIS_HEIM_COL] = heim_score
        all_results.loc[game_id, ERGEBNIS_AUSWAERTS_COL] = auswaerts_score
        print(f"Ergebnis {heim_score}:{auswaerts_score} für Spiel {game_id} eingetragen.")

    # Ergebnisse speichern
    save_csv_file(all_results, ERGEBNISSE_DATEI)
    print("\n--------------------------")
    print("Ergebniseingabe abgeschlossen.")

if __name__ == "__main__":
    main()