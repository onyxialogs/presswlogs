import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path


# Get list of all report.json files in /reports subfolders
st.set_page_config(layout="wide")
st.title("📊 Raid Performance Dashboard")

all_players = []
# List all /reports/**/report.json files
report_paths = sorted(Path("reports").rglob("report.json"), reverse=True)  # Newest first
# Create clean report names (remove "reports/" prefix)
clean_report_names = [str(path.parent.name) for path in report_paths]

# Create mapping from clean names back to full paths
name_to_path = {str(path.parent.name): str(path) for path in report_paths}

# Report selection options
st.markdown("### 📂 Report Selection")

# Selection mode in a row at the top
selection_mode = st.radio(
    "Selection mode:",
    ["All Reports", "Single Report", "Multiple Reports"],
    horizontal=True,  # Display options in a row
    index=1  # Default to single report
)

# Report selection below
if selection_mode == "Single Report":
    selected_report = st.selectbox("Select a report:", clean_report_names, index=0)
    selected_reports = [selected_report]
elif selection_mode == "Multiple Reports":
    selected_reports = st.multiselect(
        "Select multiple reports:", 
        clean_report_names,
        default=clean_report_names[:3]  # Default to 3 newest reports
    )
    if not selected_reports:
        st.warning("Please select at least one report.")
        st.stop()
else:  # All Reports
    selected_reports = clean_report_names

# Iterate and combine data from selected reports only
for path in report_paths:
    report_name = str(path.parent.name)
    if report_name in selected_reports:  # Only load selected reports
        try:
            with open(path, "r", encoding="utf-8") as f:
                report = json.load(f)
            players = report.get("players", [])
            for player in players:
                if player["name"] != "Total":
                    player["report_name"] = report_name
                    all_players.append(player)
        except Exception as e:
            st.warning(f"Could not load {path}: {e}")

df_all = pd.DataFrame(all_players)

# Load data based on selection
if selection_mode == "Single Report":
    # Load single report without aggregation
    if df_all.empty:
        st.error("No valid report data found.")
        st.stop()
    df = df_all.copy()
else:
    # Multiple reports or all reports - aggregate data
    if df_all.empty:
        st.error("No valid report data found.")
        st.stop()
    
    # Aggregate numeric columns by player name
    numeric_columns = df_all.select_dtypes(include=[np.number]).columns.tolist()
    
    # Group by player name and sum numeric values
    df_aggregated = df_all.groupby('name').agg({
        **{col: 'sum' for col in numeric_columns},
        'report_name': lambda x: ', '.join(sorted(set(x)))  # Combine report names
    }).reset_index()
    
    # Keep any non-numeric columns from the first occurrence
    non_numeric_cols = [col for col in df_all.columns if col not in numeric_columns + ['name', 'report_name']]
    if non_numeric_cols:
        first_occurrence = df_all.groupby('name')[non_numeric_cols].first().reset_index()
        df = df_aggregated.merge(first_occurrence, on='name', how='left')
    else:
        df = df_aggregated



def top_table(title, column, n=20, column_display_name="used"):
    st.markdown(f"**{title}**")
    sorted_df = (
        df[["name", column]]
        .query(f"{column} > 0")  # Filter out zero values
        .sort_values(by=column, ascending=False)
        .head(n)
    )
    # Rename column if display name provided
    if column_display_name:
        sorted_df = sorted_df.rename(columns={column: column_display_name})
    
    st.dataframe(sorted_df, use_container_width=True, hide_index=True)

def bar_chart(title, column, n=10):
    st.subheader(title)
    chart_data = (
        df[["name", column]]
        .query(f"{column} > 0")  # Filter out zero values
        .sort_values(by=column, ascending=False)
        .head(n)
    )
    
    # Add invisible ranking characters (spaces) to maintain order
    chart_data['ranked_name'] = [f"{' ' * (n-i)}{name}" for i, name in enumerate(chart_data['name'])]
    chart_data = chart_data.set_index('ranked_name')[column]
    
    st.bar_chart(chart_data)

# === DPS / HPS Bar Charts ===
col1, col2 = st.columns(2)
with col1:
    bar_chart("Top 10 Damage Dealers (DPS)", "dps", n=10)
with col2:
    bar_chart("Top 5 Healers (HPS)", "hps", n=5)


# === Potion Usage ===
st.subheader("🧪 Potions")
col1, col2, col3, col4 = st.columns(4)
with col1:
    top_table("HASTE POTION", "haste_potion")
with col2:
    top_table("DESTRUCTION POTION", "destruction_potion")
with col3:
    top_table("ELIXIR OF DEMONSLAYING", "spell_elixir_of_demonslaying")
with col4:
    top_table("MANA POTION", "mana_potion")


# === Sappers ===
st.subheader("💥 Sappers")
col1, col2 = st.columns(2)
with col1:
    top_table("SUPER SAPPER CHARGE", "super_sapper_charge")
with col2:
    top_table("GOBLIN SAPPER CHARGE", "goblin_sapper_charge")


# === Necks ===
st.subheader("💎 Necks")
col1, col2, col3 = st.columns(3)
with col1:
    top_table("BRAIDED ETERNIUM CHAIN", "spell_braided_eternium_chain")
with col2:
    top_table("CHAIN OF THE TWILIGHT OWL", "spell_chain_of_the_twilight_owl")
with col3:
    top_table("EYE OF THE NIGHT", "spell_eye_of_the_night")

# === Warriors ===
st.subheader("⚔️ Warriors")
col1, col2, col3, col4 = st.columns(4)
with col1:
    top_table("SUNDER ARMOR", "spell_sunder_armor")
with col2:
    top_table("DEMORALIZING SHOUT", "spell_demoralizing_shout")
with col3:
    top_table("THUNDER CLAP", "spell_thunder_clap")
with col4:
    top_table("PUMMEL", "spell_pummel")


# === Druids ===
st.subheader("🐻 Druids")
col1, col2, col3, col4 = st.columns(4)
with col1:
    top_table("FAERIE FIRE", "spell_faerie_fire")
with col2:
    top_table("INSECT SWARM", "spell_insect_swarm")
with col3:
    top_table("INNERVATE", "spell_innervate")


# === Warlocks ===
st.subheader("💀 Warlocks")
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    top_table("CURSE OF THE ELEMENTS", "spell_curse_of_the_elements")
with col2:
    top_table("CURSE OF RECKLESSNESS", "spell_curse_of_recklessness")
with col3:
    top_table("CURSE OF TONGUES", "spell_curse_of_tongues")
with col4:
    top_table("CURSE OF AGONY", "spell_curse_of_agony")
with col5:
    top_table("CURSE OF DOOM", "spell_curse_of_doom")
with col6:
    top_table("SHADOW VULNERABILITY", "spell_shadow_vulnerability")


# === Shamans ===
st.subheader("🌀 Shamans")
col1, col2, col3, col4 = st.columns(4)
with col1:
    top_table("BLOODLUST", "spell_bloodlust")
with col2:
    top_table("MANA TIDE TOTEM", "spell_mana_tide_totem")
with col3:
    top_table("NATURE'S SWIFTNESS", "spell_natures_swiftness")
with col4:
    top_table("PURGE", "spell_purge")


st.subheader("✨ Buffs")
col1, col2, col3 = st.columns(3)
with col1:
    top_table("FORTITUDE", "spell_fortitude")
with col2:
    top_table("INTELLECT", "spell_intellect")
with col3:
    top_table("MOTW", "spell_mark_of_the_wild")


# === Other ===
st.subheader("🎭 Other")
col1, col2, col3, col4 = st.columns(4)
with col1:
    top_table("SCROLL OF STRENGTH", "spell_scroll_of_strength")
with col2:
    top_table("SCROLL OF AGILITY", "spell_scroll_of_agility")
with col3:
    top_table("DRUMS OF BATTLE", "spell_drums_of_battle")
with col4:
    top_table("DEMONIC/DARK RUNE", "spell_demonicdark_rune")


# === Resurrects ===
top_table("RESURRECTS", "spell_resurrects")
