from flask import Blueprint, request, jsonify
from src.models.models import Fixture, FixtureStatistics, Prediction
from src.models.database import db
from src.models.ai_model import BettingModel
import os
import pickle

ai_bp = Blueprint('ai', __name__)

# Caminho para salvar/carregar o modelo
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'model')
os.makedirs(MODEL_PATH, exist_ok=True)
MODEL_FILE = os.path.join(MODEL_PATH, 'betting_model.h5')
SCALER_FILE = os.path.join(MODEL_PATH, 'scaler.pkl')

# Instância global do modelo
betting_model = BettingModel()

@ai_bp.route('/train', methods=['POST'])
def train_model():
    """Treina o modelo com dados históricos"""
    from src.models.models import Fixture, FixtureStatistics
    
    # Obter todos os jogos finalizados com estatísticas
    fixtures = Fixture.query.filter_by(status='Match Finished').all()
    statistics = FixtureStatistics.query.all()
    
    if len(fixtures) < 100:
        return jsonify({
            'success': False,
            'message': f'Dados insuficientes para treinamento. Necessário pelo menos 100 jogos, encontrados {len(fixtures)}.'
        })
    
    # Treinar modelo
    success = betting_model.train(fixtures, statistics)
    
    if success:
        # Salvar modelo treinado
        betting_model.save_model(MODEL_FILE)
        
        # Salvar scaler
        with open(SCALER_FILE, 'wb') as f:
            pickle.dump(betting_model.scaler, f)
        
        return jsonify({
            'success': True,
            'message': f'Modelo treinado com sucesso usando {len(fixtures)} jogos.'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Falha ao treinar o modelo.'
        })

@ai_bp.route('/predict', methods=['POST'])
def predict():
    """Gera previsões para jogos selecionados"""
    data = request.get_json()
    fixture_ids = data.get('fixture_ids', [])
    
    if not fixture_ids:
        return jsonify({
            'success': False,
            'message': 'Nenhum jogo selecionado para análise.'
        })
    
    # Verificar se o modelo está carregado
    if not betting_model.model:
        # Tentar carregar modelo salvo
        if os.path.exists(MODEL_FILE):
            betting_model.load_model(MODEL_FILE)
            
            # Carregar scaler
            if os.path.exists(SCALER_FILE):
                with open(SCALER_FILE, 'rb') as f:
                    betting_model.scaler = pickle.load(f)
        else:
            return jsonify({
                'success': False,
                'message': 'Modelo não treinado. Execute o treinamento primeiro.'
            })
    
    results = []
    
    for fixture_id in fixture_ids:
        fixture = Fixture.query.get(fixture_id)
        if not fixture:
            continue
        
        statistics = FixtureStatistics.query.filter_by(fixture_id=fixture_id).first()
        if not statistics:
            continue
        
        # Gerar previsão
        prediction = betting_model.predict(fixture, statistics)
        
        if not prediction:
            continue
        
        # Simular odds do mercado (em produção, seriam obtidas da API)
        market_odds = {
            '1X2': {
                'Home': 2.0,
                'Draw': 3.5,
                'Away': 3.8
            },
            'BTTS': {
                'Yes': 1.9,
                'No': 1.9
            },
            'Over/Under 2.5': {
                'Over': 1.85,
                'Under': 1.95
            }
        }
        
        # Detectar value bets
        value_bets = betting_model.detect_value_bets(prediction, market_odds)
        
        # Salvar previsões no banco de dados
        for market, values in prediction.items():
            for selection, confidence in values.items():
                # Verificar se é uma value bet
                is_value = any(vb['market'] == market and vb['selection'] == selection for vb in value_bets)
                
                # Obter odds do mercado
                odds = market_odds.get(market, {}).get(selection, None)
                
                # Criar previsão
                pred = Prediction(
                    fixture_id=fixture.id,
                    prediction_type=market,
                    prediction_value=selection,
                    confidence=float(confidence),
                    is_value_bet=is_value,
                    odds=odds
                )
                db.session.add(pred)
        
        # Adicionar ao resultado
        results.append({
            'fixture_id': fixture.id,
            'home_team': fixture.home_team.name,
            'away_team': fixture.away_team.name,
            'predictions': prediction,
            'value_bets': value_bets
        })
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Análise concluída para {len(results)} jogos.',
        'results': results
    })
