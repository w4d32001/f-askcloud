from flask import Flask, request, jsonify
from flask_cors import CORS
from deep_translator import GoogleTranslator, MicrosoftTranslator, MyMemoryTranslator
import logging
from functools import lru_cache

app = Flask(__name__)
CORS(app)  

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1000)
def cached_translation(text, source_lang, target_lang, service='google'):
    try:
        if service == 'google':
            translator = GoogleTranslator(source=source_lang, target=target_lang)
        elif service == 'microsoft':
            translator = MicrosoftTranslator(source=source_lang, target=target_lang)
        elif service == 'mymemory':
            translator = MyMemoryTranslator(source=source_lang, target=target_lang)
        else:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
        
        return translator.translate(text)
    except Exception as e:
        logger.error(f"Error en traducción: {str(e)}")
        return None

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        text = data.get('text', '').strip()
        target_language = data.get('target_language', 'es')
        source_language = data.get('source_language', 'auto')
        service = data.get('service', 'google')  
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        if len(text) > 5000:
            return jsonify({'error': 'Text too long (max 5000 characters)'}), 400
        
        logger.info(f"Translating: '{text[:50]}...' from {source_language} to {target_language}")
        
        translated_text = cached_translation(text, source_language, target_language, service)
        
        if translated_text is None:
            return jsonify({'error': 'Translation failed'}), 500
        
        if translated_text.lower().strip() == text.lower().strip():
            logger.info("Text appears to already be in target language")
        
        response_data = {
            'original_text': text,
            'translated_text': translated_text,
            'source_language': source_language,
            'target_language': target_language,
            'service_used': service,
            'success': True
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error in translate endpoint: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'success': False
        }), 500

@app.route('/detect-language', methods=['POST'])
def detect_language():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        detector = GoogleTranslator(source='auto', target='en')
        result = detector.translate(text)
        
        from deep_translator import single_detection
        detected_lang = single_detection(text, api_key=None) 
        
        return jsonify({
            'text': text,
            'detected_language': detected_lang,
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error in detect-language endpoint: {str(e)}")
        return jsonify({
            'error': 'Language detection failed',
            'message': str(e),
            'success': False
        }), 500

@app.route('/supported-languages', methods=['GET'])
def supported_languages():
    """Endpoint que devuelve los idiomas soportados"""
    try:
        # Idiomas más comunes soportados por Google Translate
        languages = {
            'af': 'Afrikaans',
            'ar': 'Arabic',
            'bg': 'Bulgarian',
            'bn': 'Bengali',
            'ca': 'Catalan',
            'cs': 'Czech',
            'da': 'Danish',
            'de': 'German',
            'el': 'Greek',
            'en': 'English',
            'es': 'Spanish',
            'et': 'Estonian',
            'fa': 'Persian',
            'fi': 'Finnish',
            'fr': 'French',
            'gu': 'Gujarati',
            'he': 'Hebrew',
            'hi': 'Hindi',
            'hr': 'Croatian',
            'hu': 'Hungarian',
            'id': 'Indonesian',
            'it': 'Italian',
            'ja': 'Japanese',
            'kn': 'Kannada',
            'ko': 'Korean',
            'lt': 'Lithuanian',
            'lv': 'Latvian',
            'mk': 'Macedonian',
            'ml': 'Malayalam',
            'mr': 'Marathi',
            'ne': 'Nepali',
            'nl': 'Dutch',
            'no': 'Norwegian',
            'pa': 'Punjabi',
            'pl': 'Polish',
            'pt': 'Portuguese',
            'ro': 'Romanian',
            'ru': 'Russian',
            'sk': 'Slovak',
            'sl': 'Slovenian',
            'so': 'Somali',
            'sq': 'Albanian',
            'sv': 'Swedish',
            'sw': 'Swahili',
            'ta': 'Tamil',
            'te': 'Telugu',
            'th': 'Thai',
            'tl': 'Filipino',
            'tr': 'Turkish',
            'uk': 'Ukrainian',
            'ur': 'Urdu',
            'vi': 'Vietnamese',
            'zh': 'Chinese',
        }
        
        return jsonify({
            'languages': languages,
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error in supported-languages endpoint: {str(e)}")
        return jsonify({
            'error': 'Failed to get supported languages',
            'success': False
        }), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'translation-api',
        'version': '1.0.0'
    }), 200

@app.route('/batch-translate', methods=['POST'])
def batch_translate():
    try:
        data = request.get_json()
        texts = data.get('texts', [])
        target_language = data.get('target_language', 'es')
        source_language = data.get('source_language', 'auto')
        service = data.get('service', 'google')
        
        if not texts or not isinstance(texts, list):
            return jsonify({'error': 'Texts array is required'}), 400
        
        if len(texts) > 100:
            return jsonify({'error': 'Too many texts (max 100)'}), 400
        
        results = []
        
        for i, text in enumerate(texts):
            if not text or not isinstance(text, str):
                results.append({
                    'index': i,
                    'original_text': text,
                    'translated_text': '',
                    'error': 'Invalid text'
                })
                continue
            
            if len(text) > 5000:
                results.append({
                    'index': i,
                    'original_text': text,
                    'translated_text': '',
                    'error': 'Text too long'
                })
                continue
            
            try:
                translated = cached_translation(text.strip(), source_language, target_language, service)
                results.append({
                    'index': i,
                    'original_text': text,
                    'translated_text': translated or '',
                    'error': None if translated else 'Translation failed'
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'original_text': text,
                    'translated_text': '',
                    'error': str(e)
                })
        
        return jsonify({
            'results': results,
            'total_processed': len(results),
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch-translate endpoint: {str(e)}")
        return jsonify({
            'error': 'Batch translation failed',
            'message': str(e),
            'success': False
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)