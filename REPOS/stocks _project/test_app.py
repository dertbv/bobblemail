#!/usr/bin/env python3
"""
Simple test Flask app to verify basic functionality
"""

from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    """Test main page"""
    return render_template('index.html')

@app.route('/test')
def test():
    """Simple test endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'Flask app is working!',
        'test': True
    })

@app.route('/dashboard')
def dashboard():
    """Test dashboard page"""
    return render_template('dashboard.html')

if __name__ == '__main__':
    print("Starting Test Flask Application...")
    print("Access the application at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)