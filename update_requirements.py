requirements = [
    "Flask==3.1.0",
    "Flask-SQLAlchemy==3.1.1",
    "SQLAlchemy==2.0.40",
    "requests==2.31.0",
    "numpy==1.26.4",
    "pandas==2.2.1",
    "tensorflow==2.15.0",
    "scikit-learn==1.4.0",
    "gunicorn==21.2.0"
]

with open('requirements.txt', 'w') as f:
    for req in requirements:
        f.write(req + '\n')
