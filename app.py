"""
NBL Team Ratings Dashboard
Streamlit app for real-time NBL team ratings with FlashScore integration
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
from utils.scraper import FlashScoreScraper
from utils.ratings import RatingSystem

# Page configuration
st.set_page_config(
    page_title="NBL Team Ratings Dashboard",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_initial_data():
    """Load initial ratings and team mapping"""
    with open('data/initial_ratings.json', 'r') as f:
        initial_ratings = json.load(f)
    with open('data/team_mapping.json', 'r') as f:
        team_mapping = json.load(f)
    return initial_ratings, team_mapping

def save_game_history(history):
    """Save game history to CSV"""
    if history:
        df = pd.DataFrame(history)
        df.to_csv('data/game_history.csv', index=False)

def load_game_history():
    """Load game history from CSV"""
    if os.path.exists('data/game_history.csv'):
        return pd.read_csv('data/game_history.csv').to_dict('records')
    return []

def main():
    # Initialize session state
    if 'ratings_system' not in st.session_state:
        initial_ratings, team_mapping = load_initial_data()
        st.session_state.ratings_system = RatingSystem(initial_ratings, team_mapping)
        st.session_state.game_history = load_game_history()
        st.session_state.last_scrape = None
    
    # Title and header
    st.title("🏀 NBL 2025/2026 Team Ratings Dashboard")
    st.markdown("""
    **Real-time team ratings** based on game results using an Elo-inspired system.
    Scores are automatically fetched from [FlashScore](https://www.flashscoreusa.com/basketball/australia/nbl/results/).
    """)
    
    # Sidebar
    with st.sidebar:
        st.image("assets/nbl_logo.png", width=150) if os.path.exists("assets/nbl_logo.png") else None
        
        st.header("⚙️ Configuration")
        
        # Parameters
        k_value = st.slider(
            "K-factor (rating change sensitivity)",
            min_value=0.01, max_value=0.2,
            value=st.session_state.ratings_system.k, step=0.01
        )
        
        home_adv = st.slider(
            "Home Court Advantage",
            min_value=0.0, max_value=5.0,
            value=st.session_state.ratings_system.home_adv, step=0.1
        )
        
        # Update parameters
        st.session_state.ratings_system.k = k_value
        st.session_state.ratings_system.home_adv = home_adv
        
        st.divider()
        
        # Manual game entry
        st.subheader("➕ Add Manual Game")
        with st.form("manual_game_form"):
            col1, col2 = st.columns(2)
            with col1:
                home_team = st.selectbox(
                    "Home Team",
                    options=list(st.session_state.ratings_system.team_mapping.keys())[:10]
                )
            with col2:
                away_team = st.selectbox(
                    "Away Team",
                    options=list(st.session_state.ratings_system.team_mapping.keys())[:10]
                )
            
            home_score = st.number_input("Home Score", min_value=0, max_value=200, value=90)
            away_score = st.number_input("Away Score", min_value=0, max_value=200, value=85)
            
            if st.form_submit_button("Add Game", use_container_width=True):
                result = st.session_state.ratings_system.play_game(
                    home_team, away_team, home_score, away_score
                )
                st.session_state.game_history.append(result)
                save_game_history(st.session_state.game_history)
                st.success(f"Game added! {home_team} {home_score}-{away_score} {away_team}")
                st.rerun()
        
        st.divider()
        
        # Data management
        st.subheader("🗃️ Data Management")
        
        col_reset, col_export = st.columns(2)
        with col_reset:
            if st.button("🔄 Reset", use_container_width=True):
                initial_ratings, _ = load_initial_data()
                st.session_state.ratings_system = RatingSystem(initial_ratings)
                st.session_state.game_history = []
                save_game_history([])
                st.rerun()
        
        with col_export:
            if st.button("📥 Export", use_container_width=True):
                # Create export data
                export_data = {
                    "timestamp": datetime.now().isoformat(),
                    "parameters": {
                        "k": k_value,
                        "home_advantage": home_adv
                    },
                    "ratings": st.session_state.ratings_system.ratings,
                    "games_played": len(st.session_state.game_history)
                }
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"nbl_ratings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Live updates section
        st.header("📊 Live Updates")
        
        update_tab, manual_tab = st.tabs(["🔄 Auto Update", "📝 Manual Entry"])
        
        with update_tab:
            st.subheader("Fetch Latest Games from FlashScore")
            
            col_fetch, col_status = st.columns([3, 1])
            with col_fetch:
                if st.button("🚀 Scrape Latest Results", use_container_width=True):
                    with st.spinner("Fetching data from FlashScore..."):
                        scraper = FlashScoreScraper(st.session_state.ratings_system.team_mapping)
                        new_games = scraper.scrape()
                        
                        if new_games:
                            added_count = 0
                            for game in new_games:
                                # Check if game already exists
                                game_exists = any(
                                    g.get('home') == game['home'] and 
                                    g.get('away') == game['away'] and 
                                    g.get('home_score') == game['home_score'] and 
                                    g.get('away_score') == game['away_score']
                                    for g in st.session_state.game_history
                                )
                                
                                if not game_exists:
                                    result = st.session_state.ratings_system.play_game(
                                        game['home'], game['away'],
                                        game['home_score'], game['away_score']
                                    )
                                    st.session_state.game_history.append(result)
                                    added_count += 1
                            
                            if added_count > 0:
                                save_game_history(st.session_state.game_history)
                                st.success(f"✅ Added {added_count} new games!")
                                st.session_state.last_scrape = datetime.now()
                                st.rerun()
                            else:
                                st.info("📭 No new games found.")
                        else:
                            st.warning("⚠️ Could not fetch games. Check your connection.")
            
            with col_status:
                if st.session_state.last_scrape:
                    st.caption(f"Last updated: {st.session_state.last_scrape.strftime('%H:%M')}")
        
        with manual_tab:
            # Recent games table
            if st.session_state.game_history:
                st.subheader("Recent Games")
                recent_games = st.session_state.game_history[-10:]
                
                games_data = []
                for game in recent_games:
                    games_data.append({
                        "Date": game.get('timestamp', 'N/A'),
                        "Match": f"{game['home']} vs {game['away']}",
                        "Score": f"{game['home_score']} - {game['away_score']}",
                        "Δ Rating": f"{game.get('delta_rating', 0):+.2f}"
                    })
                
                st.dataframe(
                    pd.DataFrame(games_data),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No games recorded yet. Add games manually or fetch from FlashScore.")
    
    with col2:
        # Current standings
        st.header("📈 Current Standings")
        
        standings = st.session_state.ratings_system.get_standings()
        
        for i, (team, rating) in enumerate(standings, 1):
            with st.container():
                col_rank, col_team, col_rating = st.columns([0.5, 2, 1])
                with col_rank:
                    st.markdown(f"**{i}**")
                with col_team:
                    st.markdown(f"**{team}**")
                with col_rating:
                    color = "green" if rating >= 0 else "red"
                    st.markdown(f"<span style='color:{color}'>{rating:+.2f}</span>", 
                               unsafe_allow_html=True)
                st.progress(min(max((rating + 10) / 20, 0), 1))
        
        # Stats summary
        st.divider()
        
        if standings:
            avg_rating = sum(r for _, r in standings) / len(standings)
            top_team, top_rating = standings[0]
            bottom_team, bottom_rating = standings[-1]
            
            col_avg, col_top, col_bottom = st.columns(3)
            with col_avg:
                st.metric("Avg Rating", f"{avg_rating:+.2f}")
            with col_top:
                st.metric("Top Team", f"{top_team[:10]}...", f"{top_rating:+.2f}")
            with col_bottom:
                st.metric("Bottom Team", f"{bottom_team[:10]}...", f"{bottom_rating:+.2f}")
    
    # Charts and analytics
    st.header("📊 Analytics")
    
    tab1, tab2, tab3 = st.tabs(["📈 Ratings Trend", "🎯 Distribution", "📋 Game Log"])
    
    with tab1:
        if len(st.session_state.game_history) > 1:
            # Create rating trend chart
            import plotly.express as px
            
            # Prepare data for visualization
            trend_data = []
            for game in st.session_state.game_history:
                trend_data.append({
                    'Game': len(trend_data) + 1,
                    'Home Team': game['home'],
                    'Home Δ': game.get('delta_rating', 0),
                    'Away Team': game['away'],
                    'Away Δ': -game.get('delta_rating', 0)
                })
            
            if trend_data:
                df_trend = pd.DataFrame(trend_data)
                fig = px.line(df_trend, x='Game', y=['Home Δ', 'Away Δ'],
                            title="Rating Changes Over Games")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Play more games to see rating trends.")
    
    with tab2:
        # Rating distribution
        import plotly.graph_objects as go
        
        ratings_list = list(st.session_state.ratings_system.ratings.values())
        
        fig = go.Figure(data=[go.Histogram(x=ratings_list, nbinsx=10)])
        fig.update_layout(
            title="Rating Distribution",
            xaxis_title="Rating",
            yaxis_title="Count"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Full game log
        if st.session_state.game_history:
            full_log = []
            for game in st.session_state.game_history:
                full_log.append({
                    "Home": game['home'],
                    "Away": game['away'],
                    "Score": f"{game['home_score']}-{game['away_score']}",
                    "Home Rating": f"{game.get('home_rating_before', 0):.2f} → {game.get('home_rating_after', 0):.2f}",
                    "Away Rating": f"{game.get('away_rating_before', 0):.2f} → {game.get('away_rating_after', 0):.2f}",
                    "Δ Rating": f"{game.get('delta_rating', 0):+.2f}"
                })
            
            st.dataframe(
                pd.DataFrame(full_log).iloc[::-1],  # Reverse to show latest first
                use_container_width=True,
                height=400
            )
        else:
            st.info("No games in the log yet.")
    
    # Footer
    st.divider()
    st.caption(f"🏀 NBL Ratings System • Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("[View on GitHub](https://github.com/yourusername/nbl-ratings) • Data source: FlashScore")

if __name__ == "__main__":
    main()
