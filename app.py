#!/usr/bin/env python3
"""
JIM AI - Local Forensic Chat Interface
Flask web app for chatting with Bedrock Knowledge Base
"""

from flask import Flask, render_template, request, jsonify, session
import boto3
import json
import time
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'jim-ai-forensic-app-secret-key'

# Configuration
KB_ID = "HFCMSKWHFU"
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
REGION = "us-east-1"

# Initialize Bedrock client
bedrock_client = boto3.client('bedrock-agent-runtime', region_name=REGION)

class ChatHistory:
    def __init__(self):
        self.messages = []

    def add_message(self, role, content, sources=None):
        self.messages.append({
            'role': role,
            'content': content,
            'sources': sources or [],
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

    def get_messages(self):
        return self.messages

# Global chat history
chat_history = ChatHistory()

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Empty message'}), 400

        # Add user message to history
        chat_history.add_message('user', user_message)

        # Add typing delay to prevent rate limiting
        time.sleep(1)

        # Query Bedrock Knowledge Base
        response = bedrock_client.retrieve_and_generate(
            input={'text': user_message},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': KB_ID,
                    'modelArn': MODEL_ARN
                }
            }
        )

        # Extract answer and sources
        answer = response['output']['text']
        citations = response.get('citations', [])

        # Format sources
        sources = []
        for citation in citations:
            for ref in citation.get('retrievedReferences', []):
                location = ref.get('location', {}).get('s3Location', {})
                uri = location.get('uri', 'Unknown')
                # Extract filename from S3 URI
                filename = uri.split('/')[-1] if '/' in uri else uri
                sources.append({
                    'filename': filename,
                    'uri': uri
                })

        # Add assistant response to history
        chat_history.add_message('assistant', answer, sources)

        return jsonify({
            'answer': answer,
            'sources': sources,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        chat_history.add_message('assistant', error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/api/history')
def get_history():
    """Get chat history"""
    return jsonify(chat_history.get_messages())

@app.route('/api/clear')
def clear_history():
    """Clear chat history"""
    global chat_history
    chat_history = ChatHistory()
    return jsonify({'status': 'cleared'})

@app.route('/api/status')
def status():
    """Get system status"""
    return jsonify({
        'knowledge_base_id': KB_ID,
        'model': MODEL_ARN.split('/')[-1],
        'region': REGION,
        'status': 'online'
    })

if __name__ == '__main__':
    print("🚀 Starting JIM AI Forensic Chat Interface...")
    print(f"📊 Knowledge Base: {KB_ID}")
    print(f"🤖 Model: {MODEL_ARN.split('/')[-1]}")
    print(f"🌍 Region: {REGION}")
    print("💻 Open your browser to: http://localhost:8080")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=8080)