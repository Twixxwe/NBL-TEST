"""
Rating system module for Elo-inspired NBL team ratings
"""

from datetime import datetime

class RatingSystem:
    def __init__(self, initial_ratings=None, team_mapping=None, k=0.05, home_adv=2.2):
        self.ratings = initial_ratings or {}
        self.team_mapping = team_mapping or {}
        self.k = k  # K-factor for rating changes
        self.home_adv = home_adv  # Home court advantage
        self.game_history = []
    
    def expected_mov(self, home_rating, away_rating):
        """Expected margin of victory"""
        return home_rating + self.home_adv - away_rating
    
    def delta_rating(self, actual_mov, expected_mov):
        """Rating change calculation"""
        return self.k * (actual_mov - expected_mov)
    
    def play_game(self, home, away, home_score, away_score):
        """Process a game and update ratings"""
        home_rating = self.ratings.get(home, 0.0)
        away_rating = self.ratings.get(away, 0.0)
        
        actual_mov = home_score - away_score
        exp_mov = self.expected_mov(home_rating, away_rating)
        dr = self.delta_rating(actual_mov, exp_mov)
        
        # Update ratings
        self.ratings[home] = home_rating + dr
        self.ratings[away] = away_rating - dr
        
        # Record game
        game_result = {
            'timestamp': datetime.now().isoformat(),
            'home': home,
            'away': away,
            'home_score': home_score,
            'away_score': away_score,
            'home_rating_before': home_rating,
            'away_rating_before': away_rating,
            'home_rating_after': self.ratings[home],
            'away_rating_after': self.ratings[away],
            'expected_mov': exp_mov,
            'actual_mov': actual_mov,
            'delta_rating': dr,
            'home_team_full': self.team_mapping.get(home, home),
            'away_team_full': self.team_mapping.get(away, away)
        }
        
        self.game_history.append(game_result)
        return game_result
    
    def get_standings(self):
        """Get current standings sorted by rating"""
        return sorted(
            [(self.team_mapping.get(team, team), rating) 
             for team, rating in self.ratings.items()],
            key=lambda x: x[1],
            reverse=True
        )
    
    def get_team_rating(self, team):
        """Get rating for specific team"""
        return self.ratings.get(team, 0.0)
    
    def predict_game(self, home, away):
        """Predict outcome of a future game"""
        home_rating = self.ratings.get(home, 0.0)
        away_rating = self.ratings.get(away, 0.0)
        
        expected = self.expected_mov(home_rating, away_rating)
        
        return {
            'home': home,
            'away': away,
            'home_rating': home_rating,
            'away_rating': away_rating,
            'expected_mov': expected,
            'home_win_probability': self._mov_to_probability(expected)
        }
    
    def _mov_to_probability(self, mov):
        """Convert margin of victory to win probability"""
        # Simple logistic function
        import math
        return 1 / (1 + math.exp(-mov / 10))
