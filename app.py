from flask import Flask, request, render_template, jsonify, send_from_directory
import google.generativeai as genai
from PIL import Image
import os
import base64
from io import BytesIO
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure upload folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

# Get API key from environment
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY not found in environment variables!")
    print("Please check your .env file")
    exit(1)

# Configure Gemini AI
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name
    print("✅ Gemini AI configured successfully!")
except Exception as e:
    print(f"❌ Error configuring Gemini AI: {e}")
    exit(1)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image_dimensions(image):
    """Process image to extract basic dimensions"""
    width, height = image.size
    aspect_ratio = width / height
    return {
        'width': width,
        'height': height,
        'aspect_ratio': round(aspect_ratio, 2)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_image():
    try:
        print("📸 Received image analysis request")
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded', 'success': False})
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected', 'success': False})
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload an image.', 'success': False})
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        print(f"💾 Image saved: {filepath}")
        
        # Open and process image
        image = Image.open(filepath)
        image_info = process_image_dimensions(image)
        print(f"📏 Image dimensions: {image_info}")
        
        # Enhanced prompt for better floor plan analysis
        prompt = """
        You are an expert architect and floor plan analyzer. Analyze this floor plan image and provide:

        1. **DIMENSIONS ANALYSIS:**
           - Estimate the total floor area in square feet
           - Identify the approximate length and width of the property
           - Calculate room dimensions where visible

        2. **SPACE IDENTIFICATION:**
           - List all identifiable rooms and spaces
           - Estimate the size of each room in square feet
           - Identify doors, windows, and openings

        3. **OPTIMAL LAYOUT RECOMMENDATIONS:**
           - Suggest improvements for space utilization
           - Recommend furniture placement for each room
           - Identify potential traffic flow issues
           - Suggest lighting and ventilation considerations

        4. **MEASUREMENTS & SPECIFICATIONS:**
           - Provide specific measurements in feet and inches
           - Calculate total usable space vs. circulation space
           - Identify any structural elements (walls, columns, etc.)

        5. **DESIGN SUGGESTIONS:**
           - Recommend color schemes for different areas
           - Suggest materials for flooring in different rooms
           - Provide storage solutions for each space

        Please format your response in clear sections with bullet points and specific measurements where possible.
        """
        
        print("🤖 Sending request to Gemini AI...")
        
        # Generate content using Gemini
        response = model.generate_content([prompt, image])
        
        if not response.text:
            return jsonify({
                'error': 'No response from AI model',
                'success': False
            })
        
        print("✅ Received response from Gemini AI")
        
        # Save analysis results
        analysis_data = {
            'timestamp': timestamp,
            'filename': filename,
            'image_info': image_info,
            'analysis': response.text,
            'success': True
        }
        
        # Save analysis to file
        analysis_filename = f"analysis_{timestamp}.json"
        analysis_path = os.path.join(OUTPUT_FOLDER, analysis_filename)
        with open(analysis_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"💾 Analysis saved: {analysis_path}")
        
        return jsonify(analysis_data)
        
    except Exception as e:
        print(f"❌ Error in analyze_image: {str(e)}")
        return jsonify({
            'error': f'Error processing image: {str(e)}',
            'success': False
        })

@app.route('/generate_plan', methods=['POST'])
def generate_plan():
    try:
        print("🏗️ Received plan generation request")
        
        data = request.get_json()
        requirements = data.get('requirements', '')
        
        if not requirements:
            return jsonify({'error': 'No requirements provided', 'success': False})
        
        # Enhanced prompt for plan generation
        plan_prompt = f"""
        Based on these requirements: "{requirements}"
        
        Generate a detailed floor plan with:
        1. Room layout and dimensions
        2. Door and window placements
        3. Furniture arrangement suggestions
        4. Traffic flow optimization
        5. Lighting and electrical recommendations
        6. Plumbing considerations
        7. Storage solutions
        
        Provide specific measurements and practical implementation details.
        """
        
        print("🤖 Sending plan generation request to Gemini AI...")
        
        model_text = genai.GenerativeModel('gemini-1.5-flash')
        response = model_text.generate_content(plan_prompt)
        
        if not response.text:
            return jsonify({
                'error': 'No response from AI model',
                'success': False
            })
        
        print("✅ Received plan generation response")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_data = {
            'timestamp': timestamp,
            'requirements': requirements,
            'generated_plan': response.text,
            'success': True
        }
        
        # Save generated plan
        plan_filename = f"plan_{timestamp}.json"
        plan_path = os.path.join(OUTPUT_FOLDER, plan_filename)
        with open(plan_path, 'w') as f:
            json.dump(plan_data, f, indent=2)
        
        print(f"💾 Plan saved: {plan_path}")
        
        return jsonify(plan_data)
        
    except Exception as e:
        print(f"❌ Error in generate_plan: {str(e)}")
        return jsonify({
            'error': f'Error generating plan: {str(e)}',
            'success': False
        })

@app.route('/test_api')
def test_api():
    """Test endpoint to verify Gemini API connection"""
    try:
        model_test = genai.GenerativeModel('gemini-1.5-flash')
        response = model_test.generate_content("Say 'Hello, Gemini API is working!'")
        
        return jsonify({
            'success': True,
            'message': 'API connection successful',
            'response': response.text,
            'api_key_configured': bool(GEMINI_API_KEY)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'api_key_configured': bool(GEMINI_API_KEY)
        })

@app.route('/history')
def get_history():
    try:
        files = []
        if os.path.exists(OUTPUT_FOLDER):
            for filename in os.listdir(OUTPUT_FOLDER):
                if filename.endswith('.json'):
                    filepath = os.path.join(OUTPUT_FOLDER, filename)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            files.append({
                                'filename': filename,
                                'timestamp': data.get('timestamp', ''),
                                'type': 'analysis' if 'analysis' in data else 'plan'
                            })
                    except:
                        continue
        
        # Sort by timestamp (newest first)
        files.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify({'files': files, 'success': True})
        
    except Exception as e:
        return jsonify({
            'error': f'Error fetching history: {str(e)}',
            'success': False
        })

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(OUTPUT_FOLDER, filename)
    except Exception as e:
        return jsonify({
            'error': f'File not found: {str(e)}',
            'success': False
        })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'gemini_configured': bool(GEMINI_API_KEY),
        'api_key_length': len(GEMINI_API_KEY) if GEMINI_API_KEY else 0
    })

# Error handlers
@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'error': 'File too large. Maximum size is 16MB.',
        'success': False
    }), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Endpoint not found',
        'success': False
    }), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'error': 'Internal server error',
        'success': False
    }), 500

if __name__ == '__main__':
    # Check configuration
    print("🚀 Starting Floor Plan Generator...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Output folder: {OUTPUT_FOLDER}")
    print(f"🔑 API Key configured: {'✅' if GEMINI_API_KEY else '❌'}")
    
    if GEMINI_API_KEY:
        print(f"🔑 API Key length: {len(GEMINI_API_KEY)} characters")
    
    # Test API connection on startup
    try:
        test_model = genai.GenerativeModel('gemini-1.5-flash')
        test_response = test_model.generate_content("Test connection")
        print("✅ Gemini API connection test successful!")
    except Exception as e:
        print(f"❌ Gemini API connection test failed: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
