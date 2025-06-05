from flask import Blueprint, jsonify, request
from src.models.database import db
from src.models.models import League, Team, Fixture, Prediction

api_bp = Blueprint('api', __name__)

@api_bp.route('/leagues', methods=['GET'])
def get_leagues():
    """Retorna todas as ligas/competições disponíveis"""
    leagues = League.query.all()
    result = []
    for league in leagues:
        result.append({
            'id': league.id,
            'api_id': league.api_id,
            'name': league.name,
            'country': league.country,
            'logo': league.logo,
            'season': league.season
        })
    return jsonify(result)

@api_bp.route('/leagues/<int:league_id>/fixtures', methods=['GET'])
def get_fixtures(league_id):
    """Retorna jogos de uma liga específica"""
    fixtures = Fixture.query.filter_by(league_id=league_id).all()
    result = []
    for fixture in fixtures:
        result.append({
            'id': fixture.id,
            'api_id': fixture.api_id,
            'date': fixture.date.isoformat(),
            'status': fixture.status,
            'home_team': fixture.home_team.name,
            'away_team': fixture.away_team.name,
            'home_goals': fixture.home_goals,
            'away_goals': fixture.away_goals
        })
    return jsonify(result)

@api_bp.route('/fixtures/<int:fixture_id>/predictions', methods=['GET'])
def get_predictions(fixture_id):
    """Retorna previsões para um jogo específico"""
    predictions = Prediction.query.filter_by(fixture_id=fixture_id).all()
    result = []
    for prediction in predictions:
        result.append({
            'id': prediction.id,
            'type': prediction.prediction_type,
            'value': prediction.prediction_value,
            'confidence': prediction.confidence,
            'is_value_bet': prediction.is_value_bet,
            'odds': prediction.odds,
            'created_at': prediction.created_at.isoformat()
        })
    return jsonify(result)

@api_bp.route('/analyze', methods=['POST'])
def analyze_fixtures():
    """Endpoint para analisar jogos selecionados"""
    data = request.get_json()
    fixture_ids = data.get('fixture_ids', [])
    
    # Placeholder para chamada ao modelo de IA
    # Será implementado na etapa de desenvolvimento da IA
    
    return jsonify({
        'status': 'processing',
        'message': f'Analisando {len(fixture_ids)} jogos',
        'fixture_ids': fixture_ids
    })
