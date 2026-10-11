import html
import threading
from datetime import date, timedelta

import mysql.connector
import pandas as pd
import streamlit as st
from mysql.connector import Error

st.set_page_config(page_title="ArenaX", layout="wide")


def load_db_config():
    """Connection details come from the secrets file or the hosting dashboard, never from this file."""
    try:
        d = st.secrets["db"]
        return dict(host=d["host"], port=int(d.get("port", 3306)), user=d["user"],
                    password=d["password"], database=d.get("database", "arenax"),
                    use_pure=True)
    except Exception:
        return None


DB = load_db_config()

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Sora:wght@500;600;700&display=swap');

:root {
  --bg: #0f1420;
  --panel: #161d2d;
  --panel-2: #1c2538;
  --line: #27324a;
  --text: #e7ebf3;
  --muted: #8d99b0;
  --accent: #4d8dff;
  --gold: #e2b44f;
  --ok: #3ecf8e;
  --bad: #ef6a6a;
}

.stApp { background: var(--bg); color: var(--text); font-family: 'DM Sans', system-ui, -apple-system, 'Segoe UI', sans-serif; }
.stApp p, .stApp li, .stApp label, .stApp span { font-family: 'DM Sans', system-ui, -apple-system, 'Segoe UI', sans-serif; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, .stAppDeployButton { visibility: hidden; }
.block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem; }

/* brand */
.brand { font-family: 'Sora', system-ui, sans-serif; font-weight: 700; font-size: 1.7rem; letter-spacing: -0.02em; color: var(--text); line-height: 1.1; }
.brand-sub { color: var(--muted); font-size: 0.9rem; margin-top: 0.25rem; }

/* tournament header */
.hero { margin: 1.6rem 0 1.1rem 0; padding-left: 1rem; border-left: 3px solid var(--accent); }
.hero-top { display: flex; align-items: center; gap: 0.9rem; flex-wrap: wrap; }
.hero-name { font-family: 'Sora', system-ui, sans-serif; font-weight: 600; font-size: 1.9rem; letter-spacing: -0.015em; line-height: 1.15; }
.hero-sub { color: var(--muted); margin-top: 0.35rem; font-size: 0.95rem; }

.badge { display: inline-block; padding: 0.18rem 0.65rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600; border: 1px solid transparent; }
.badge.s-upcoming { color: #8db4ff; background: rgba(77,141,255,0.12); border-color: rgba(77,141,255,0.35); }
.badge.s-ongoing { color: var(--ok); background: rgba(62,207,142,0.12); border-color: rgba(62,207,142,0.35); }
.badge.s-closed { color: var(--muted); background: rgba(141,153,176,0.12); border-color: rgba(141,153,176,0.3); }

.stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.9rem; margin: 0 0 1.6rem 0; }
.stat { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 0.95rem 1.15rem; }
.stat .k { color: var(--muted); font-size: 0.85rem; }
.stat .v { font-family: 'Sora', system-ui, sans-serif; font-weight: 600; font-size: 1.55rem; margin-top: 0.15rem; letter-spacing: -0.01em; }
.stat .n { color: var(--muted); font-size: 0.82rem; margin-top: 0.1rem; }

/* section headings */
.sec { margin: 0 0 0.9rem 0; }
.sec .t { font-family: 'Sora', system-ui, sans-serif; font-weight: 600; font-size: 1.08rem; letter-spacing: -0.005em; }
.sec .d { color: var(--muted); font-size: 0.9rem; margin-top: 0.2rem; line-height: 1.45; }
.gap { height: 1.4rem; }

/* tables */
div.tbl-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 12px; background: var(--panel); }
div.tbl-wrap table.t { width: 100%; border-collapse: collapse; font-size: 0.92rem; margin: 0; }
div.tbl-wrap table.t th { text-align: left; font-weight: 500; font-size: 0.82rem; color: var(--muted) !important; padding: 0.75rem 1rem; border: none !important; border-bottom: 1px solid var(--line) !important; background: transparent !important; }
div.tbl-wrap table.t td { padding: 0.72rem 1rem; border: none !important; border-bottom: 1px solid rgba(39,50,74,0.65) !important; background: transparent !important; color: var(--text); }
div.tbl-wrap table.t tbody tr:last-child td { border-bottom: none !important; }
div.tbl-wrap table.t tbody tr:hover td { background: rgba(77,141,255,0.06) !important; }
div.tbl-wrap table.t .n { text-align: right; font-variant-numeric: tabular-nums; }
div.tbl-wrap table.t td.p1 { color: var(--gold); font-weight: 700; }

.empty { border: 1px dashed var(--line); border-radius: 12px; padding: 1.4rem 1.2rem; color: var(--muted); text-align: center; font-size: 0.95rem; }

/* section navigation */
[data-testid="stRadio"] [role="radiogroup"] { gap: 0.25rem; border-bottom: 1px solid var(--line); flex-wrap: wrap; }
[data-testid="stRadio"] label { margin: 0; padding: 0.7rem 1rem; cursor: pointer; border-bottom: 2px solid transparent; color: var(--muted); }
[data-testid="stRadio"] label > *:not(input):not(:has([data-testid="stMarkdownContainer"])) { display: none; }
[data-testid="stRadio"] label p { color: inherit; font-weight: 500; font-size: 1rem; }
[data-testid="stRadio"] label:hover { color: var(--text); }
[data-testid="stRadio"] label:has(input:checked) { color: var(--text); border-bottom-color: var(--accent); }
[data-testid="stRadio"] label:has(input:focus-visible) { outline: 2px solid var(--accent); outline-offset: -2px; }

/* inputs */
[data-testid="stWidgetLabel"] p { color: var(--muted); font-size: 0.86rem; font-weight: 500; }
[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input, .stDateInput input {
  background: var(--panel-2) !important; border-color: var(--line) !important; border-radius: 8px !important; color: var(--text) !important;
}
.stNumberInput [data-baseweb="input"], .stTextInput [data-baseweb="input"], .stDateInput [data-baseweb="input"] { border-radius: 8px; background: var(--panel-2) !important; }

/* buttons */
.stButton > button, .stFormSubmitButton > button {
  border-radius: 8px; font-weight: 600; padding: 0.5rem 1.15rem; transition: background 0.12s, border-color 0.12s;
}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  background: var(--accent); border: 1px solid var(--accent); color: #fff;
}
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover { background: #6aa0ff; border-color: #6aa0ff; color: #fff; }
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"] {
  background: transparent; border: 1px solid var(--line); color: var(--text);
}
[data-testid="stBaseButton-secondary"]:hover { border-color: var(--accent); color: var(--text); background: rgba(77,141,255,0.08); }
.stButton > button:disabled { opacity: 0.4; cursor: not-allowed; }
.stButton > button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

[class*="st-key-danger"] [data-testid="stBaseButton-secondary"] { border-color: rgba(239,106,106,0.55); color: var(--bad); }
[class*="st-key-danger"] [data-testid="stBaseButton-secondary"]:hover:not(:disabled) { background: var(--bad); border-color: var(--bad); color: #fff; }
[class*="st-key-danger"] [data-testid="stBaseButton-secondary"]:disabled { border-color: var(--line); color: var(--muted); }

/* bordered containers and alerts */
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 12px; border-color: var(--line); }
[data-testid="stAlert"] { border-radius: 10px; }

@media (max-width: 760px) {
  .stats { grid-template-columns: 1fr; }
  .hero-name { font-size: 1.5rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

if DB is None:
    st.error("This app is not set up yet. The owner needs to finish the setup.")
    st.stop()


# ---------------------------------------------------------------- database

GENERIC_ERROR = "Something went wrong. Please try again."


def friendly(e):
    """Only messages written for people are shown. Anything else becomes a generic line."""
    if getattr(e, "sqlstate", None) == "45000" and getattr(e, "msg", None):
        return e.msg
    return GENERIC_ERROR


@st.cache_resource(show_spinner=False)
def _holder():
    """One shared connection and lock for the whole app, kept between clicks."""
    return {"conn": None, "lock": threading.Lock()}


def _conn():
    """Return the shared connection, reconnecting only if it has dropped."""
    h = _holder()
    c = h["conn"]
    if c is not None:
        try:
            c.ping(reconnect=True, attempts=2, delay=0)
            return c
        except Exception:
            pass
    c = mysql.connector.connect(connection_timeout=10, **DB)
    h["conn"] = c
    return c


def _drop():
    """Throw the shared connection away so the next call opens a fresh one."""
    h = _holder()
    try:
        if h["conn"] is not None:
            h["conn"].close()
    except Exception:
        pass
    h["conn"] = None


def _rollback(conn):
    try:
        if conn is not None:
            conn.rollback()
    except Exception:
        _drop()


def query(sql, params=()):
    """Run a SELECT and return a DataFrame (with its columns even when empty)."""
    failed = False
    rows, cols = [], []
    with _holder()["lock"]:
        conn = None
        try:
            conn = _conn()
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute(sql, params)
                rows = cur.fetchall()
                cols = cur.column_names
            finally:
                cur.close()
            conn.commit()  # ends the read snapshot so later reads see fresh data
        except Error:
            failed = True
            _drop()
    if failed:
        st.error("We couldn't load this page. Please refresh and try again.")
        st.stop()
    return pd.DataFrame(rows, columns=cols)


def call(proc, args):
    """Run an action. Returns (result tables, message to show if it failed)."""
    with _holder()["lock"]:
        conn = None
        try:
            conn = _conn()
            cur = conn.cursor(dictionary=True)
            try:
                cur.callproc(proc, args)
                tables = [pd.DataFrame(r.fetchall(), columns=r.column_names)
                          for r in cur.stored_results()]
            finally:
                cur.close()
            conn.commit()
            return tables, None
        except Error as e:
            _rollback(conn)
            return [], friendly(e)


def execute(sql, params=()):
    """Add a row. Returns (new id, message to show if it failed)."""
    with _holder()["lock"]:
        conn = None
        try:
            conn = _conn()
            cur = conn.cursor()
            try:
                cur.execute(sql, params)
                new_id = cur.lastrowid
            finally:
                cur.close()
            conn.commit()
            return new_id, None
        except Error as e:
            _rollback(conn)
            return None, friendly(e)


@st.cache_data(ttl=60, show_spinner=False)
def ref(sql):
    """Lists that rarely change (tournaments, teams, games) are remembered for 60 seconds."""
    return query(sql)


# ---------------------------------------------------------------- ui helpers

STATUS = {
    "UPCOMING": ("Upcoming", "s-upcoming"),
    "ONGOING": ("In progress", "s-ongoing"),
    "CLOSED": ("Closed", "s-closed"),
}


def esc(x):
    return html.escape(str(x))


def section(title, note=None):
    d = f'<div class="d">{esc(note)}</div>' if note else ""
    st.markdown(f'<div class="sec"><div class="t">{esc(title)}</div>{d}</div>',
                unsafe_allow_html=True)


def spacer():
    st.markdown('<div class="gap"></div>', unsafe_allow_html=True)


def empty(msg):
    st.markdown(f'<div class="empty">{esc(msg)}</div>', unsafe_allow_html=True)


def table(df, num=(), gold="Pos"):
    """Draw a DataFrame as a styled table. Columns in `num` are right aligned."""
    if df is None or df.empty:
        return
    cols = list(df.columns)
    head = "".join(
        f'<th class="n">{esc(c)}</th>' if c in num else f"<th>{esc(c)}</th>"
        for c in cols)
    body = []
    for rec in df.itertuples(index=False):
        cells = []
        for c, v in zip(cols, rec):
            blank = v is None or (not isinstance(v, str) and pd.isna(v))
            txt = "-" if blank else str(v)
            cls = []
            if c in num:
                cls.append("n")
            if c == gold and txt == "1":
                cls.append("p1")
            cs = " ".join(cls)
            cells.append(f'<td class="{cs}">{esc(txt)}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    st.markdown(
        f'<div class="tbl-wrap"><table class="t"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>',
        unsafe_allow_html=True)


def danger_box(name):
    """A container the stylesheet can find so destructive buttons turn red."""
    try:
        return st.container(border=True, key=name)
    except TypeError:  # older Streamlit without container keys
        return st.container(border=True)


def fmt_date(d):
    return d.strftime("%d %b %Y")


def go(kind, msg):
    """Show a message after the page reloads, then reload so all data is fresh."""
    st.cache_data.clear()
    st.session_state["flash"] = (kind, msg)
    st.rerun()


# ---------------------------------------------------------------- shared data

tournaments = ref(
    "SELECT tournament_id, tournament_name FROM Tournaments ORDER BY tournament_id")
teams = ref("SELECT team_id, team_name FROM Teams ORDER BY team_name")
games = ref("SELECT game_id, game_name FROM Games ORDER BY game_name")

T = dict(zip(tournaments.tournament_id.tolist(), tournaments.tournament_name))
C = dict(zip(teams.team_id.tolist(), teams.team_name))
G = dict(zip(games.game_id.tolist(), games.game_name))

# a tournament that was just created gets selected on the next load
if "select_next" in st.session_state:
    st.session_state["tid"] = st.session_state.pop("select_next")
if st.session_state.get("tid") not in T:
    st.session_state.pop("tid", None)

# ---------------------------------------------------------------- header

try:
    head_l, head_r = st.columns([3, 2], vertical_alignment="bottom")
except TypeError:  # older Streamlit
    head_l, head_r = st.columns([3, 2])
with head_l:
    st.markdown('<div class="brand">ArenaX</div>'
                '<div class="brand-sub">Esports tournament manager</div>',
                unsafe_allow_html=True)
with head_r:
    if T:
        tid = st.selectbox("Tournament", list(T), format_func=T.get, key="tid")
    else:
        tid = None

if "flash" in st.session_state:
    kind, msg = st.session_state.pop("flash")
    getattr(st, kind)(msg)

info = None
registered = pd.DataFrame(columns=["team_id", "team_name", "country", "registered_on"])
status = None

if tid is not None:
    info = query(
        "SELECT t.tournament_name, g.game_name, t.start_date, t.end_date, t.status, "
        "t.max_teams, t.prize_pool, "
        "(SELECT COUNT(*) FROM Registrations WHERE tournament_id = %s) AS registered, "
        "(SELECT COUNT(*) FROM Matches WHERE tournament_id = %s) AS matches, "
        "pkg_registration_is_full(%s) AS is_full "
        "FROM Tournaments t JOIN Games g ON g.game_id = t.game_id "
        "WHERE t.tournament_id = %s", (tid, tid, tid, tid)).iloc[0]
    status = info["status"]
    registered = query(
        "SELECT t.team_id, t.team_name, t.country, r.registered_on "
        "FROM Registrations r JOIN Teams t ON t.team_id = r.team_id "
        "WHERE r.tournament_id = %s ORDER BY t.team_name", (tid,))

    label, cls = STATUS[status]
    st.markdown(
        f'<div class="hero"><div class="hero-top">'
        f'<div class="hero-name">{esc(info["tournament_name"])}</div>'
        f'<span class="badge {cls}">{label}</span></div>'
        f'<div class="hero-sub">{esc(info["game_name"])}, '
        f'{fmt_date(info["start_date"])} to {fmt_date(info["end_date"])}</div></div>',
        unsafe_allow_html=True)

    spots = int(info["max_teams"]) - int(info["registered"])
    if info["is_full"]:
        spots_note = "Tournament is full"
    else:
        spots_note = f"{spots} spot{'s' if spots != 1 else ''} left"
    st.markdown(
        f'<div class="stats">'
        f'<div class="stat"><div class="k">Teams</div>'
        f'<div class="v">{int(info["registered"])} / {int(info["max_teams"])}</div>'
        f'<div class="n">{spots_note}</div></div>'
        f'<div class="stat"><div class="k">Prize pool</div>'
        f'<div class="v">{float(info["prize_pool"]):,.0f}</div>'
        f'<div class="n">Top three teams are paid</div></div>'
        f'<div class="stat"><div class="k">Matches played</div>'
        f'<div class="v">{int(info["matches"])}</div>'
        f'<div class="n">Win is worth 3 points</div></div>'
        f'</div>',
        unsafe_allow_html=True)
else:
    spacer()

PAGES = ["Leaderboard", "Teams", "Matches", "Prizes", "Manage", "Activity"]
page = st.radio("Section", PAGES, horizontal=True, key="page", label_visibility="collapsed")
spacer()

# ---------------------------------------------------------------- leaderboard

if page == "Leaderboard":
    if tid is None:
        empty("There are no tournaments yet. Create one in the Manage tab.")
    else:
        section("Standings", "Teams are ranked by points, then by wins.")
        tables, err = call("pkg_reports_leaderboard", (tid,))
        if err:
            st.error(err)
        elif tables and not tables[0].empty:
            lb = tables[0].copy()
            lb["win_rate_pct"] = lb["win_rate_pct"].map(lambda x: f"{float(x):.1f}%")
            lb.columns = ["Pos", "Team", "Played", "Won", "Lost", "Points", "Win rate"]
            table(lb, num=("Pos", "Played", "Won", "Lost", "Points", "Win rate"))
        else:
            empty("No teams are registered yet. Add some in the Teams tab.")

    spacer()
    section("Overall win rate", "Across every completed match in every tournament.")
    wr = query("SELECT team_name, pkg_reports_win_rate(team_id) AS win_rate_pct "
               "FROM Teams ORDER BY win_rate_pct DESC, team_name")
    if wr.empty:
        empty("No teams yet.")
    else:
        wr["win_rate_pct"] = wr["win_rate_pct"].map(lambda x: f"{float(x):.1f}%")
        wr.columns = ["Team", "Win rate"]
        table(wr, num=("Win rate",))

# ---------------------------------------------------------------- teams

if page == "Teams":
    if tid is None:
        empty("There are no tournaments yet. Create one in the Manage tab.")
    else:
        reg_ids = registered.team_id.tolist()
        can_change = status == "UPCOMING"
        left, right = st.columns(2, gap="large")

        with left:
            with st.container(border=True):
                section("Register a team", "Add a team before the first match is played.")
                avail = [i for i in C if i not in reg_ids]
                if not can_change:
                    st.info("Registration closed when the first match was played.")
                elif info["is_full"]:
                    st.info("This tournament is full.")
                elif not avail:
                    st.info("Every team is already registered.")
                else:
                    team = st.selectbox("Team", avail, format_func=C.get,
                                        key=f"reg_team_{tid}")
                    if st.button("Register team", type="primary", key="reg_btn"):
                        _, err = call("pkg_registration_register_team", (tid, team))
                        if err:
                            st.error(err)
                        else:
                            go("success", f"{C[team]} registered for {T[tid]}.")

        with right:
            with st.container(border=True):
                section("Withdraw a team", "Take a team out before the tournament starts.")
                if not can_change:
                    st.info("Teams cannot withdraw once the tournament has started.")
                elif not reg_ids:
                    st.info("No teams are registered yet.")
                else:
                    out = st.selectbox("Team", reg_ids, format_func=C.get,
                                       key=f"wd_team_{tid}")
                    if st.button("Withdraw team", key="wd_btn"):
                        _, err = call("pkg_registration_withdraw_team", (tid, out))
                        if err:
                            st.error(err)
                        else:
                            go("success", f"{C[out]} withdrawn from {T[tid]}.")

        spacer()
        section("Registered teams")
        if registered.empty:
            empty("No teams are registered yet.")
        else:
            rt = registered[["team_name", "country", "registered_on"]].copy()
            rt["registered_on"] = pd.to_datetime(rt["registered_on"]).dt.strftime("%d %b %Y, %H:%M")
            rt.columns = ["Team", "Country", "Registered"]
            table(rt)

# ---------------------------------------------------------------- matches

if page == "Matches":
    if tid is None:
        empty("There are no tournaments yet. Create one in the Manage tab.")
    else:
        reg_ids = registered.team_id.tolist()
        left, right = st.columns(2, gap="large")

        with left:
            with st.container(border=True):
                section("Record a result", "Scores decide the winner. Draws are not allowed.")
                if status == "CLOSED":
                    st.info("This tournament is closed.")
                elif len(reg_ids) < 2:
                    st.info("Register at least two teams first.")
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        t1 = st.selectbox("Team 1", reg_ids, format_func=C.get,
                                          key=f"m_t1_{tid}")
                        s1 = st.number_input("Team 1 score", min_value=0, step=1,
                                             key=f"m_s1_{tid}")
                    with c2:
                        t2 = st.selectbox("Team 2", reg_ids, index=1, format_func=C.get,
                                          key=f"m_t2_{tid}")
                        s2 = st.number_input("Team 2 score", min_value=0, step=1,
                                             key=f"m_s2_{tid}")
                    if st.button("Save result", type="primary", key="save_btn"):
                        _, err = call("pkg_matches_record_result",
                                      (tid, t1, t2, int(s1), int(s2)))
                        if err:
                            st.error(err)
                        else:
                            go("success", "Result saved and standings updated.")

        with right:
            with st.container(border=True):
                section("Simulate round robin",
                        "Plays every pairing once with random scores. The winner gets 13. "
                        "Only works before the first match.")
                n = len(reg_ids)
                pairs = n * (n - 1) // 2
                if status != "UPCOMING":
                    st.info("This tournament has already started.")
                elif n < 2:
                    st.info("Register at least two teams first.")
                else:
                    st.caption(f"{n} teams will play {pairs} match{'es' if pairs != 1 else ''}.")
                    if st.button("Simulate round robin", type="primary", key="sim_btn"):
                        with st.spinner("Playing matches"):
                            _, err = call("pkg_matches_simulate_round_robin", (tid,))
                        if err:
                            st.error(err)
                        else:
                            go("success", f"Round robin played: {pairs} matches recorded.")

        spacer()
        section("Results")
        res = query(
            "SELECT m.match_date, t1.team_name AS team1, m.team1_score, m.team2_score, "
            "t2.team_name AS team2, w.team_name AS winner "
            "FROM Matches m "
            "JOIN Teams t1 ON t1.team_id = m.team1_id "
            "JOIN Teams t2 ON t2.team_id = m.team2_id "
            "LEFT JOIN Teams w ON w.team_id = m.winner_id "
            "WHERE m.tournament_id = %s ORDER BY m.match_id DESC", (tid,))
        if res.empty:
            empty("No matches have been played yet.")
        else:
            res["score"] = res["team1_score"].astype(int).astype(str) + " - " + res["team2_score"].astype(int).astype(str)
            res["played"] = pd.to_datetime(res["match_date"]).dt.strftime("%d %b %Y, %H:%M")
            res = res[["played", "team1", "score", "team2", "winner"]]
            res.columns = ["Played", "Team 1", "Score", "Team 2", "Winner"]
            table(res, num=("Score",))

# ---------------------------------------------------------------- prizes

if page == "Prizes":
    if tid is None:
        empty("There are no tournaments yet. Create one in the Manage tab.")
    else:
        left, right = st.columns(2, gap="large")
        with left:
            section("Prize split", "How the prize pool is shared between the top three teams.")
            split = query(
                "SELECT 1 AS place, pkg_prizes_share(%s, 1) AS prize "
                "UNION ALL SELECT 2, pkg_prizes_share(%s, 2) "
                "UNION ALL SELECT 3, pkg_prizes_share(%s, 3)", (tid, tid, tid))
            split["place"] = split["place"].map({1: "1st", 2: "2nd", 3: "3rd"})
            split["prize"] = split["prize"].map(lambda x: f"{float(x):,.2f}")
            split.columns = ["Place", "Prize"]
            table(split, num=("Prize",))

        with right:
            with st.container(border=True):
                section("Close tournament",
                        "Ranks every team, pays the top three and locks the results.")
                if status == "UPCOMING":
                    st.info("No matches have been played yet, so there is nothing to close.")
                elif status == "CLOSED":
                    st.info("This tournament is closed and its prizes are paid.")
                else:
                    if st.button("Close tournament and pay prizes", type="primary",
                                 key="close_btn"):
                        _, err = call("pkg_prizes_close_tournament", (tid,))
                        if err:
                            st.error(err)
                        else:
                            go("success", "Tournament closed and prizes paid out.")

        payouts = query(
            "SELECT p.final_rank, t.team_name, p.amount "
            "FROM Prize_Payouts p JOIN Teams t ON t.team_id = p.team_id "
            "WHERE p.tournament_id = %s ORDER BY p.final_rank", (tid,))
        if not payouts.empty:
            spacer()
            section("Prizes paid")
            payouts["final_rank"] = payouts["final_rank"].map(
                lambda r: {1: "1st", 2: "2nd", 3: "3rd"}.get(int(r), str(r)))
            payouts["amount"] = payouts["amount"].map(lambda x: f"{float(x):,.2f}")
            payouts.columns = ["Place", "Team", "Amount"]
            table(payouts, num=("Amount",))

# ---------------------------------------------------------------- manage

if page == "Manage":
    nonce = st.session_state.get("nonce", 0)

    with st.container(border=True):
        section("New tournament", "Creates an upcoming tournament that teams can register for.")
        name = st.text_input("Name", max_chars=80, key=f"nt_name_{nonce}")
        c1, c2 = st.columns(2)
        with c1:
            game = st.selectbox("Game", list(G), format_func=G.get, key="nt_game")
            start = st.date_input("Start date", value=date.today() + timedelta(days=14),
                                  key="nt_start")
            prize = st.number_input("Prize pool", min_value=0.0, max_value=99999999.0,
                                    value=10000.0, step=1000.0, key="nt_prize")
        with c2:
            max_teams = st.number_input("Max teams", min_value=2, max_value=64,
                                        value=8, step=1, key="nt_max")
            end = st.date_input("End date", value=date.today() + timedelta(days=20),
                                key="nt_end")
        if st.button("Create tournament", type="primary", key="nt_btn"):
            if not name.strip():
                st.error("Give the tournament a name.")
            elif not G:
                st.error("No games are set up yet, so a tournament cannot be created.")
            elif end < start:
                st.error("The end date cannot be before the start date.")
            else:
                new_id, err = execute(
                    "INSERT INTO Tournaments "
                    "(tournament_name, game_id, start_date, end_date, max_teams, prize_pool) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (name.strip(), int(game), start, end, int(max_teams), float(prize)))
                if err:
                    st.error(err)
                else:
                    st.session_state["select_next"] = new_id
                    st.session_state["nonce"] = nonce + 1
                    go("success", f"Created {name.strip()}.")

    spacer()

    with st.container(border=True):
        section("New team", "Adds a team you can then register into any tournament.")
        c1, c2 = st.columns(2)
        with c1:
            team_name = st.text_input("Team name", max_chars=60, key=f"nteam_name_{nonce}")
        with c2:
            team_country = st.text_input("Country", max_chars=40, key=f"nteam_country_{nonce}")
        if st.button("Add team", type="primary", key="nteam_btn"):
            clean_name = " ".join(team_name.split())
            clean_country = " ".join(team_country.split())
            if not clean_name:
                st.error("Give the team a name.")
            elif not clean_country:
                st.error("Enter the team's country.")
            elif clean_name.lower() in {n.lower() for n in C.values()}:
                st.error("A team with that name already exists.")
            else:
                _, err = execute("INSERT INTO Teams (team_name, country) VALUES (%s, %s)",
                                 (clean_name, clean_country))
                if err:
                    st.error(err)
                else:
                    st.session_state["nonce"] = nonce + 1
                    go("success", f"Added {clean_name}.")

    spacer()

    with danger_box("danger_one"):
        section("Delete this tournament",
                "Removes the tournament together with its teams, matches, "
                "standings and prizes. This cannot be undone.")
        if tid is None:
            st.info("There is no tournament to delete.")
        else:
            sure = st.checkbox(f"Delete {T[tid]} permanently", key=f"sure_{tid}_{nonce}")
            if st.button("Delete tournament", disabled=not sure, key="del_one"):
                _, err = call("pkg_tournaments_delete", (tid,))
                if err:
                    st.error(err)
                else:
                    st.session_state["nonce"] = nonce + 1
                    go("success", f"Deleted {T[tid]}.")

    spacer()

    with danger_box("danger_all"):
        section("Delete all tournaments",
                "Removes every tournament and everything in them. Your teams and games are kept. "
                "This cannot be undone.")
        if not T:
            st.info("There are no tournaments to delete.")
        else:
            typed = st.text_input(f"Type DELETE to remove all {len(T)} tournaments",
                                  key=f"typed_{nonce}")
            if st.button("Delete all tournaments", disabled=typed.strip() != "DELETE",
                         key="del_all"):
                _, err = call("pkg_tournaments_delete_all", ())
                if err:
                    st.error(err)
                else:
                    st.session_state["nonce"] = nonce + 1
                    go("success", "All tournaments deleted.")

# ---------------------------------------------------------------- activity

def describe(v):
    """Turn a stored record such as 'w=1,l=0,pts=3' into plain words."""
    try:
        parts = dict(p.split("=") for p in str(v).split(","))
        return f"{parts['w']} won, {parts['l']} lost, {parts['pts']} points"
    except Exception:
        return "-"


if page == "Activity":
    section("Activity", "Manual changes made to team results. The latest 50 are shown.")
    log = query(
        "SELECT a.changed_at, t.team_name, tn.tournament_name, a.old_value, a.new_value "
        "FROM Audit_Log a "
        "LEFT JOIN Standings s ON s.standing_id = a.record_id "
        "LEFT JOIN Teams t ON t.team_id = s.team_id "
        "LEFT JOIN Tournaments tn ON tn.tournament_id = s.tournament_id "
        "ORDER BY a.log_id DESC LIMIT 50")
    if log.empty:
        empty("No changes have been made yet.")
    else:
        log["changed_at"] = pd.to_datetime(log["changed_at"]).dt.strftime("%d %b %Y, %H:%M")
        log["team_name"] = log["team_name"].fillna("Removed team")
        log["tournament_name"] = log["tournament_name"].fillna("Removed tournament")
        log["old_value"] = log["old_value"].map(describe)
        log["new_value"] = log["new_value"].map(describe)
        log.columns = ["When", "Team", "Tournament", "Before", "After"]
        table(log)
