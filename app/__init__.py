from flask import Flask

def create_app():
    app = Flask(__name__)

    from . import monitoreo

    app.register_blueprint(monitoreo.bp)
    return app

if __name__ == '__main__':
    app = create_app()