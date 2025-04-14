
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Optimize for production
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')  # For custom domain
    app.run(host='0.0.0.0', port=5000)
