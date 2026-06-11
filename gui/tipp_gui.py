import tkinter as tk
from tkinter import ttk, messagebox
import os
import pandas as pd

from scripts.ranking_anzeige import (
    BASE_DIR, DATA_DIR, TIPPS_DIR, SPIELE_DATEI, ERGEBNISSE_DATEI,
    HEIMTEAM_COL, AUSWAERTSTE_COL, SPIELID_COL,
    HEIM_TORE_COL, AUSWAERTS_TORE_COL,
    load_games, load_results, load_player_tips,
    calculate_points_for_player, get_all_player_rankings,
    save_result
)

# =========================================================
# 🎨 WM 2026 FARBEN
# =========================================================
WM_BG         = "#0a0a2e"   # Dunkelblau – Hintergrund
WM_ACCENT     = "#FFD700"   # Gold
WM_ACCENT2    = "#e63946"   # Rot
WM_WHITE      = "#FFFFFF"
WM_CARD       = "#1a1a4e"   # Karten-Hintergrund
WM_GREEN      = "#2dc653"   # Erfolg
WM_GRAY       = "#3a3a5c"   # Deaktiviert
WM_TEXT_LIGHT = "#c8c8e8"   # Heller Text

# =========================================================
# 🏳️ TEAM → FLAGGEN EMOJI MAPPING
# =========================================================
TEAM_FLAGS = {
    # Gruppe A – Gastgeber
    "USA":          "🇺🇸",
    "Kanada":       "🇨🇦",
    "Mexiko":       "🇲🇽",
    # Europa
    "Deutschland":  "🇩🇪",
    "Frankreich":   "🇫🇷",
    "Spanien":      "🇪🇸",
    "England":      "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Portugal":     "🇵🇹",
    "Italien":      "🇮🇹",
    "Niederlande":  "🇳🇱",
    "Belgien":      "🇧🇪",
    "Schweiz":      "🇨🇭",
    "Kroatien":     "🇭🇷",
    "Österreich":   "🇦🇹",
    "Polen":        "🇵🇱",
    "Serbien":      "🇷🇸",
    "Dänemark":     "🇩🇰",
    "Türkei":       "🇹🇷",
    "Ukraine":      "🇺🇦",
    "Ungarn":       "🇭🇺",
    "Tschechien":   "🇨🇿",
    "Schottland":   "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Wales":        "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "Slowakei":     "🇸🇰",
    "Slowenien":    "🇸🇮",
    "Albanien":     "🇦🇱",
    "Rumänien":     "🇷🇴",
    "Georgien":     "🇬🇪",
    # Südamerika
    "Brasilien":    "🇧🇷",
    "Argentinien":  "🇦🇷",
    "Uruguay":      "🇺🇾",
    "Kolumbien":    "🇨🇴",
    "Chile":        "🇨🇱",
    "Ecuador":      "🇪🇨",
    "Peru":         "🇵🇪",
    "Venezuela":    "🇻🇪",
    "Paraguay":     "🇵🇾",
    "Bolivien":     "🇧🇴",
    # Afrika
    "Marokko":      "🇲🇦",
    "Senegal":      "🇸🇳",
    "Nigeria":      "🇳🇬",
    "Ghana":        "🇬🇭",
    "Kamerun":      "🇨🇲",
    "Elfenbeinküste":"🇨🇮",
    "Ägypten":      "🇪🇬",
    "Tunesien":     "🇹🇳",
    "Algerien":     "🇩🇿",
    "Mali":         "🇲🇱",
    "Südafrika":    "🇿🇦",
    # Asien
    "Japan":        "🇯🇵",
    "Südkorea":     "🇰🇷",
    "Iran":         "🇮🇷",
    "Saudi-Arabien":"🇸🇦",
    "Australien":   "🇦🇺",
    "Katar":        "🇶🇦",
    "China":        "🇨🇳",
    "Irak":         "🇮🇶",
    "Jordanien":    "🇯🇴",
    "Usbekistan":   "🇺🇿",
}

def get_flag(team_name):
    """Gibt die Flagge für ein Team zurück, oder ⚽ wenn unbekannt."""
    for key, flag in TEAM_FLAGS.items():
        if key.lower() in team_name.lower():
            return flag
    return "⚽"

def save_player_tips(player_name, tips_df, tips_dir=TIPPS_DIR):
    os.makedirs(tips_dir, exist_ok=True)
    file_path = os.path.join(tips_dir, f'{player_name.lower()}.csv')
    try:
        df_to_save = tips_df.copy()
        if df_to_save.index.name != SPIELID_COL:
            if SPIELID_COL in df_to_save.columns:
                df_to_save = df_to_save.set_index(SPIELID_COL)
            else:
                print(f"WARNUNG: Spalte '{SPIELID_COL}' nicht gefunden!")
        df_to_save.to_csv(file_path, index=True)
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")

def player_file_exists(player_name, tips_dir=TIPPS_DIR):
    file_path = os.path.join(tips_dir, f'{player_name.lower()}.csv')
    return os.path.exists(file_path)

class TippspielApp:
    def __init__(self, root):
        self.root = root
        self.root.title("⚽ WM 2026 Tippspiel")
        self.root.geometry("900x680")
        self.root.resizable(True, True)
        self.root.configure(bg=WM_BG)

        self.is_admin_mode = False
        self.player_name = ""
        self.all_games = pd.DataFrame()
        self.player_tips = pd.DataFrame()
        self.current_game_index = 0

        self._apply_styles()
        self._build_header()
        self._build_notebook()
        self._build_statusbar()

        self.update_results_table()
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    # =========================================================
    # 🎨 STYLING
    # =========================================================
    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Notebook
        style.configure('TNotebook',
            background=WM_BG, borderwidth=0)
        style.configure('TNotebook.Tab',
            background=WM_CARD, foreground=WM_TEXT_LIGHT,
            font=('Arial', 11, 'bold'), padding=[15, 8])
        style.map('TNotebook.Tab',
            background=[('selected', WM_ACCENT)],
            foreground=[('selected', WM_BG)])

        # Frames
        style.configure('TFrame', background=WM_BG)
        style.configure('Card.TFrame', background=WM_CARD, relief='flat')

        # Labels
        style.configure('TLabel', background=WM_BG, foreground=WM_WHITE, font=('Arial', 10))
        style.configure('Title.TLabel', background=WM_BG, foreground=WM_ACCENT,
            font=('Arial', 16, 'bold'))
        style.configure('Card.TLabel', background=WM_CARD, foreground=WM_WHITE, font=('Arial', 10))
        style.configure('CardTitle.TLabel', background=WM_CARD, foreground=WM_ACCENT,
            font=('Arial', 13, 'bold'))

        # Buttons
        style.configure('Gold.TButton',
            background=WM_ACCENT, foreground=WM_BG,
            font=('Arial', 11, 'bold'), padding=[12, 6], borderwidth=0)
        style.map('Gold.TButton',
            background=[('active', '#FFC200')])

        style.configure('Red.TButton',
            background=WM_ACCENT2, foreground=WM_WHITE,
            font=('Arial', 10, 'bold'), padding=[10, 5], borderwidth=0)
        style.map('Red.TButton',
            background=[('active', '#c1121f')])

        style.configure('Ghost.TButton',
            background=WM_GRAY, foreground=WM_WHITE,
            font=('Arial', 10), padding=[10, 5], borderwidth=0)
        style.map('Ghost.TButton',
            background=[('active', '#4a4a7c')])

        # Entries
        style.configure('TEntry', fieldbackground=WM_CARD,
            foreground=WM_WHITE, insertcolor=WM_WHITE, font=('Arial', 12))

        # Treeview
        style.configure('Treeview',
            background=WM_CARD, foreground=WM_WHITE,
            fieldbackground=WM_CARD, font=('Arial', 10),
            rowheight=28)
        style.configure('Treeview.Heading',
            background=WM_ACCENT, foreground=WM_BG,
            font=('Arial', 10, 'bold'))
        style.map('Treeview',
            background=[('selected', WM_ACCENT)],
            foreground=[('selected', WM_BG)])

        # Scrollbar
        style.configure('TScrollbar', background=WM_GRAY, troughcolor=WM_BG)

    # =========================================================
    # 🏆 HEADER
    # =========================================================
    def _build_header(self):
        header = tk.Frame(self.root, bg=WM_CARD, height=70)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🏆  WM 2026  TIPPSPIEL  🏆",
            bg=WM_CARD, fg=WM_ACCENT,
            font=('Arial', 20, 'bold')
        ).pack(side="left", padx=25, pady=15)

        tk.Label(
            header,
            text="🇺🇸 🇨🇦 🇲🇽",
            bg=WM_CARD, fg=WM_WHITE,
            font=('Arial', 18)
        ).pack(side="right", padx=25, pady=15)

    # =========================================================
    # 📓 NOTEBOOK
    # =========================================================
    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root, style='TNotebook')
        self.notebook.pack(expand=True, fill="both", padx=10, pady=(5, 0))

        self.tipping_tab = ttk.Frame(self.notebook, style='TFrame', padding="15")
        self.notebook.add(self.tipping_tab, text="🎯  Tippabgabe")
        self.create_tipping_tab()

        self.ranking_tab = ttk.Frame(self.notebook, style='TFrame', padding="15")
        self.notebook.add(self.ranking_tab, text="🏅  Ranking")
        self.create_ranking_tab()

        self.results_tab = ttk.Frame(self.notebook, style='TFrame', padding="15")
        self.notebook.add(self.results_tab, text="📊  Ergebnisse")
        self.create_results_tab()

        if self.is_admin_mode:
            self.admin_tab = ttk.Frame(self.notebook, style='TFrame', padding="15")
            self.notebook.add(self.admin_tab, text="🔧  Admin")
            self.create_admin_tab()

    # =========================================================
    # 📊 STATUSBAR
    # =========================================================
    def _build_statusbar(self):
        self.status_label = tk.Label(
            self.root,
            text="⚽  Bereit. Gib deinen Namen ein, um zu starten.",
            bg=WM_CARD, fg=WM_TEXT_LIGHT,
            font=('Arial', 9), anchor="w", padx=10
        )
        self.status_label.pack(side="bottom", fill="x", ipady=4)

    # =========================================================
    # TAB 1: TIPPABGABE
    # =========================================================
    def create_tipping_tab(self):

        # --- Login Card ---
        login_card = tk.Frame(self.tipping_tab, bg=WM_CARD, bd=0)
        login_card.pack(fill="x", pady=(0, 10), ipady=15, ipadx=10)

        tk.Label(login_card, text="👤  Dein Name:", bg=WM_CARD,
                fg=WM_ACCENT, font=('Arial', 12, 'bold')).grid(
            row=0, column=0, padx=15, pady=10, sticky="w")

        self.name_entry = ttk.Entry(login_card, width=28, font=('Arial', 12))
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)
        self.name_entry.focus_set()
        self.name_entry.bind("<Return>", lambda e: self.start_tipping())
        self.name_entry.bind("<KeyRelease>", self.check_player_exists)

        ttk.Button(login_card, text="Einloggen ▶",
                command=self.start_tipping, style='Gold.TButton').grid(
            row=0, column=2, padx=10, pady=10)

        self.login_info_label = tk.Label(
            login_card, text="", bg=WM_CARD,
            font=('Arial', 10, 'italic'), fg=WM_TEXT_LIGHT)
        self.login_info_label.grid(row=1, column=0, columnspan=3, pady=(0, 5))

        # --- Regeln Card ---
        rules_card = tk.Frame(self.tipping_tab, bg=WM_CARD, bd=0)
        rules_card.pack(fill="x", pady=(0, 10), ipady=10, ipadx=15)

        tk.Label(rules_card, text="📋  Punkte-Regeln", bg=WM_CARD,
                fg=WM_ACCENT, font=('Arial', 11, 'bold')).pack(anchor="w", padx=15, pady=(8, 2))

        rules_text = (
            "  🥇  4 Punkte – Exakter Tipp (z.B. Tipp 2:1 → Ergebnis 2:1)\n"
            "  ✅  1 Punkt  – Richtiger Spielausgang (Sieg / Unentschieden / Niederlage)\n"
            "  ➕  2 Punkte – Richtige Tordifferenz (z.B. Tipp 2:1 → Ergebnis 3:2)\n\n"
            "  💡  Format: Vorname_Nachname  |  Melde dich immer mit dem gleichen Namen an!"
        )
        tk.Label(rules_card, text=rules_text, bg=WM_CARD, fg=WM_TEXT_LIGHT,
                font=('Arial', 10), justify="left").pack(anchor="w", padx=15, pady=(0, 8))

        # =========================================================
        # ✅ SPIEL CARD – Nav-Buttons INNERHALB der Card!
        # =========================================================
        self.game_card = tk.Frame(self.tipping_tab, bg=WM_CARD, bd=0)
        # Noch nicht packen – erst nach Login

        # Zeile 0: Spiel-Titel
        self.game_label = tk.Label(
            self.game_card, text="Spiel:", bg=WM_CARD,
            fg=WM_ACCENT, font=('Arial', 15, 'bold'))
        self.game_label.grid(row=0, column=0, columnspan=7, pady=(15, 10), padx=20)

        # Zeile 1: Flagge | Team | Eingabe : Eingabe | Team | Flagge
        self.team1_flag_label = tk.Label(
            self.game_card, text="⚽", bg=WM_CARD, fg=WM_WHITE, font=('Arial', 28))
        self.team1_flag_label.grid(row=1, column=0, padx=(20, 5), pady=10)

        self.team1_name_label = tk.Label(
            self.game_card, text="Heimteam", bg=WM_CARD,
            fg=WM_WHITE, font=('Arial', 12, 'bold'))
        self.team1_name_label.grid(row=1, column=1, padx=5, pady=10)

        self.team1_entry = ttk.Entry(self.game_card, width=4,
                                    font=('Arial', 16, 'bold'), justify='center')
        self.team1_entry.grid(row=1, column=2, padx=10, pady=10)

        tk.Label(self.game_card, text=":", bg=WM_CARD,
                fg=WM_ACCENT, font=('Arial', 20, 'bold')).grid(row=1, column=3, padx=5)

        self.team2_entry = ttk.Entry(self.game_card, width=4,
                                    font=('Arial', 16, 'bold'), justify='center')
        self.team2_entry.grid(row=1, column=4, padx=10, pady=10)

        self.team2_name_label = tk.Label(
            self.game_card, text="Auswärtsteam", bg=WM_CARD,
            fg=WM_WHITE, font=('Arial', 12, 'bold'))
        self.team2_name_label.grid(row=1, column=5, padx=5, pady=10)

        self.team2_flag_label = tk.Label(
            self.game_card, text="⚽", bg=WM_CARD, fg=WM_WHITE, font=('Arial', 28))
        self.team2_flag_label.grid(row=1, column=6, padx=(5, 20), pady=10)

        # Zeile 2: Tipp speichern Button
        self.save_tip_button = ttk.Button(
            self.game_card, text="💾  Tipp speichern",
            command=self.save_current_tip, style='Gold.TButton')
        self.save_tip_button.grid(row=2, column=0, columnspan=7, pady=(10, 5))

        # ✅ Zeile 3: Navigation INNERHALB der game_card!
        nav_inner = tk.Frame(self.game_card, bg=WM_CARD)
        nav_inner.grid(row=3, column=0, columnspan=7, pady=(5, 15))

        self.prev_button = ttk.Button(
            nav_inner, text="◀  Vorheriges",
            command=self.show_previous_game, style='Ghost.TButton')
        self.prev_button.grid(row=0, column=0, padx=10)

        self.next_button = ttk.Button(
            nav_inner, text="Nächstes  ▶",
            command=self.show_next_game, style='Ghost.TButton')
        self.next_button.grid(row=0, column=1, padx=10)

        self.finish_button = ttk.Button(
            nav_inner, text="✅  Alle Tipps speichern & beenden",
            command=self.finish_tipping, style='Red.TButton')
        self.finish_button.grid(row=0, column=2, padx=10)

    def check_player_exists(self, event=None):
        name = self.name_entry.get().strip()
        if not name:
            self.login_info_label.config(text="", fg=WM_TEXT_LIGHT)
            return
        if player_file_exists(name):
            self.login_info_label.config(
                text=f"✅  Willkommen zurück, {name}! Deine Tipps werden geladen.",
                fg=WM_GREEN)
        else:
            self.login_info_label.config(
                text=f"🆕  Neuer Spieler: {name} – ein neues Profil wird erstellt.",
                fg=WM_ACCENT)

    def start_tipping(self):
        player_name_input = self.name_entry.get().strip()
        if not player_name_input:
            messagebox.showwarning("Eingabefehler", "Bitte gib deinen Namen ein!")
            return

        self.player_name = player_name_input
        self.all_games   = load_games()
        if self.all_games.empty:
            messagebox.showerror("Fehler", "Keine Spiele gefunden!")
            return

        is_returning     = player_file_exists(self.player_name)
        self.player_tips = load_player_tips(self.player_name)

        if self.player_tips.empty:
            self.player_tips = pd.DataFrame(index=self.all_games.index)
            self.player_tips[HEIMTEAM_COL    + '_Tipp'] = pd.NA
            self.player_tips[AUSWAERTSTE_COL + '_Tipp'] = pd.NA
        else:
            for game_id in self.all_games.index:
                if game_id not in self.player_tips.index:
                    self.player_tips.loc[game_id, HEIMTEAM_COL    + '_Tipp'] = pd.NA
                    self.player_tips.loc[game_id, AUSWAERTSTE_COL + '_Tipp'] = pd.NA
            if HEIMTEAM_COL + '_Tipp' not in self.player_tips.columns:
                self.player_tips[HEIMTEAM_COL + '_Tipp'] = pd.NA
            if AUSWAERTSTE_COL + '_Tipp' not in self.player_tips.columns:
                self.player_tips[AUSWAERTSTE_COL + '_Tipp'] = pd.NA

        # ✅ Nur game_card packen – nav ist jetzt drin!
        self.game_card.pack(fill="x", pady=10, ipady=10)

        self.current_game_index = 0
        self.display_current_game()

        if is_returning:
            self.status_label.config(
                text=f"👋  Willkommen zurück, {self.player_name}! Deine gespeicherten Tipps wurden geladen.")
        else:
            self.status_label.config(
                text=f"🆕  Neues Profil erstellt für {self.player_name}. Viel Erfolg! 🍀")

        self.update_results_table()

    def display_current_game(self):
        if not self.all_games.empty and 0 <= self.current_game_index < len(self.all_games):
            game_id        = self.all_games.index[self.current_game_index]
            game_row       = self.all_games.loc[game_id]
            heim_team      = game_row[HEIMTEAM_COL]
            auswaerts_team = game_row[AUSWAERTSTE_COL]

            heim_flag      = get_flag(heim_team)
            auswaerts_flag = get_flag(auswaerts_team)

            self.root.title(f"⚽ WM 2026 Tippspiel – {self.player_name} – Spiel {game_id}")
            self.game_label.config(
                text=f"Spiel {game_id}  |  {heim_flag} {heim_team}  vs.  {auswaerts_team} {auswaerts_flag}")
            self.team1_name_label.config(text=heim_team)
            self.team2_name_label.config(text=auswaerts_team)
            self.team1_flag_label.config(text=heim_flag)
            self.team2_flag_label.config(text=auswaerts_flag)

            current_heim      = self.player_tips.loc[game_id, HEIMTEAM_COL    + '_Tipp']
            current_auswaerts = self.player_tips.loc[game_id, AUSWAERTSTE_COL + '_Tipp']

            self.team1_entry.delete(0, tk.END)
            self.team2_entry.delete(0, tk.END)
            if pd.notna(current_heim):
                self.team1_entry.insert(0, str(int(current_heim)))
            if pd.notna(current_auswaerts):
                self.team2_entry.insert(0, str(int(current_auswaerts)))

            # 🔒 Sperren wenn Ergebnis vorhanden
            results = load_results()
            ergebnis_vorhanden = (
                game_id in results.index
                and pd.notna(results.loc[game_id, HEIM_TORE_COL])
                and pd.notna(results.loc[game_id, AUSWAERTS_TORE_COL])
            )

            if ergebnis_vorhanden:
                self.team1_entry.config(state='disabled')
                self.team2_entry.config(state='disabled')
                self.save_tip_button.config(state='disabled')
                h = int(results.loc[game_id, HEIM_TORE_COL])
                a = int(results.loc[game_id, AUSWAERTS_TORE_COL])
                self.game_label.config(
                    text=f"Spiel {game_id}  |  {heim_flag} {heim_team}  {h} : {a}  {auswaerts_team} {auswaerts_flag}  🔒")
            else:
                self.team1_entry.config(state='normal')
                self.team2_entry.config(state='normal')
                self.save_tip_button.config(state='normal')

            self.prev_button.config(
                state=tk.NORMAL if self.current_game_index > 0 else tk.DISABLED)
            self.next_button.config(
                state=tk.NORMAL if self.current_game_index < len(self.all_games) - 1 else tk.DISABLED)
            self.status_label.config(
                text=f"Spiel {self.current_game_index + 1} von {len(self.all_games)}:  "
                     f"{heim_flag} {heim_team}  vs.  {auswaerts_team} {auswaerts_flag}"
                     + ("  🔒 Gesperrt" if ergebnis_vorhanden else ""))
        else:
            self.game_label.config(text="Keine Spiele verfügbar.")
            self.team1_name_label.config(text="Heimteam")
            self.team2_name_label.config(text="Auswärtsteam")
            self.team1_flag_label.config(text="⚽")
            self.team2_flag_label.config(text="⚽")
            self.team1_entry.delete(0, tk.END)
            self.team2_entry.delete(0, tk.END)
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.save_tip_button.config(state=tk.DISABLED)
            self.status_label.config(text="Keine Spiele geladen oder verfügbar.")

    def save_current_tip(self):
        game_id            = self.all_games.index[self.current_game_index]
        heim_tipp_str      = self.team1_entry.get().strip()
        auswaerts_tipp_str = self.team2_entry.get().strip()

        results = load_results()
        if (game_id in results.index
                and pd.notna(results.loc[game_id, HEIM_TORE_COL])
                and pd.notna(results.loc[game_id, AUSWAERTS_TORE_COL])):
            messagebox.showwarning("Gesperrt 🔒",
                f"Spiel {game_id} hat bereits ein Ergebnis.\nDein Tipp kann nicht mehr geändert werden!")
            return

        if not heim_tipp_str and not auswaerts_tipp_str:
            messagebox.showinfo("Info", "Keine Tipps eingegeben. Nichts gespeichert.")
            return

        try:
            heim_tipp      = int(heim_tipp_str)      if heim_tipp_str      else pd.NA
            auswaerts_tipp = int(auswaerts_tipp_str) if auswaerts_tipp_str else pd.NA

            if heim_tipp is not pd.NA and heim_tipp < 0:
                messagebox.showwarning("Ungültige Eingabe", "Tore können nicht negativ sein.")
                return
            if auswaerts_tipp is not pd.NA and auswaerts_tipp < 0:
                messagebox.showwarning("Ungültige Eingabe", "Tore können nicht negativ sein.")
                return

            self.player_tips.loc[game_id, HEIMTEAM_COL    + '_Tipp'] = heim_tipp
            self.player_tips.loc[game_id, AUSWAERTSTE_COL + '_Tipp'] = auswaerts_tipp

            save_player_tips(self.player_name, self.player_tips)
            self.update_results_table()
            messagebox.showinfo("✅ Gespeichert",
                f"Tipp für Spiel {game_id} gespeichert: {heim_tipp_str} : {auswaerts_tipp_str}")

        except ValueError:
            messagebox.showwarning("Ungültige Eingabe", "Bitte nur ganze Zahlen eingeben.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Unerwarteter Fehler: {e}")

    def show_next_game(self):
        if self.current_game_index < len(self.all_games) - 1:
            self.current_game_index += 1
            self.display_current_game()

    def show_previous_game(self):
        if self.current_game_index > 0:
            self.current_game_index -= 1
            self.display_current_game()

    def finish_tipping(self):
        if messagebox.askyesno("Tippabgabe beenden", "Möchtest du alle Tipps speichern?"):
            save_player_tips(self.player_name, self.player_tips)
            messagebox.showinfo("🏆 Abgeschlossen", "Deine Tipps wurden gespeichert! Viel Glück! 🍀")
            self.root.destroy()

    # =========================================================
    # TAB 2: RANKING
    # =========================================================
    def create_ranking_tab(self):
        tk.Label(self.ranking_tab, text="🏅  Aktuelles Ranking",
                 bg=WM_BG, fg=WM_ACCENT, font=('Arial', 14, 'bold')).pack(pady=(0, 10))

        self.ranking_tree = ttk.Treeview(
            self.ranking_tab,
            columns=('Rang', 'Spieler', 'Punkte'),
            show='headings'
        )
        self.ranking_tree.heading('Rang',    text='🏆  Rang')
        self.ranking_tree.heading('Spieler', text='👤  Spieler')
        self.ranking_tree.heading('Punkte',  text='⭐  Punkte')
        self.ranking_tree.column('Rang',    width=80,  anchor='center')
        self.ranking_tree.column('Spieler', width=200, anchor='w')
        self.ranking_tree.column('Punkte',  width=100, anchor='center')
        self.ranking_tree.pack(pady=5, fill="both", expand=True)

        ttk.Button(self.ranking_tab, text="🔄  Ranking aktualisieren",
                   command=self.update_ranking, style='Gold.TButton').pack(pady=10)

    def update_ranking(self):
        for item in self.ranking_tree.get_children():
            self.ranking_tree.delete(item)
        try:
            ranking_df = get_all_player_rankings()
            if not ranking_df.empty:
                medals = ["🥇", "🥈", "🥉"]
                for i, (_, row) in enumerate(ranking_df.iterrows()):
                    rang = medals[i] if i < 3 else str(row['Rang'])
                    self.ranking_tree.insert("", "end",
                        values=(rang, row['Spieler'], row['Punkte']))
                self.status_label.config(text="🏅  Ranking aktualisiert.")
            else:
                self.status_label.config(text="Noch kein Ranking verfügbar.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden des Rankings:\n{e}")

    # =========================================================
    # TAB 3: ERGEBNISSE
    # =========================================================
    def create_results_tab(self):
        tk.Label(self.results_tab, text="📊  Spielergebnisse Übersicht",
                 bg=WM_BG, fg=WM_ACCENT, font=('Arial', 14, 'bold')).pack(pady=(0, 10))

        tree_frame = tk.Frame(self.results_tab, bg=WM_BG)
        tree_frame.pack(fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.results_tree = ttk.Treeview(
            tree_frame,
            columns=('SpielID', 'Heimteam', 'MeinTipp', 'Ergebnis', 'Auswaertsteam'),
            show='headings',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        v_scrollbar.config(command=self.results_tree.yview)
        h_scrollbar.config(command=self.results_tree.xview)

        self.results_tree.heading('SpielID',       text='#')
        self.results_tree.heading('Heimteam',      text='🏠  Heimteam')
        self.results_tree.heading('MeinTipp',      text='🎯  Mein Tipp')
        self.results_tree.heading('Ergebnis',      text='📋  Ergebnis')
        self.results_tree.heading('Auswaertsteam', text='✈️  Auswärtsteam')

        self.results_tree.column('SpielID',       width=40,  anchor='center')
        self.results_tree.column('Heimteam',      width=200, anchor='e')
        self.results_tree.column('MeinTipp',      width=100, anchor='center')
        self.results_tree.column('Ergebnis',      width=100, anchor='center')
        self.results_tree.column('Auswaertsteam', width=200, anchor='w')

        self.results_tree.tag_configure('gespielt',   background='#1a3a2a', foreground='#2dc653')
        self.results_tree.tag_configure('ungespielt', background=WM_CARD,   foreground=WM_TEXT_LIGHT)

        self.results_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        ttk.Button(self.results_tab, text="🔄  Aktualisieren",
                   command=self.update_results_table, style='Gold.TButton').pack(pady=10)

    def update_results_table(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        try:
            games   = load_games()
            results = load_results()
            my_tips = pd.DataFrame()
            if self.player_name:
                my_tips = load_player_tips(self.player_name)

            if games.empty:
                self.results_tree.insert("", "end",
                    values=("–", "Keine Spiele gefunden", "–", "–", "–"))
                return

            for game_id, game in games.iterrows():
                heim      = game[HEIMTEAM_COL]
                auswaerts = game[AUSWAERTSTE_COL]
                heim_flag = get_flag(heim)
                aus_flag  = get_flag(auswaerts)

                if (game_id in results.index
                        and pd.notna(results.loc[game_id, HEIM_TORE_COL])
                        and pd.notna(results.loc[game_id, AUSWAERTS_TORE_COL])):
                    h = int(results.loc[game_id, HEIM_TORE_COL])
                    a = int(results.loc[game_id, AUSWAERTS_TORE_COL])
                    ergebnis = f"{h}  :  {a}"
                    tag      = 'gespielt'
                else:
                    ergebnis = "-  :  -"
                    tag      = 'ungespielt'

                mein_tipp = "-  :  -"
                if not my_tips.empty and game_id in my_tips.index:
                    t_h = my_tips.loc[game_id, HEIMTEAM_COL    + '_Tipp']
                    t_a = my_tips.loc[game_id, AUSWAERTSTE_COL + '_Tipp']
                    if pd.notna(t_h) and pd.notna(t_a):
                        mein_tipp = f"{int(t_h)}  :  {int(t_a)}"

                self.results_tree.insert("", "end",
                    values=(game_id,
                            f"{heim_flag}  {heim}",
                            mein_tipp,
                            ergebnis,
                            f"{auswaerts}  {aus_flag}"),
                    tags=(tag,))

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Fehler", f"Fehler:\n{e}")

    # =========================================================
    # TAB 4: ADMIN
    # =========================================================
    def create_admin_tab(self):
        tk.Label(self.admin_tab, text="🔧  Admin: Spielergebnisse eingeben",
                 bg=WM_BG, fg=WM_ACCENT, font=('Arial', 14, 'bold')).pack(pady=(0, 10))

        self.admin_games_frame = tk.Frame(self.admin_tab, bg=WM_BG)
        self.admin_games_frame.pack(pady=5, padx=5, fill="both", expand=True)

        self.admin_canvas    = tk.Canvas(self.admin_games_frame, bg=WM_BG, highlightthickness=0)
        self.admin_scrollbar = ttk.Scrollbar(self.admin_games_frame,
                                             orient="vertical", command=self.admin_canvas.yview)
        self.admin_scrollable_frame = tk.Frame(self.admin_canvas, bg=WM_BG)

        self.admin_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.admin_canvas.configure(
                scrollregion=self.admin_canvas.bbox("all")))

        self.admin_canvas.create_window((0, 0), window=self.admin_scrollable_frame, anchor="nw")
        self.admin_canvas.configure(yscrollcommand=self.admin_scrollbar.set)
        self.admin_canvas.pack(side="left", fill="both", expand=True)
        self.admin_scrollbar.pack(side="right", fill="y")

        self.admin_entries = {}
        self.load_games_for_admin()

        ttk.Button(self.admin_tab, text="💾  Ergebnisse speichern",
                   command=self.save_results_admin, style='Gold.TButton').pack(pady=10)

    def load_games_for_admin(self):
        for widget in self.admin_scrollable_frame.winfo_children():
            widget.destroy()
        self.admin_entries.clear()

        games   = load_games()
        results = load_results()

        if games.empty:
            tk.Label(self.admin_scrollable_frame, text="Keine Spiele vorhanden.",
                     bg=WM_BG, fg=WM_WHITE).pack(pady=5)
            return

        for game_id, game in games.iterrows():
            heim      = game[HEIMTEAM_COL]
            auswaerts = game[AUSWAERTSTE_COL]
            heim_flag = get_flag(heim)
            aus_flag  = get_flag(auswaerts)

            row_frame = tk.Frame(self.admin_scrollable_frame,
                                 bg=WM_CARD, relief="flat", bd=0)
            row_frame.pack(fill="x", padx=5, pady=3, ipady=5)

            tk.Label(row_frame,
                     text=f"  Spiel {game_id}:  {heim_flag} {heim}  vs.  {auswaerts} {aus_flag}",
                     bg=WM_CARD, fg=WM_WHITE,
                     font=('Arial', 10, 'bold')).pack(side="left", padx=10)

            heim_entry = ttk.Entry(row_frame, width=5, font=('Arial', 11), justify='center')
            heim_entry.pack(side="left", padx=5)

            tk.Label(row_frame, text=":", bg=WM_CARD,
                     fg=WM_ACCENT, font=('Arial', 14, 'bold')).pack(side="left")

            auswaerts_entry = ttk.Entry(row_frame, width=5, font=('Arial', 11), justify='center')
            auswaerts_entry.pack(side="left", padx=5)

            if game_id in results.index:
                if pd.notna(results.loc[game_id, HEIM_TORE_COL]):
                    heim_entry.insert(0, str(int(results.loc[game_id, HEIM_TORE_COL])))
                if pd.notna(results.loc[game_id, AUSWAERTS_TORE_COL]):
                    auswaerts_entry.insert(0, str(int(results.loc[game_id, AUSWAERTS_TORE_COL])))

            self.admin_entries[game_id] = {'heim': heim_entry, 'auswaerts': auswaerts_entry}

    def save_results_admin(self):
        all_successful = True
        for game_id, entries in self.admin_entries.items():
            heim_str      = entries['heim'].get().strip()
            auswaerts_str = entries['auswaerts'].get().strip()

            if not heim_str and not auswaerts_str:
                continue
            if bool(heim_str) != bool(auswaerts_str):
                messagebox.showwarning("Fehler",
                    f"Spiel {game_id}: Bitte beide Tore oder keines eingeben.")
                all_successful = False
                continue
            try:
                heim_tore      = int(heim_str)
                auswaerts_tore = int(auswaerts_str)
                if heim_tore < 0 or auswaerts_tore < 0:
                    messagebox.showwarning("Fehler",
                        f"Spiel {game_id}: Tore können nicht negativ sein.")
                    all_successful = False
                    continue
                save_result(game_id, heim_tore, auswaerts_tore)
            except ValueError:
                messagebox.showerror("Fehler",
                    f"Spiel {game_id}: Nur ganze Zahlen erlaubt.")
                all_successful = False
            except Exception as e:
                messagebox.showerror("Fehler",
                    f"Spiel {game_id}: Unerwarteter Fehler: {e}")
                all_successful = False

        if all_successful:
            messagebox.showinfo("✅ Erfolg", "Alle Ergebnisse erfolgreich gespeichert!")
            self.update_ranking()
            self.update_results_table()
            self.load_games_for_admin()
        else:
            messagebox.showwarning("Hinweis",
                "Einige Ergebnisse konnten nicht gespeichert werden.")

    # =========================================================
    # TAB-WECHSEL
    # =========================================================
    def on_tab_change(self, event):
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if "Ranking" in selected_tab:
            self.update_ranking()
        elif "Ergebnisse" in selected_tab:
            self.update_results_table()
        elif "Admin" in selected_tab and self.is_admin_mode:
            self.load_games_for_admin()

if __name__ == "__main__":
    root = tk.Tk()
    app = TippspielApp(root)
    root.mainloop()