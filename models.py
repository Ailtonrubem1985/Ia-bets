from src.models.database import db
from datetime import datetime

class League(db.Model):
    """Modelo para ligas/competições"""
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100))
    logo = db.Column(db.String(255))
    season = db.Column(db.Integer)
    fixtures = db.relationship('Fixture', backref='league', lazy=True)
    
    def __repr__(self):
        return f'<League {self.name}>'

class Team(db.Model):
    """Modelo para times"""
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.String(255))
    home_fixtures = db.relationship('Fixture', backref='home_team', 
                                   foreign_keys='Fixture.home_team_id', lazy=True)
    away_fixtures = db.relationship('Fixture', backref='away_team', 
                                   foreign_keys='Fixture.away_team_id', lazy=True)
    
    def __repr__(self):
        return f'<Team {self.name}>'

class Fixture(db.Model):
    """Modelo para partidas/jogos"""
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True)
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'), nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50))
    home_goals = db.Column(db.Integer)
    away_goals = db.Column(db.Integer)
    statistics = db.relationship('FixtureStatistics', backref='fixture', lazy=True)
    predictions = db.relationship('Prediction', backref='fixture', lazy=True)
    
    def __repr__(self):
        return f'<Fixture {self.home_team.name} vs {self.away_team.name}>'

class FixtureStatistics(db.Model):
    """Modelo para estatísticas de partidas"""
    id = db.Column(db.Integer, primary_key=True)
    fixture_id = db.Column(db.Integer, db.ForeignKey('fixture.id'), nullable=False)
    home_possession = db.Column(db.Float)
    away_possession = db.Column(db.Float)
    home_shots = db.Column(db.Integer)
    away_shots = db.Column(db.Integer)
    home_shots_on_target = db.Column(db.Integer)
    away_shots_on_target = db.Column(db.Integer)
    home_corners = db.Column(db.Integer)
    away_corners = db.Column(db.Integer)
    home_fouls = db.Column(db.Integer)
    away_fouls = db.Column(db.Integer)
    home_yellow_cards = db.Column(db.Integer)
    away_yellow_cards = db.Column(db.Integer)
    home_red_cards = db.Column(db.Integer)
    away_red_cards = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<Statistics for Fixture {self.fixture_id}>'

class Prediction(db.Model):
    """Modelo para previsões/tips gerados pela IA"""
    id = db.Column(db.Integer, primary_key=True)
    fixture_id = db.Column(db.Integer, db.ForeignKey('fixture.id'), nullable=False)
    prediction_type = db.Column(db.String(50), nullable=False)  # 1X2, BTTS, Over/Under, etc.
    prediction_value = db.Column(db.String(50), nullable=False)  # Home, Away, Draw, Yes, No, etc.
    confidence = db.Column(db.Float, nullable=False)  # 0.0 a 1.0
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_value_bet = db.Column(db.Boolean, default=False)
    odds = db.Column(db.Float)  # Odds disponíveis no mercado
    
    def __repr__(self):
        return f'<Prediction {self.prediction_type} {self.prediction_value} ({self.confidence:.2f})>'
