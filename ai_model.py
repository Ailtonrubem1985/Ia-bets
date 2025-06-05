import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pandas as pd
from datetime import datetime, timedelta

class BettingModel:
    """Classe para o modelo de IA para análise de apostas esportivas"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.features = [
            'home_possession', 'away_possession',
            'home_shots', 'away_shots',
            'home_shots_on_target', 'away_shots_on_target',
            'home_corners', 'away_corners',
            'home_fouls', 'away_fouls',
            'home_yellow_cards', 'away_yellow_cards',
            'home_red_cards', 'away_red_cards',
            'home_form', 'away_form',
            'home_league_position', 'away_league_position',
            'home_goals_scored_avg', 'away_goals_scored_avg',
            'home_goals_conceded_avg', 'away_goals_conceded_avg'
        ]
        self.prediction_types = ['1X2', 'BTTS', 'Over/Under 2.5']
    
    def _build_model(self, input_shape):
        """Constrói a arquitetura da rede neural"""
        model = keras.Sequential([
            layers.Input(shape=(input_shape,)),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(16, activation='relu'),
            # Saída para múltiplas previsões (1X2, BTTS, Over/Under)
            layers.Dense(5, activation='softmax')  # [Home, Draw, Away, BTTS-Yes, Over2.5]
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _prepare_data(self, fixtures, statistics):
        """Prepara os dados para treinamento"""
        data = []
        labels = []
        
        for fixture in fixtures:
            # Pular jogos sem estatísticas ou resultados
            if fixture.status != 'Match Finished' or not fixture.home_goals or not fixture.away_goals:
                continue
            
            # Encontrar estatísticas do jogo
            stats = next((s for s in statistics if s.fixture_id == fixture.id), None)
            if not stats:
                continue
            
            # Calcular métricas de forma (últimos 5 jogos)
            home_team_fixtures = [f for f in fixtures if 
                                 (f.home_team_id == fixture.home_team_id or f.away_team_id == fixture.home_team_id) and
                                 f.date < fixture.date and f.status == 'Match Finished']
            home_team_fixtures = sorted(home_team_fixtures, key=lambda x: x.date, reverse=True)[:5]
            
            away_team_fixtures = [f for f in fixtures if 
                                 (f.home_team_id == fixture.away_team_id or f.away_team_id == fixture.away_team_id) and
                                 f.date < fixture.date and f.status == 'Match Finished']
            away_team_fixtures = sorted(away_team_fixtures, key=lambda x: x.date, reverse=True)[:5]
            
            # Calcular forma (pontos nos últimos 5 jogos)
            home_form = 0
            for f in home_team_fixtures:
                if f.home_team_id == fixture.home_team_id:
                    if f.home_goals > f.away_goals:
                        home_form += 3
                    elif f.home_goals == f.away_goals:
                        home_form += 1
                else:
                    if f.away_goals > f.home_goals:
                        home_form += 3
                    elif f.away_goals == f.home_goals:
                        home_form += 1
            
            away_form = 0
            for f in away_team_fixtures:
                if f.home_team_id == fixture.away_team_id:
                    if f.home_goals > f.away_goals:
                        away_form += 3
                    elif f.home_goals == f.away_goals:
                        away_form += 1
                else:
                    if f.away_goals > f.home_goals:
                        away_form += 3
                    elif f.away_goals == f.home_goals:
                        away_form += 1
            
            # Calcular médias de gols
            home_goals_scored = []
            home_goals_conceded = []
            for f in home_team_fixtures:
                if f.home_team_id == fixture.home_team_id:
                    home_goals_scored.append(f.home_goals)
                    home_goals_conceded.append(f.away_goals)
                else:
                    home_goals_scored.append(f.away_goals)
                    home_goals_conceded.append(f.home_goals)
            
            away_goals_scored = []
            away_goals_conceded = []
            for f in away_team_fixtures:
                if f.home_team_id == fixture.away_team_id:
                    away_goals_scored.append(f.home_goals)
                    away_goals_conceded.append(f.away_goals)
                else:
                    away_goals_scored.append(f.away_goals)
                    away_goals_conceded.append(f.home_goals)
            
            home_goals_scored_avg = sum(home_goals_scored) / len(home_goals_scored) if home_goals_scored else 0
            home_goals_conceded_avg = sum(home_goals_conceded) / len(home_goals_conceded) if home_goals_conceded else 0
            away_goals_scored_avg = sum(away_goals_scored) / len(away_goals_scored) if away_goals_scored else 0
            away_goals_conceded_avg = sum(away_goals_conceded) / len(away_goals_conceded) if away_goals_conceded else 0
            
            # Posição na liga (simplificada)
            home_league_position = 10  # Placeholder
            away_league_position = 10  # Placeholder
            
            # Criar vetor de características
            feature_vector = [
                stats.home_possession if stats.home_possession else 50,
                stats.away_possession if stats.away_possession else 50,
                stats.home_shots if stats.home_shots else 0,
                stats.away_shots if stats.away_shots else 0,
                stats.home_shots_on_target if stats.home_shots_on_target else 0,
                stats.away_shots_on_target if stats.away_shots_on_target else 0,
                stats.home_corners if stats.home_corners else 0,
                stats.away_corners if stats.away_corners else 0,
                stats.home_fouls if stats.home_fouls else 0,
                stats.away_fouls if stats.away_fouls else 0,
                stats.home_yellow_cards if stats.home_yellow_cards else 0,
                stats.away_yellow_cards if stats.away_yellow_cards else 0,
                stats.home_red_cards if stats.home_red_cards else 0,
                stats.away_red_cards if stats.away_red_cards else 0,
                home_form,
                away_form,
                home_league_position,
                away_league_position,
                home_goals_scored_avg,
                away_goals_scored_avg,
                home_goals_conceded_avg,
                away_goals_conceded_avg
            ]
            
            # Criar rótulos (1X2, BTTS, Over/Under 2.5)
            result_1x2 = 0  # Home win
            if fixture.home_goals < fixture.away_goals:
                result_1x2 = 2  # Away win
            elif fixture.home_goals == fixture.away_goals:
                result_1x2 = 1  # Draw
            
            btts = 1 if fixture.home_goals > 0 and fixture.away_goals > 0 else 0
            over_under = 1 if (fixture.home_goals + fixture.away_goals) > 2.5 else 0
            
            # One-hot encoding para resultado 1X2
            label_1x2 = [0, 0, 0]
            label_1x2[result_1x2] = 1
            
            # Combinar todos os rótulos
            label = label_1x2 + [btts, over_under]
            
            data.append(feature_vector)
            labels.append(label)
        
        return np.array(data), np.array(labels)
    
    def train(self, fixtures, statistics):
        """Treina o modelo com dados históricos"""
        X, y = self._prepare_data(fixtures, statistics)
        
        if len(X) < 100:
            print(f"Dados insuficientes para treinamento: {len(X)} amostras")
            return False
        
        # Normalizar dados
        X = self.scaler.fit_transform(X)
        
        # Dividir em treino e teste
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Construir e treinar modelo
        self.model = self._build_model(X_train.shape[1])
        
        # Callback para early stopping
        early_stopping = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        history = self.model.fit(
            X_train, y_train,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=[early_stopping],
            verbose=1
        )
        
        # Avaliar modelo
        loss, accuracy = self.model.evaluate(X_test, y_test)
        print(f"Acurácia do modelo: {accuracy:.4f}")
        
        return True
    
    def predict(self, fixture, statistics):
        """Gera previsões para um jogo específico"""
        if not self.model:
            return None
        
        # Encontrar estatísticas do jogo
        stats = next((s for s in statistics if s.fixture_id == fixture.id), None)
        if not stats:
            return None
        
        # Preparar dados para previsão (similar ao método _prepare_data)
        # Aqui precisaríamos implementar a mesma lógica de extração de características
        
        # Placeholder para demonstração
        feature_vector = [
            stats.home_possession if stats.home_possession else 50,
            stats.away_possession if stats.away_possession else 50,
            stats.home_shots if stats.home_shots else 0,
            stats.away_shots if stats.away_shots else 0,
            stats.home_shots_on_target if stats.home_shots_on_target else 0,
            stats.away_shots_on_target if stats.away_shots_on_target else 0,
            stats.home_corners if stats.home_corners else 0,
            stats.away_corners if stats.away_corners else 0,
            stats.home_fouls if stats.home_fouls else 0,
            stats.away_fouls if stats.away_fouls else 0,
            stats.home_yellow_cards if stats.home_yellow_cards else 0,
            stats.away_yellow_cards if stats.away_yellow_cards else 0,
            stats.home_red_cards if stats.home_red_cards else 0,
            stats.away_red_cards if stats.away_red_cards else 0,
            0,  # home_form (placeholder)
            0,  # away_form (placeholder)
            10,  # home_league_position (placeholder)
            10,  # away_league_position (placeholder)
            0,  # home_goals_scored_avg (placeholder)
            0,  # away_goals_scored_avg (placeholder)
            0,  # home_goals_conceded_avg (placeholder)
            0   # away_goals_conceded_avg (placeholder)
        ]
        
        # Normalizar dados
        X = self.scaler.transform([feature_vector])
        
        # Fazer previsão
        predictions = self.model.predict(X)[0]
        
        # Interpretar resultados
        result = {
            '1X2': {
                'Home': predictions[0],
                'Draw': predictions[1],
                'Away': predictions[2]
            },
            'BTTS': {
                'Yes': predictions[3],
                'No': 1 - predictions[3]
            },
            'Over/Under 2.5': {
                'Over': predictions[4],
                'Under': 1 - predictions[4]
            }
        }
        
        return result
    
    def detect_value_bets(self, prediction, odds):
        """Detecta value bets comparando previsões com odds do mercado"""
        value_bets = []
        
        # Converter probabilidades para odds implícitas
        implied_odds = {
            '1X2': {
                'Home': 1 / prediction['1X2']['Home'] if prediction['1X2']['Home'] > 0 else float('inf'),
                'Draw': 1 / prediction['1X2']['Draw'] if prediction['1X2']['Draw'] > 0 else float('inf'),
                'Away': 1 / prediction['1X2']['Away'] if prediction['1X2']['Away'] > 0 else float('inf')
            },
            'BTTS': {
                'Yes': 1 / prediction['BTTS']['Yes'] if prediction['BTTS']['Yes'] > 0 else float('inf'),
                'No': 1 / prediction['BTTS']['No'] if prediction['BTTS']['No'] > 0 else float('inf')
            },
            'Over/Under 2.5': {
                'Over': 1 / prediction['Over/Under 2.5']['Over'] if prediction['Over/Under 2.5']['Over'] > 0 else float('inf'),
                'Under': 1 / prediction['Over/Under 2.5']['Under'] if prediction['Over/Under 2.5']['Under'] > 0 else float('inf')
            }
        }
        
        # Comparar com odds do mercado
        # Exemplo: se odds implícitas < odds do mercado, é uma value bet
        for market in odds:
            for selection, market_odds in odds[market].items():
                if market in implied_odds and selection in implied_odds[market]:
                    implied = implied_odds[market][selection]
                    if market_odds > implied * 1.1:  # 10% de margem para value bet
                        value_bets.append({
                            'market': market,
                            'selection': selection,
                            'implied_odds': implied,
                            'market_odds': market_odds,
                            'value': (market_odds / implied - 1) * 100  # Valor em percentual
                        })
        
        return value_bets
    
    def save_model(self, path):
        """Salva o modelo treinado"""
        if self.model:
            self.model.save(path)
            return True
        return False
    
    def load_model(self, path):
        """Carrega um modelo treinado"""
        try:
            self.model = keras.models.load_model(path)
            return True
        except:
            return False
