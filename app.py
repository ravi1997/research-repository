from flask import Flask, request, jsonify
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
