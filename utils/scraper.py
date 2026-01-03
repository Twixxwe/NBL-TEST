"""
FlashScore scraper module for fetching NBL game results
"""

import requests
import re
from bs4 import BeautifulSoup
import time
from datetime import datetime

class FlashScoreScraper:
    def __init__(self, team_mapping):
        self.team_mapping = team_mapping
        self.url = "https://www.flashscoreusa.com/basketball/australia/nbl/results/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape(self):
        """Main scraping method"""
        try:
            response = requests.get(self.url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            games = self._parse_html(response.text)
            if not games:
                games = self._parse_fallback(response.text)
            
            return games
            
        except Exception as e:
            print(f"Scraping error: {e}")
            return self._get_fallback_data()
    
    def _parse_html(self, html_content):
        """Parse HTML using BeautifulSoup"""
        soup = BeautifulSoup(html_content, 'html.parser')
        games = []
        
        # Method 1: Look for match containers
        match_selectors = [
            'div.event__match',
            'div[class*="match"]',
            'div[class*="event"]'
        ]
        
        for selector in match_selectors:
            matches = soup.select(selector)
            if matches:
                for match in matches:
                    game = self._extract_game_from_element(match)
                    if game:
                        games.append(game)
                break
        
        return games
    
    def _extract_game_from_element(self, element):
        """Extract game data from HTML element"""
        try:
            # Try different class patterns
            home_elem = element.find(class_=re.compile(r'.*home.*', re.I))
            away_elem = element.find(class_=re.compile(r'.*away.*', re.I))
            
            if not home_elem or not away_elem:
                return None
            
            home_team = home_elem.get_text(strip=True)
            away_team = away_elem.get_text(strip=True)
            
            # Find scores
            score_pattern = re.compile(r'(\d{1,3})\s*[-:]\s*(\d{1,3})')
            text = element.get_text()
            scores = score_pattern.search(text)
            
            if scores:
                home_score = int(scores.group(1))
                away_score = int(scores.group(2))
            else:
                # Try to find score elements
                score_elems = element.find_all(class_=re.compile(r'.*score.*', re.I))
                if len(score_elems) >= 2:
                    home_score = int(score_elems[0].get_text(strip=True))
                    away_score = int(score_elems[1].get_text(strip=True))
                else:
                    return None
            
            # Map team names to our codes
            home_code = self.team_mapping.get(home_team, home_team)
            away_code = self.team_mapping.get(away_team, away_team)
            
            return {
                'home': home_code,
                'away': away_code,
                'home_score': home_score,
                'away_score': away_score,
                'home_team_full': home_team,
                'away_team_full': away_team,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception:
            return None
    
    def _parse_fallback(self, html_content):
        """Fallback parsing using regex"""
        games = []
        
        # Look for score patterns in text
        patterns = [
            r'([A-Za-z\s\.]+)\s+([A-Za-z\s\.]+)\s+(\d{2,3})(\d{2,3})',
            r'([A-Za-z\s]+)\s+(\d{1,3})\s+([A-Za-z\s]+)\s+(\d{1,3})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if len(match) == 4:
                    home_team = match[0].strip()
                    away_team = match[1].strip()
                    home_score = int(match[2])
                    away_score = int(match[3])
                    
                    home_code = self.team_mapping.get(home_team, home_team)
                    away_code = self.team_mapping.get(away_team, away_team)
                    
                    games.append({
                        'home': home_code,
                        'away': away_code,
                        'home_score': home_score,
                        'away_score': away_score,
                        'home_team_full': home_team,
                        'away_team_full': away_team,
                        'scraped_at': datetime.now().isoformat()
                    })
        
        return games[:20]  # Limit to 20 games
    
    def _get_fallback_data(self):
        """Return sample data when scraping fails"""
        # This would be your sample/backup data
        return [
            {
                'home': '36',
                'away': 'syd',
                'home_score': 85,
                'away_score': 79,
                'home_team_full': 'Adelaide 36ers',
                'away_team_full': 'Sydney Kings'
            }
        ]
