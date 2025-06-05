import requests
import time
from datetime import datetime
from src.models.database import db
from src.models.models import League, Team, Fixture, FixtureStatistics

class FootballAPI:
    """Classe para interagir com a API-Football"""
    
    BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
    
    def __init__(self, api_key):
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
    
    def _make_request(self, endpoint, params=None):
        """Faz uma requisição para a API com tratamento de limites de requisição"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            # Verificar limites de requisição
            remaining = int(response.headers.get('x-ratelimit-requests-remaining', 0))
            if remaining < 5:
                print(f"Atenção: Apenas {remaining} requisições restantes hoje!")
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição: {e}")
            return None
    
    def get_leagues(self, current=True):
        """Obtém as principais ligas disponíveis"""
        params = {"current": "true" if current else "false"}
        return self._make_request("leagues", params)
    
    def get_league_by_id(self, league_id):
        """Obtém informações de uma liga específica"""
        params = {"id": league_id}
        return self._make_request("leagues", params)
    
    def get_fixtures_by_league(self, league_id, season):
        """Obtém jogos de uma liga específica"""
        params = {"league": league_id, "season": season}
        return self._make_request("fixtures", params)
    
    def get_fixture_by_id(self, fixture_id):
        """Obtém informações de um jogo específico"""
        params = {"id": fixture_id}
        return self._make_request("fixtures", params)
    
    def get_fixture_statistics(self, fixture_id):
        """Obtém estatísticas de um jogo específico"""
        params = {"fixture": fixture_id}
        return self._make_request("fixtures/statistics", params)
    
    def get_teams_by_league(self, league_id, season):
        """Obtém times de uma liga específica"""
        params = {"league": league_id, "season": season}
        return self._make_request("teams", params)


class DataManager:
    """Classe para gerenciar a coleta e armazenamento de dados"""
    
    def __init__(self, api_key):
        self.api = FootballAPI(api_key)
    
    def sync_leagues(self, leagues_to_sync=None):
        """Sincroniza as ligas principais com o banco de dados"""
        response = self.api.get_leagues(current=True)
        if not response or 'response' not in response:
            return False
        
        leagues_added = 0
        
        for league_data in response['response']:
            league_info = league_data['league']
            country_info = league_data['country']
            
            # Se uma lista específica de ligas foi fornecida, verificar se esta está incluída
            if leagues_to_sync and league_info['id'] not in leagues_to_sync:
                continue
            
            # Verificar se a liga já existe no banco
            league = League.query.filter_by(api_id=league_info['id']).first()
            
            if not league:
                league = League(
                    api_id=league_info['id'],
                    name=league_info['name'],
                    country=country_info['name'],
                    logo=league_info['logo'],
                    season=league_data['seasons'][-1]['year'] if league_data['seasons'] else None
                )
                db.session.add(league)
                leagues_added += 1
            
        db.session.commit()
        return leagues_added
    
    def sync_teams(self, league_id, season):
        """Sincroniza os times de uma liga com o banco de dados"""
        league = League.query.filter_by(api_id=league_id).first()
        if not league:
            return False
        
        response = self.api.get_teams_by_league(league_id, season)
        if not response or 'response' not in response:
            return False
        
        teams_added = 0
        
        for team_data in response['response']:
            team_info = team_data['team']
            
            # Verificar se o time já existe no banco
            team = Team.query.filter_by(api_id=team_info['id']).first()
            
            if not team:
                team = Team(
                    api_id=team_info['id'],
                    name=team_info['name'],
                    logo=team_info['logo']
                )
                db.session.add(team)
                teams_added += 1
        
        db.session.commit()
        return teams_added
    
    def sync_fixtures(self, league_id, season):
        """Sincroniza os jogos de uma liga com o banco de dados"""
        league = League.query.filter_by(api_id=league_id).first()
        if not league:
            return False
        
        response = self.api.get_fixtures_by_league(league_id, season)
        if not response or 'response' not in response:
            return False
        
        fixtures_added = 0
        
        for fixture_data in response['response']:
            fixture_info = fixture_data['fixture']
            teams_info = fixture_data['teams']
            goals_info = fixture_data['goals']
            
            # Verificar se o jogo já existe no banco
            fixture = Fixture.query.filter_by(api_id=fixture_info['id']).first()
            
            # Obter os times (ou criar se não existirem)
            home_team = Team.query.filter_by(api_id=teams_info['home']['id']).first()
            if not home_team:
                home_team = Team(
                    api_id=teams_info['home']['id'],
                    name=teams_info['home']['name'],
                    logo=teams_info['home'].get('logo')
                )
                db.session.add(home_team)
                db.session.flush()  # Para obter o ID gerado
            
            away_team = Team.query.filter_by(api_id=teams_info['away']['id']).first()
            if not away_team:
                away_team = Team(
                    api_id=teams_info['away']['id'],
                    name=teams_info['away']['name'],
                    logo=teams_info['away'].get('logo')
                )
                db.session.add(away_team)
                db.session.flush()  # Para obter o ID gerado
            
            if not fixture:
                # Converter timestamp para datetime
                date = datetime.fromtimestamp(fixture_info['timestamp'])
                
                fixture = Fixture(
                    api_id=fixture_info['id'],
                    league_id=league.id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    date=date,
                    status=fixture_info['status']['long'],
                    home_goals=goals_info['home'],
                    away_goals=goals_info['away']
                )
                db.session.add(fixture)
                fixtures_added += 1
            else:
                # Atualizar informações do jogo se já existir
                fixture.status = fixture_info['status']['long']
                fixture.home_goals = goals_info['home']
                fixture.away_goals = goals_info['away']
        
        db.session.commit()
        return fixtures_added
    
    def sync_fixture_statistics(self, fixture_id):
        """Sincroniza as estatísticas de um jogo com o banco de dados"""
        fixture = Fixture.query.filter_by(api_id=fixture_id).first()
        if not fixture:
            return False
        
        response = self.api.get_fixture_statistics(fixture_id)
        if not response or 'response' not in response:
            return False
        
        # Verificar se já existem estatísticas para este jogo
        stats = FixtureStatistics.query.filter_by(fixture_id=fixture.id).first()
        if not stats:
            stats = FixtureStatistics(fixture_id=fixture.id)
            db.session.add(stats)
        
        # Processar estatísticas do time da casa
        home_stats = next((item for item in response['response'] if item['team']['id'] == fixture.home_team.api_id), None)
        if home_stats and 'statistics' in home_stats:
            for stat in home_stats['statistics']:
                if stat['type'] == 'Ball Possession':
                    stats.home_possession = float(stat['value'].replace('%', '')) if stat['value'] else None
                elif stat['type'] == 'Total Shots':
                    stats.home_shots = int(stat['value']) if stat['value'] else None
                elif stat['type'] == 'Shots on Goal':
                    stats.home_shots_on_target = int(stat['value']) if stat['value'] else None
                elif stat['type'] == 'Corner Kicks':
                    stats.home_corners = int(stat['value']) if stat['value'] else None
                elif stat['type'] == 'Fouls':
                    stats.home_fouls = int(stat['value']) if stat['value'] else None
                elif stat['type'] == 'Yellow Cards':
                    stats.home_yellow_cards = int(stat['value']) if stat['value'] else None
                elif stat['type'] == 'Red Cards':
                    stats.home_red_cards = int(stat['value']) if stat['value'] else None
        
        # Processar estatísticas do time visitante
        away_stats = next((item for item in response['response'] if item['team']['id'] == fixture.away_team.api_id), None)
        if away_stats and 'statistics' in away_stats:
            for stat in away_stats['statistics']:
                if stat['type'] == 'Ball Possession':
                    stats.away_possession = float(stat['value'].replace('%', '')) if stat['value'] else None
                elif stat['type'] == 'Total Shots':
                    stats.away_shots = int(stat['value']) if stat['value'] else None
                elif stat['type'] == 'Shots on Goal':
                    stats.away_shots_on_target = int(stat['value']) if stat['value'] else None
                elif stat['type'] == 'Corner Kicks':
                    stats.away_corners = int(stat['value']) if stat['value'] else None
                elif stat['type'] == 'Fouls':
                    stats.away_fouls = int(stat['value']) if stat['value'] else None
                elif stat['type'] == 'Yellow Cards':
                    stats.away_yellow_cards = int(stat['value']) if stat['value'] else None
                elif stat['type'] == 'Red Cards':
                    stats.away_red_cards = int(stat['value']) if stat['value'] else None
        
        db.session.commit()
        return True
