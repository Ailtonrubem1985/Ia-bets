from flask import Blueprint, render_template
import os

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def index():
    """Página inicial do sistema"""
    return send_from_directory('static', 'index.html')

@frontend_bp.route('/<path:path>')
def catch_all(path):
    """Rota para capturar todas as outras requisições e redirecionar para o frontend"""
    return send_from_directory('static', 'index.html')
