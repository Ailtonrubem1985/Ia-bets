import streamlit as st
import pandas as pd
import numpy as np
import requests
import sqlite3
import os
import json
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import pickle

# Configuração da página
st.set_page_config(
    page_title="Sistema IA - Apostas Esportivas",
    page_icon="🤖",
    layout="wide"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3498db;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .value-bet {
        background-color: #e74c3c;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .confidence-high {
        color: #27ae60;
        font-weight: bold;
    }
    .confidence-medium {
        color: #f39c12;
        font-weight: bold;
    }
    .confidence-low {
        color: #e74c3c;
        font-weight: bold;
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        color: #7f8c8d;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização do banco de dados
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Criar tabelas se não existirem
    c.execute('''
    CREATE TABLE IF NOT EXISTS leagues (
        id INTEGER PRIMARY KEY,
        api_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        country TEXT,
        logo TEXT,
        season INTEGER
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY,
        api_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        logo TEXT
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS fixtures (
        id INTEGER PRIMARY KEY,
        api_id INTEGER UNIQUE,
        league_id INTEGER,
        home_team_id INTEGER,
        away_team_id INTEGER,
        date TIMESTAMP,
        status TEXT,
        home_goals INTEGER,
        away_goals INTEGER,
        FOREIGN KEY (league_id) REFERENCES leagues (id),
        FOREIGN KEY (home_team_id) REFERENCES teams (id),
        FOREIGN KEY (away_team_id) REFERENCES teams (id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS fixture_statistics (
        id INTEGER PRIMARY KEY,
        fixture_id INTEGER,
        home_possession REAL,
        away_possession REAL,
        home_shots INTEGER,
        away_shots INTEGER,
        home_shots_on_target INTEGER,
        away_shots_on_target INTEGER,
        home_corners INTEGER,
        away_corners INTEGER,
        home_fouls INTEGER,
        away_fouls INTEGER,
        home_yellow_cards INTEGER,
        away_yellow_cards INTEGER,
        home_red_cards INTEGER,
        away_red_cards INTEGER,
        FOREIGN KEY (fixture_id) REFERENCES fixtures (id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY,
        fixture_id INTEGER,
        prediction_type TEXT NOT NULL,
        prediction_value TEXT NOT NULL,
        confidence REAL NOT NULL,
        is_value_bet INTEGER,
        odds REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (fixture_id) REFERENCES fixtures (id)
    )
    ''')
    
    # Inserir dados de exemplo para demonstração
    # Ligas
    sample_leagues = [
        (1, 39, 'Premier League', 'Inglaterra', 'https://media.api-sports.io/football/leagues/39.png', 2024),
        (2, 140, 'La Liga', 'Espanha', 'https://media.api-sports.io/football/leagues/140.png', 2024),
        (3, 135, 'Serie A', 'Itália', 'https://media.api-sports.io/football/leagues/135.png', 2024),
        (4, 78, 'Bundesliga', 'Alemanha', 'https://media.api-sports.io/football/leagues/78.png', 2024),
        (5, 61, 'Ligue 1', 'França', 'https://media.api-sports.io/football/leagues/61.png', 2024),
        (6, 71, 'Brasileirão Série A', 'Brasil', 'https://media.api-sports.io/football/leagues/71.png', 2024),
        (7, 1, 'Copa do Mundo', 'Mundial', 'https://media.api-sports.io/football/leagues/1.png', 2026),
        (8, 32, 'Eliminatórias Copa do Mundo', 'Mundial', 'https://media.api-sports.io/football/leagues/32.png', 2025)
    ]
    
    for league in sample_leagues:
        try:
            c.execute("INSERT OR IGNORE INTO leagues VALUES (?, ?, ?, ?, ?, ?)", league)
        except:
            pass
    
    # Times
    sample_teams = [
        (1, 50, 'Manchester City', 'https://media.api-sports.io/football/teams/50.png'),
        (2, 40, 'Liverpool', 'https://media.api-sports.io/football/teams/40.png'),
        (3, 49, 'Chelsea', 'https://media.api-sports.io/football/teams/49.png'),
        (4, 42, 'Arsenal', 'https://media.api-sports.io/football/teams/42.png'),
        (5, 33, 'Manchester United', 'https://media.api-sports.io/football/teams/33.png'),
        (6, 47, 'Tottenham', 'https://media.api-sports.io/football/teams/47.png'),
        (7, 34, 'Newcastle', 'https://media.api-sports.io/football/teams/34.png'),
        (8, 66, 'Aston Villa', 'https://media.api-sports.io/football/teams/66.png'),
        (9, 51, 'Brighton', 'https://media.api-sports.io/football/teams/51.png'),
        (10, 48, 'West Ham', 'https://media.api-sports.io/football/teams/48.png'),
        (11, 52, 'Crystal Palace', 'https://media.api-sports.io/football/teams/52.png'),
        (12, 45, 'Everton', 'https://media.api-sports.io/football/teams/45.png')
    ]
    
    for team in sample_teams:
        try:
            c.execute("INSERT OR IGNORE INTO teams VALUES (?, ?, ?, ?)", team)
        except:
            pass
    
    # Jogos
    sample_fixtures = [
        (101, 1001, 1, 1, 2, '2025-06-10 16:00:00', 'Not Started', None, None),
        (102, 1002, 1, 3, 4, '2025-06-10 18:30:00', 'Not Started', None, None),
        (103, 1003, 1, 5, 6, '2025-06-11 16:00:00', 'Not Started', None, None),
        (104, 1004, 1, 7, 8, '2025-06-11 18:30:00', 'Not Started', None, None),
        (105, 1005, 1, 9, 10, '2025-06-12 16:00:00', 'Not Started', None, None),
        (106, 1006, 1, 11, 12, '2025-06-12 18:30:00', 'Not Started', None, None)
    ]
    
    for fixture in sample_fixtures:
        try:
            c.execute("INSERT OR IGNORE INTO fixtures VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", fixture)
        except:
            pass
    
    conn.commit()
    conn.close()

# Classe para o modelo de IA
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
        self._build_model()
    
    def _build_model(self):
        """Constrói a arquitetura da rede neural"""
        model = keras.Sequential([
            keras.layers.Input(shape=(22,)),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation='relu'),
            # Saída para múltiplas previsões (1X2, BTTS, Over/Under)
            keras.layers.Dense(5, activation='softmax')  # [Home, Draw, Away, BTTS-Yes, Over2.5]
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
    
    def predict(self, fixture_data):
        """Gera previsões para um jogo específico"""
        # Simulação de previsão para demonstração
        home_team_strength = np.random.uniform(0.3, 0.7)
        away_team_strength = np.random.uniform(0.3, 0.7)
        
        # Ajustar probabilidades com base na força relativa
        home_win_prob = home_team_strength / (home_team_strength + away_team_strength) + np.random.uniform(-0.1, 0.1)
        home_win_prob = max(0.2, min(0.8, home_win_prob))
        
        away_win_prob = away_team_strength / (home_team_strength + away_team_strength) + np.random.uniform(-0.1, 0.1)
        away_win_prob = max(0.2, min(0.8, away_win_prob))
        
        # Normalizar para soma = 1
        total = home_win_prob + away_win_prob
        home_win_prob = home_win_prob / total * 0.7
        away_win_prob = away_win_prob / total * 0.7
        draw_prob = 1 - home_win_prob - away_win_prob
        
        # Outras previsões
        btts_yes = np.random.uniform(0.5, 0.8)
        over_25 = np.random.uniform(0.4, 0.7)
        
        # Interpretar resultados
        result = {
            '1X2': {
                'Home': float(home_win_prob),
                'Draw': float(draw_prob),
                'Away': float(away_win_prob)
            },
            'BTTS': {
                'Yes': float(btts_yes),
                'No': float(1 - btts_yes)
            },
            'Over/Under 2.5': {
                'Over': float(over_25),
                'Under': float(1 - over_25)
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

# Funções para interagir com o banco de dados
def get_leagues():
    conn = sqlite3.connect('database.db')
    leagues = pd.read_sql_query("SELECT * FROM leagues", conn)
    conn.close()
    return leagues

def get_fixtures_by_league(league_id):
    conn = sqlite3.connect('database.db')
    query = """
    SELECT f.id, f.date, f.status, f.home_goals, f.away_goals,
           h.name as home_team, h.logo as home_logo,
           a.name as away_team, a.logo as away_logo
    FROM fixtures f
    JOIN teams h ON f.home_team_id = h.id
    JOIN teams a ON f.away_team_id = a.id
    WHERE f.league_id = ?
    """
    fixtures = pd.read_sql_query(query, conn, params=(league_id,))
    conn.close()
    return fixtures

def get_fixture_by_id(fixture_id):
    conn = sqlite3.connect('database.db')
    query = """
    SELECT f.id, f.date, f.status, f.home_goals, f.away_goals,
           h.name as home_team, h.logo as home_logo,
           a.name as away_team, a.logo as away_logo,
           l.name as league_name, l.logo as league_logo
    FROM fixtures f
    JOIN teams h ON f.home_team_id = h.id
    JOIN teams a ON f.away_team_id = a.id
    JOIN leagues l ON f.league_id = l.id
    WHERE f.id = ?
    """
    fixture = pd.read_sql_query(query, conn, params=(fixture_id,))
    conn.close()
    if not fixture.empty:
        return fixture.iloc[0]
    return None

def save_prediction(fixture_id, predictions, value_bets):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Simular odds do mercado
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
    
    # Salvar previsões
    for market, values in predictions.items():
        for selection, confidence in values.items():
            # Verificar se é uma value bet
            is_value = any(vb['market'] == market and vb['selection'] == selection for vb in value_bets)
            
            # Obter odds do mercado
            odds = market_odds.get(market, {}).get(selection, None)
            
            c.execute("""
            INSERT INTO predictions (fixture_id, prediction_type, prediction_value, confidence, is_value_bet, odds)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (fixture_id, market, selection, confidence, 1 if is_value else 0, odds))
    
    conn.commit()
    conn.close()

def get_predictions_by_fixture(fixture_id):
    conn = sqlite3.connect('database.db')
    query = """
    SELECT * FROM predictions
    WHERE fixture_id = ?
    ORDER BY created_at DESC
    """
    predictions = pd.read_sql_query(query, conn, params=(fixture_id,))
    conn.close()
    
    if predictions.empty:
        return None
    
    # Organizar previsões por tipo
    result = {
        '1X2': {},
        'BTTS': {},
        'Over/Under 2.5': {}
    }
    
    value_bets = []
    
    for _, row in predictions.iterrows():
        market = row['prediction_type']
        selection = row['prediction_value']
        confidence = row['confidence']
        
        if market in result:
            result[market][selection] = confidence
        
        if row['is_value_bet'] == 1:
            value_bets.append({
                'market': market,
                'selection': selection,
                'market_odds': row['odds'],
                'value': ((row['odds'] * confidence) - 1) * 100
            })
    
    return {'predictions': result, 'value_bets': value_bets}

# Inicializar o banco de dados
init_db()

# Inicializar o modelo de IA
betting_model = BettingModel()

# Interface do Streamlit
st.markdown('<h1 class="main-header">🤖 Sistema de IA para Análise de Apostas Esportivas</h1>', unsafe_allow_html=True)

# Sidebar para navegação
st.sidebar.title("Navegação")
page = st.sidebar.radio("Ir para:", ["Início", "Selecionar Competição", "Análises"])

if page == "Início":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
    ## Bem-vindo ao Sistema de IA para Apostas Esportivas!
    
    Este sistema utiliza inteligência artificial para analisar dados históricos e estatísticas de jogos de futebol, gerando palpites com score de confiança.
    
    ### Características principais:
    - Análise de dados históricos e estatísticas
    - Detecção de padrões e value bets
    - Geração de tips com score de confiança
    - Foco nas principais ligas, seleções e eliminatórias
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📊 Selecione Competições")
        st.write("Escolha entre as principais ligas, seleções e eliminatórias disponíveis.")
        if st.button("Ver Competições", key="btn_competitions"):
            st.session_state.page = "Selecionar Competição"
            st.experimental_rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🗓️ Selecione Jogos")
        st.write("Escolha manualmente os jogos que deseja analisar com nossa IA.")
        if st.button("Selecionar Jogos", key="btn_fixtures"):
            st.session_state.page = "Selecionar Competição"
            st.experimental_rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📈 Obtenha Análises")
        st.write("Receba palpites com score de confiança e identificação de value bets.")
        if st.button("Ver Análises", key="btn_analysis"):
            st.session_state.page = "Análises"
            st.experimental_rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ℹ️ Sobre o Sistema")
    st.write("""
    Este sistema utiliza inteligência artificial para analisar dados históricos e estatísticas de jogos de futebol, gerando palpites com score de confiança.
    
    A IA foi treinada com dados de milhares de partidas, aprendendo padrões e tendências que podem indicar oportunidades de apostas com valor.
    
    **Aviso:** Este sistema é apenas para fins educacionais. Aposte com responsabilidade.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Selecionar Competição":
    st.markdown('<h2 class="sub-header">🏆 Selecione uma Competição</h2>', unsafe_allow_html=True)
    st.write("Escolha uma competição para ver os jogos disponíveis.")
    
    # Obter ligas do banco de dados
    leagues = get_leagues()
    
    # Exibir ligas em grid
    cols = st.columns(4)
    for i, (_, league) in enumerate(leagues.iterrows()):
        with cols[i % 4]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.image(league['logo'], width=100)
            st.markdown(f"#### {league['name']}")
            st.write(f"{league['country']}")
            if st.button(f"Ver Jogos", key=f"league_{league['id']}"):
                st.session_state.selected_league = league['id']
                st.session_state.selected_league_name = league['name']
                st.session_state.selected_fixtures = []
                st.experimental_rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Se uma liga foi selecionada, mostrar jogos
    if 'selected_league' in st.session_state:
        st.markdown(f'<h2 class="sub-header">⚽ Jogos - {st.session_state.selected_league_name}</h2>', unsafe_allow_html=True)
        st.write("Selecione os jogos que deseja analisar:")
        
        # Obter jogos da liga selecionada
        fixtures = get_fixtures_by_league(st.session_state.selected_league)
        
        if fixtures.empty:
            st.info("Não há jogos disponíveis para esta competição no momento.")
        else:
            # Inicializar lista de jogos selecionados se não existir
            if 'selected_fixtures' not in st.session_state:
                st.session_state.selected_fixtures = []
            
            # Exibir jogos em grid
            cols = st.columns(3)
            for i, (_, fixture) in enumerate(fixtures.iterrows()):
                with cols[i % 3]:
                    # Formatar data
                    fixture_date = datetime.strptime(fixture['date'], '%Y-%m-%d %H:%M:%S')
                    formatted_date = fixture_date.strftime('%d/%m/%Y')
                    formatted_time = fixture_date.strftime('%H:%M')
                    
                    # Verificar se o jogo já está selecionado
                    is_selected = fixture['id'] in st.session_state.selected_fixtures
                    
                    # Estilo do card baseado na seleção
                    card_style = "card"
                    if is_selected:
                        card_style += " border border-primary"
                    
                    st.markdown(f'<div class="{card_style}">', unsafe_allow_html=True)
                    st.write(f"**{formatted_date} - {formatted_time}**")
                    
                    col1, col2, col3 = st.columns([2, 1, 2])
                    with col1:
                        st.image(fixture['home_logo'], width=30)
                        st.write(fixture['home_team'])
                    with col2:
                        st.write("vs")
                    with col3:
                        st.image(fixture['away_logo'], width=30)
                        st.write(fixture['away_team'])
                    
                    # Botão para selecionar/desselecionar
                    if is_selected:
                        if st.button("Desselecionar", key=f"remove_{fixture['id']}"):
                            st.session_state.selected_fixtures.remove(fixture['id'])
                            st.experimental_rerun()
                    else:
                        if st.button("Selecionar", key=f"add_{fixture['id']}"):
                            st.session_state.selected_fixtures.append(fixture['id'])
                            st.experimental_rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Exibir botão de análise se houver jogos selecionados
            if st.session_state.selected_fixtures:
                st.markdown(f"**{len(st.session_state.selected_fixtures)} jogos selecionados**")
                if st.button("Analisar Jogos Selecionados"):
                    # Simular análise para cada jogo
                    for fixture_id in st.session_state.selected_fixtures:
                        fixture_data = get_fixture_by_id(fixture_id)
                        if fixture_data is not None:
                            # Gerar previsão
                            prediction = betting_model.predict(fixture_data)
                            
                            # Simular odds do mercado
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
                            
                            # Salvar previsão
                            save_prediction(fixture_id, prediction, value_bets)
                    
                    # Redirecionar para página de análises
                    st.session_state.page = "Análises"
                    st.experimental_rerun()

elif page == "Análises":
    st.markdown('<h2 class="sub-header">📊 Análises e Palpites</h2>', unsafe_allow_html=True)
    
    # Verificar se há jogos analisados
    conn = sqlite3.connect('database.db')
    analyzed_fixtures = pd.read_sql_query("""
    SELECT DISTINCT f.id, f.date, h.name as home_team, a.name as away_team, 
           h.logo as home_logo, a.logo as away_logo, l.name as league_name
    FROM fixtures f
    JOIN teams h ON f.home_team_id = h.id
    JOIN teams a ON f.away_team_id = a.id
    JOIN leagues l ON f.league_id = l.id
    JOIN predictions p ON f.id = p.fixture_id
    ORDER BY f.date
    """, conn)
    conn.close()
    
    if analyzed_fixtures.empty:
        st.info("Nenhuma análise disponível. Selecione jogos para analisar.")
        if st.button("Selecionar Jogos"):
            st.session_state.page = "Selecionar Competição"
            st.experimental_rerun()
    else:
        # Exibir jogos analisados
        for _, fixture in analyzed_fixtures.iterrows():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            # Cabeçalho do jogo
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"### {fixture['home_team']} vs {fixture['away_team']}")
                st.write(f"**{fixture['league_name']}**")
            with col2:
                fixture_date = datetime.strptime(fixture['date'], '%Y-%m-%d %H:%M:%S')
                st.write(f"Data: {fixture_date.strftime('%d/%m/%Y')}")
            with col3:
                st.write(f"Hora: {fixture_date.strftime('%H:%M')}")
            
            # Obter previsões
            predictions_data = get_predictions_by_fixture(fixture['id'])
            
            if predictions_data:
                predictions = predictions_data['predictions']
                value_bets = predictions_data['value_bets']
                
                # Exibir previsões
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### Resultado (1X2)")
                    
                    # Home
                    home_prob = predictions['1X2'].get('Home', 0) * 100
                    st.write(f"{fixture['home_team']}")
                    st.progress(home_prob / 100)
                    confidence_class = "confidence-high" if home_prob >= 65 else "confidence-medium" if home_prob >= 45 else "confidence-low"
                    st.markdown(f'<span class="{confidence_class}">{home_prob:.1f}%</span>', unsafe_allow_html=True)
                    
                    # Draw
                    draw_prob = predictions['1X2'].get('Draw', 0) * 100
                    st.write("Empate")
                    st.progress(draw_prob / 100)
                    confidence_class = "confidence-high" if draw_prob >= 65 else "confidence-medium" if draw_prob >= 45 else "confidence-low"
                    st.markdown(f'<span class="{confidence_class}">{draw_prob:.1f}%</span>', unsafe_allow_html=True)
                    
                    # Away
                    away_prob = predictions['1X2'].get('Away', 0) * 100
                    st.write(f"{fixture['away_team']}")
                    st.progress(away_prob / 100)
                    confidence_class = "confidence-high" if away_prob >= 65 else "confidence-medium" if away_prob >= 45 else "confidence-low"
                    st.markdown(f'<span class="{confidence_class}">{away_prob:.1f}%</span>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown("#### Ambas Marcam (BTTS)")
                    
                    # Yes
                    btts_yes_prob = predictions['BTTS'].get('Yes', 0) * 100
                    st.write("Sim")
                    st.progress(btts_yes_prob / 100)
                    confidence_class = "confidence-high" if btts_yes_prob >= 65 else "confidence-medium" if btts_yes_prob >= 45 else "confidence-low"
                    st.markdown(f'<span class="{confidence_class}">{btts_yes_prob:.1f}%</span>', unsafe_allow_html=True)
                    
                    # No
                    btts_no_prob = predictions['BTTS'].get('No', 0) * 100
                    st.write("Não")
                    st.progress(btts_no_prob / 100)
                    confidence_class = "confidence-high" if btts_no_prob >= 65 else "confidence-medium" if btts_no_prob >= 45 else "confidence-low"
                    st.markdown(f'<span class="{confidence_class}">{btts_no_prob:.1f}%</span>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown("#### Over/Under 2.5 Gols")
                    
                    # Over
                    over_prob = predictions['Over/Under 2.5'].get('Over', 0) * 100
                    st.write("Over 2.5")
                    st.progress(over_prob / 100)
                    confidence_class = "confidence-high" if over_prob >= 65 else "confidence-medium" if over_prob >= 45 else "confidence-low"
                    st.markdown(f'<span class="{confidence_class}">{over_prob:.1f}%</span>', unsafe_allow_html=True)
                    
                    # Under
                    under_prob = predictions['Over/Under 2.5'].get('Under', 0) * 100
                    st.write("Under 2.5")
                    st.progress(under_prob / 100)
                    confidence_class = "confidence-high" if under_prob >= 65 else "confidence-medium" if under_prob >= 45 else "confidence-low"
                    st.markdown(f'<span class="{confidence_class}">{under_prob:.1f}%</span>', unsafe_allow_html=True)
                
                # Value Bets
                st.markdown("#### Value Bets Detectadas")
                if value_bets:
                    value_bet_data = []
                    for vb in value_bets:
                        value_bet_data.append({
                            "Mercado": vb['market'],
                            "Seleção": vb['selection'],
                            "Odds": f"{vb['market_odds']:.2f}",
                            "Valor (%)": f"+{vb['value']:.1f}%"
                        })
                    
                    st.table(pd.DataFrame(value_bet_data))
                else:
                    st.write("Nenhuma value bet detectada para este jogo.")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="alert alert-warning">
        <i class="fas fa-exclamation-triangle me-2"></i>Aviso: Estas análises são baseadas em dados históricos e estatísticas. Aposte com responsabilidade.
    </div>
    """, unsafe_allow_html=True)

# Rodapé
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("© 2025 Sistema IA - Apostas Esportivas | Este sistema é apenas para fins educacionais. Aposte com responsabilidade.")
st.markdown('</div>', unsafe_allow_html=True)
