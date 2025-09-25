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
    response.headers['Content-Security-Policy'] = "default-src 'self'"
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
    # Capture log output
    log_output = StringIO()
    logging.basicConfig(stream=log_output, level=logging.DEBUG)

    try:
        # Create WSGI environment from the event
        env = {
            'REQUEST_METHOD': event.get('httpMethod', ''),
            'SCRIPT_NAME': '',
            'PATH_INFO': event.get('path', ''),
            'QUERY_STRING': urlencode(event.get('queryStringParameters', {})),
            'SERVER_NAME': 'vercel',
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': StringIO(''),
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }

        # Add headers
        headers = event.get('headers', {})
        for key, value in headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                key = f'HTTP_{key}'
            env[key] = value

        # Response container
        response = {}
        headers = []

        def start_response(status, response_headers, exc_info=None):
            response['statusCode'] = int(status.split()[0])
            headers.extend(response_headers)

        # Get response from Flask app
        resp = app(env, start_response)
        response['body'] = b''.join(resp).decode('utf-8')
        
        # Format headers for Lambda response
        response['headers'] = dict(headers)

        return response

    except Exception as e:
        logging.exception('Error processing request')
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': {'Content-Type': 'text/plain'},
        }