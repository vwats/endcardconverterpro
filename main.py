
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Optimize for production
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    if os.environ.get('PRODUCTION'):
        app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME', 'endcardconverter.com')
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_DOMAIN'] = os.environ.get('SERVER_NAME')
    app.run(host='0.0.0.0', port=5000)
