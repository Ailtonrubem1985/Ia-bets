import os
from flask import Flask, send_from_directory
from src.models.database import init_db
from src.routes.api import api_bp
from src.routes.ai import ai_bp

def create_app():
    app = Flask(__name__, static_folder='static')
    
    # Configuração do banco de dados SQLite
    init_db(app)
    
    # Registrar blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    
    # Rota para servir arquivos estáticos
    @app.route('/static/<path:path>')
    def serve_static(path):
        return send_from_directory('static', path)
    
    # Rota principal para o frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        return send_from_directory('static', 'index.html')
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
