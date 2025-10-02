from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from urllib.parse import urlencode
from io import StringIO
import logging
import sys
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['ENV'] = 'production'
app.config['TESTING'] = False

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:"
    return response

# Handle proxy headers correctly
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/education')
def education():
    return render_template('education.html')

@app.route('/experience')
def experience():
    return render_template('experience.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

# This is important for Vercel - expose the app
if __name__ == '__main__':
    # Ensure debug mode is disabled in production
    app.run(debug=False, host='0.0.0.0', port=8000)

# For Vercel serverless deployment
def handler(event, context):
    """
    Serverless function handler for Vercel
    """
    try:
        # Create WSGI environment
        path = event.get('path', '')
        headers = event.get('headers', {})
        
        environ = {
            'REQUEST_METHOD': event.get('httpMethod', 'GET'),
            'SCRIPT_NAME': '',
            'PATH_INFO': path,
            'QUERY_STRING': urlencode(event.get('queryStringParameters', {})),
            'SERVER_NAME': headers.get('host', 'localhost'),
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': StringIO(),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }

        # Add headers to environment
        for key, value in headers.items():
            key = 'HTTP_' + key.upper().replace('-', '_')
            if key not in ('HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH'):
                environ[key] = value

        # Handle the request
        response_data = {'statusCode': 500, 'body': '', 'headers': {}}
        
        def start_response(status, response_headers, exc_info=None):
            status_code = int(status.split()[0])
            response_data['statusCode'] = status_code
            response_data['headers'].update(dict(response_headers))
        
        # Get response from Flask app
        response_body = b''.join(app(environ, start_response))
        response_data['body'] = response_body.decode('utf-8')
        
        return response_data

    except Exception as e:
        logging.exception("Error processing request")
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': {'Content-Type': 'text/plain'}
        }