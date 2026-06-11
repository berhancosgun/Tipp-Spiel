import streamlit as st
import pandas as pd
import os

from scripts.ranking_anzeige import (
    BASE_DIR, DATA_DIR, TIPPS_DIR, SPIELE_DATEI, ERGEBNISSE_DATEI,
    HEIMTEAM_COL, AUSWAERTSTE_COL, SPIELID_COL,
    HEIM_TORE_COL, AUSWAERTS_TORE_COL,
    load_games, load_results, load_player_tips,
    calculate_points_for_player, get_all_player_rankings,
    save_result
)

def safe_int(value, default=0):
    try:
        if value is None or value == '' or (isinstance(value, float) and pd.isna(value)):
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

# =========================================================
# PASSWORT-SCHUTZ
# =========================================================
USERS = {
    st.secrets["player_password"]: "user",
    st.secrets["admin_password"]:  "admin",
}

def check_password():
    if "auth_ok" not in st.session_state:
        st.session_state.auth_ok = False

    if not st.session_state.auth_ok:
        st.markdown("""
        <div style='text-align:center; padding:60px 0 20px 0;'>
            <span style='color:#FFD700; font-size:36px; font-weight:bold;'>
                🏆 Siemens-Tippspiel WM 2026 🏆
            </span><br>
            <span style='color:#c8c8e8; font-size:18px;'>
                Bitte mit Passwort anmelden
            </span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pw = st.text_input("🔐 Passwort:", type="password", key="pw_input")
            login = st.button("Einloggen ▶", key="pw_btn")

            if login:
                if pw in USERS:
                    st.session_state.auth_ok = True
                    st.session_state.is_admin = (USERS[pw] == "admin")
                    st.rerun()
                else:
                    st.error("❌ Falsches Passwort! Bitte versuche es erneut.")
        return False
    return True

if not check_password():
    st.stop()

def get_flag(team_name):
    return ""

def save_player_tips(player_name, tips_df, tips_dir=None):
    from scripts.ranking_anzeige import save_player_tips_to_sheet
    save_player_tips_to_sheet(player_name, tips_df)

def player_file_exists(player_name, tips_dir=None):
    from scripts.ranking_anzeige import load_player_tips
    tips = load_player_tips(player_name)
    return not tips.empty

# =========================================================
# SEITEN-KONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Siemens-Tippspiel",
    page_icon="⚽",
    layout="wide"
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>
    .stApp {
        background-color: #0a0a2e;
        color: #FFFFFF;
    }
    [data-testid="stSidebar"] {
        background-color: #1a1a4e;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a4e;
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #c8c8e8;
        font-weight: bold;
        font-size: 15px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFD700 !important;
        color: #0a0a2e !important;
        border-radius: 6px;
    }
    .stButton > button {
        background-color: #FFD700;
        color: #0a0a2e;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
    }
    .stButton > button:hover {
        background-color: #FFC200;
        color: #0a0a2e;
    }
    .wm-card {
        background-color: #1a1a4e;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .wm-title {
        color: #FFD700;
        font-size: 28px;
        font-weight: bold;
        text-align: center;
    }
    .game-display {
        background-color: #1a1a4e;
        border-radius: 12px;
        padding: 25px;
        text-align: center;
        margin: 10px 0;
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background-color: #1a1a4e;
        color: #FFFFFF;
        border: 1px solid #FFD700;
        border-radius: 6px;
    }
    .stDataFrame {
        background-color: #1a1a4e;
    }
    [data-testid="stMetricValue"] {
        color: #FFD700;
        font-size: 28px;
    }
    .stSuccess {
        background-color: #1a3a2a;
    }
    .header-banner {
        background: linear-gradient(135deg, #1a1a4e 0%, #0a0a2e 100%);
        border-bottom: 3px solid #FFD700;
        padding: 15px 25px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="header-banner">
    <span style="color:#FFD700; font-size:32px; font-weight:bold;">
        🏆 &nbsp; Siemens-Tippspiel &nbsp; WM 2026 &nbsp; 🏆
    </span>
    <br>
    <span style="font-size:18px; color:#c8c8e8;">USA &nbsp;|&nbsp; Kanada &nbsp;|&nbsp; Mexiko</span>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================
if "player_name" not in st.session_state:
    st.session_state.player_name = ""
if "player_tips" not in st.session_state:
    st.session_state.player_tips = pd.DataFrame()
if "all_games" not in st.session_state:
    st.session_state.all_games = pd.DataFrame()
if "current_game_index" not in st.session_state:
    st.session_state.current_game_index = 0
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# =========================================================
# TABS
# =========================================================
if st.session_state.is_admin:
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯  Tippabgabe",
        "🏅  Ranking",
        "📊  Ergebnisse",
        "🔧  Admin"
    ])
else:
    tab1, tab2, tab3 = st.tabs([
        "🎯  Tippabgabe",
        "🏅  Ranking",
        "📊  Ergebnisse"
    ])

# =========================================================
# TAB 1: TIPPABGABE
# =========================================================
with tab1:

    st.markdown('<div class="wm-card">', unsafe_allow_html=True)
    st.markdown("### 👤 Anmeldung")

    col_name, col_btn = st.columns([3, 1])
    with col_name:
        name_input = st.text_input(
            "Dein Name (Format: Vorname_Nachname)",
            placeholder="z.B. Max_Mustermann",
            key="name_input"
        )
    with col_btn:
        st.write("")
        st.write("")
        login_clicked = st.button("Einloggen ▶", key="login_btn")

    if name_input:
        if player_file_exists(name_input):
            st.success(f"✅ Willkommen zurück, **{name_input}**! Deine Tipps werden geladen.")
        else:
            st.info(f"🆕 Neuer Spieler: **{name_input}** — ein neues Profil wird erstellt.")

    if login_clicked and name_input.strip():
        st.session_state.player_name = name_input.strip()
        st.session_state.all_games   = load_games()
        is_returning                  = player_file_exists(st.session_state.player_name)
        st.session_state.player_tips  = load_player_tips(st.session_state.player_name)

        if st.session_state.player_tips.empty:
            st.session_state.player_tips = pd.DataFrame(index=st.session_state.all_games.index)
            st.session_state.player_tips[HEIMTEAM_COL    + '_Tipp'] = pd.NA
            st.session_state.player_tips[AUSWAERTSTE_COL + '_Tipp'] = pd.NA
        else:
            for game_id in st.session_state.all_games.index:
                if game_id not in st.session_state.player_tips.index:
                    st.session_state.player_tips.loc[game_id, HEIMTEAM_COL    + '_Tipp'] = pd.NA
                    st.session_state.player_tips.loc[game_id, AUSWAERTSTE_COL + '_Tipp'] = pd.NA

        st.session_state.logged_in           = True
        st.session_state.current_game_index  = 0

        if is_returning:
            st.success(f"👋 Willkommen zurück, **{st.session_state.player_name}**!")
        else:
            st.success(f"🆕 Neues Profil erstellt für **{st.session_state.player_name}**. Viel Erfolg! 🤞")

    elif login_clicked and not name_input.strip():
        st.warning("⚠️ Bitte gib deinen Namen ein!")

    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("📋 Punkte-Regeln anzeigen", expanded=False):
        st.markdown("""
        | Punkte | Bedingung |
        |--------|-----------|
        | 🥇 **4 Punkte** | Exakter Tipp (z.B. Tipp 2:1 → Ergebnis 2:1) |
        | ✅ **1 Punkt**  | Richtiger Spielausgang (Sieg / Unentschieden / Niederlage) |
        | ➕ **2 Punkte** | Richtige Tordifferenz (z.B. Tipp 2:1 → Ergebnis 3:2) |

        💡 **Format:** Vorname_Nachname | Melde dich immer mit dem gleichen Namen an!
        """)

    if st.session_state.logged_in and not st.session_state.all_games.empty:

        games   = st.session_state.all_games
        results = load_results()
        idx     = st.session_state.current_game_index
        game_id = games.index[idx]
        game    = games.loc[game_id]

        heim      = game[HEIMTEAM_COL]
        auswaerts = game[AUSWAERTSTE_COL]

        ergebnis_vorhanden = (
            game_id in results.index
            and pd.notna(results.loc[game_id, HEIM_TORE_COL])
            and pd.notna(results.loc[game_id, AUSWAERTS_TORE_COL])
        )

        if ergebnis_vorhanden:
            h = safe_int(results.loc[game_id, HEIM_TORE_COL])
            a = safe_int(results.loc[game_id, AUSWAERTS_TORE_COL])
            st.markdown(f"""
            <div class="game-display">
                <div style="color:#c8c8e8; font-size:14px;">Spiel {game_id} &nbsp;|&nbsp; 🔒 Gesperrt</div>
                <div style="font-size:36px; margin:10px 0;">
                    <span style="color:#FFFFFF; font-weight:bold;">{heim}</span>
                    &nbsp; <span style="color:#FFD700; font-size:40px;">{h} : {a}</span> &nbsp;
                    <span style="color:#FFFFFF; font-weight:bold;">{auswaerts}</span>
                </div>
                <div style="color:#e63946;">🔒 Dieses Spiel hat bereits ein Ergebnis — Tipp gesperrt!</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="game-display">
                <div style="color:#c8c8e8; font-size:14px;">Spiel {game_id} &nbsp;|&nbsp; Spiel {idx+1} von {len(games)}</div>
                <div style="font-size:32px; margin:10px 0;">
                    <span style="color:#FFFFFF; font-weight:bold;">{heim}</span>
                    &nbsp; <span style="color:#FFD700;">vs.</span> &nbsp;
                    <span style="color:#FFFFFF; font-weight:bold;">{auswaerts}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        current_heim      = st.session_state.player_tips.loc[game_id, HEIMTEAM_COL    + '_Tipp']
        current_auswaerts = st.session_state.player_tips.loc[game_id, AUSWAERTSTE_COL + '_Tipp']

        default_heim      = int(current_heim)      if pd.notna(current_heim) and current_heim != "" else 0
        default_auswaerts = int(current_auswaerts) if pd.notna(current_auswaerts) and current_auswaerts != "" else 0

        if not ergebnis_vorhanden:
            st.markdown("#### 🎯 Dein Tipp:")
            col1, col_vs, col2 = st.columns([2, 1, 2])
            with col1:
                st.markdown(f"<div style='text-align:center; color:#FFD700; font-weight:bold;'>{heim}</div>", unsafe_allow_html=True)
                tipp_heim = st.number_input(
                    "Tore Heimteam", min_value=0, max_value=30,
                    value=default_heim, key=f"tipp_heim_{game_id}",
                    label_visibility="collapsed"
                )
            with col_vs:
                st.markdown("<div style='text-align:center; color:#FFD700; font-size:28px; font-weight:bold; padding-top:5px;'>:</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='text-align:center; color:#FFD700; font-weight:bold;'>{auswaerts}</div>", unsafe_allow_html=True)
                tipp_auswaerts = st.number_input(
                    "Tore Auswärtsteam", min_value=0, max_value=30,
                    value=default_auswaerts, key=f"tipp_aus_{game_id}",
                    label_visibility="collapsed"
                )

            col_save, col_finish = st.columns([1, 1])
            with col_save:
                if st.button("💾 Tipp speichern", key="save_tip"):
                    st.session_state.player_tips.loc[game_id, HEIMTEAM_COL + '_Tipp'] = str(tipp_heim)
                    st.session_state.player_tips.loc[game_id, AUSWAERTSTE_COL + '_Tipp'] = str(tipp_auswaerts)
                    save_player_tips(st.session_state.player_name, st.session_state.player_tips)
                    st.success(f"✅ Tipp gespeichert: **{tipp_heim} : {tipp_auswaerts}**")
            with col_finish:
                if st.button("✅ Alle Tipps speichern & beenden", key="finish_tips"):
                    save_player_tips(st.session_state.player_name, st.session_state.player_tips)
                    st.success("🏆 Alle Tipps gespeichert! Viel Glück! 🤞")
                    st.session_state.logged_in = False
                    st.rerun()
        else:
            st.markdown(f"""
            <div style='text-align:center; padding:10px;'>
                <span style='color:#c8c8e8;'>Dein Tipp war: </span>
                <span style='color:#FFD700; font-size:22px; font-weight:bold;'>
                    {default_heim} : {default_auswaerts}
                </span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("◀ Vorheriges", disabled=(idx == 0), key="prev_btn"):
                st.session_state.current_game_index -= 1
                st.rerun()
        with col_info:
            st.markdown(
                f"<div style='text-align:center; color:#c8c8e8;'>Spiel {idx+1} von {len(games)}</div>",
                unsafe_allow_html=True
            )
        with col_next:
            if st.button("Nächstes ▶", disabled=(idx >= len(games) - 1), key="next_btn"):
                st.session_state.current_game_index += 1
                st.rerun()

    elif not st.session_state.logged_in:
        st.markdown("""
        <div style='text-align:center; color:#c8c8e8; padding:40px;'>
            👆 Gib deinen Namen ein und klicke auf <b style='color:#FFD700;'>Einloggen</b> um zu starten!
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# TAB 2: RANKING
# =========================================================
with tab2:
    st.markdown("### 🏅 Aktuelles Ranking")

    if st.button("🔄 Ranking aktualisieren", key="refresh_ranking"):
        st.rerun()
    
        # ← NEU: DEBUG (temporär!)
    with st.expander("🐛 Debug Info"):
        try:
            ranking_df_debug = get_all_player_rankings()
            st.write("**Ranking DataFrame:**", ranking_df_debug)

            from scripts.ranking_anzeige import load_all_tips_from_sheet, load_games, load_results
            all_games = load_games()
            results   = load_results()
            df        = load_all_tips_from_sheet()

            st.write("**Spiele:**", all_games)
            st.write("**Ergebnisse:**", results)
            st.write("**Alle Tipps:**", df)
        except Exception as e:
            st.error(f"Debug Fehler: {e}")

    try:
        ranking_df = get_all_player_rankings()
        if not ranking_df.empty:
            medals = ["🥇", "🥈", "🥉"]
            display_df = ranking_df.copy()
            display_df['Rang'] = [
                medals[i] if i < 3 else str(row['Rang'])
                for i, (_, row) in enumerate(ranking_df.iterrows())
            ]
            display_df = display_df[['Rang', 'Spieler', 'Punkte']]
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rang":    st.column_config.TextColumn("🏆 Rang",    width="small"),
                    "Spieler": st.column_config.TextColumn("👤 Spieler", width="medium"),
                    "Punkte":  st.column_config.NumberColumn("⭐ Punkte", width="small"),
                }
            )
        else:
            st.info("Noch kein Ranking verfügbar. Bitte warte bis Ergebnisse eingetragen sind.")
    except Exception as e:
        st.error(f"Fehler beim Laden des Rankings: {e}")

# =========================================================
# TAB 3: ERGEBNISSE
# =========================================================
with tab3:
    st.markdown("### 📊 Spielergebnisse Übersicht")

    if st.button("🔄 Aktualisieren", key="refresh_results"):
        st.rerun()

    try:
        games   = load_games()
        results = load_results()
        my_tips = pd.DataFrame()

        if st.session_state.player_name:
            my_tips = load_player_tips(st.session_state.player_name)

        if games.empty:
            st.warning("Keine Spiele gefunden.")
        else:
            rows = []
            for game_id, game in games.iterrows():
                heim      = game[HEIMTEAM_COL]
                auswaerts = game[AUSWAERTSTE_COL]

                if (game_id in results.index
                        and pd.notna(results.loc[game_id, HEIM_TORE_COL])
                        and pd.notna(results.loc[game_id, AUSWAERTS_TORE_COL])):
                    h = safe_int(results.loc[game_id, HEIM_TORE_COL])
                    a = safe_int(results.loc[game_id, AUSWAERTS_TORE_COL])
                    ergebnis = f"{h} : {a}"
                else:
                    ergebnis = "- : -"

                mein_tipp = "- : -"
                if not my_tips.empty and game_id in my_tips.index:
                    t_h = my_tips.loc[game_id, HEIMTEAM_COL    + '_Tipp']
                    t_a = my_tips.loc[game_id, AUSWAERTSTE_COL + '_Tipp']
                    if pd.notna(t_h) and pd.notna(t_a):
                        mein_tipp = f"{safe_int(t_h)} : {safe_int(t_a)}"

                rows.append({
                    "#":               game_id,
                    "🏠 Heimteam":     f"{heim}",
                    "🎯 Mein Tipp":    mein_tipp,
                    "📋 Ergebnis":     ergebnis,
                    "✈️ Auswärtsteam": f"{auswaerts}",
                })

            df_display = pd.DataFrame(rows)
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Fehler: {e}")

# =========================================================
# TAB 4: ADMIN
# =========================================================
if st.session_state.is_admin:
    with tab4:
        st.markdown("### 🔧 Admin: Spielergebnisse eingeben")

        try:
            games   = load_games()
            results = load_results()

            if games.empty:
                st.warning("Keine Spiele vorhanden.")
            else:
                st.markdown("Trage hier die offiziellen Spielergebnisse ein:")

                admin_inputs = {}

                for game_id, game in games.iterrows():
                    heim      = game[HEIMTEAM_COL]
                    auswaerts = game[AUSWAERTSTE_COL]

                    existing_heim      = 0
                    existing_auswaerts = 0
                    if game_id in results.index:
                        if pd.notna(results.loc[game_id, HEIM_TORE_COL]):
                            existing_heim = safe_int(results.loc[game_id, HEIM_TORE_COL])
                        if pd.notna(results.loc[game_id, AUSWAERTS_TORE_COL]):
                            existing_auswaerts = safe_int(results.loc[game_id, AUSWAERTS_TORE_COL])

                    with st.container():
                        col_label, col_h, col_vs, col_a = st.columns([4, 1, 0.3, 1])
                        with col_label:
                            st.markdown(f"**Spiel {game_id}:** {heim} vs. {auswaerts}")
                        with col_h:
                            h_val = st.number_input(
                                f"Heim {game_id}", min_value=0, max_value=30,
                                value=existing_heim,
                                key=f"admin_heim_{game_id}",
                                label_visibility="collapsed"
                            )
                        with col_vs:
                            st.markdown("<div style='text-align:center; color:#FFD700; font-weight:bold;'>:</div>", unsafe_allow_html=True)
                        with col_a:
                            a_val = st.number_input(
                                f"Auswaerts {game_id}", min_value=0, max_value=30,
                                value=existing_auswaerts,
                                key=f"admin_aus_{game_id}",
                                label_visibility="collapsed"
                            )
                        admin_inputs[game_id] = (h_val, a_val)

                st.markdown("---")
                if st.button("💾 Alle Ergebnisse speichern", key="save_admin"):
                    errors = []
                    for game_id, (h, a) in admin_inputs.items():
                        try:
                            save_result(game_id, h, a)
                        except Exception as e:
                            errors.append(f"Spiel {game_id}: {e}")

                    if errors:
                        for err in errors:
                            st.error(err)
                    else:
                        st.success("✅ Alle Ergebnisse erfolgreich gespeichert!")
                        st.rerun()

        except Exception as e:
            st.error(f"Fehler im Admin-Tab: {e}")