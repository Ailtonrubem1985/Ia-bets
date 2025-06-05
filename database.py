from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    """Inicializa o banco de dados SQLite"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, '..', '..', 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    # Cria todas as tabelas se não existirem
    with app.app_context():
        db.create_all()
