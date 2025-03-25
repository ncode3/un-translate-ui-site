import azure.functions as func
import logging
import requests
import json
import os

# Create a FunctionApp instance (Python v2 model)
app = func.FunctionApp()

@app.function_name("translate")
@app.route(route="translate", auth_level=func.AuthLevel.FUNCTION)
def translate_text(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Parse JSON POST body
    try:
        req_body = req.get_json()
        text = req_body.get('text')
        source_language = req_body.get('sourceLanguage', '')
        target_language = req_body.get('targetLanguage', 'en')
        use_strict_mode = req_body.get('useStrictMode', False)
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid request body"}),
            status_code=400,
            mimetype="application/json"
        )

    # Validate input
    if not text:
        return func.HttpResponse(
            json.dumps({"error": "Please provide text to translate"}),
            status_code=400,
            mimetype="application/json"
        )

    # Get environment variables - Changed to lowercase to match Azure settings
    translator_key = os.environ.get('TRANSLATOR_KEY')
    translator_endpoint = os.environ.get('TRANSLATOR_ENDPOINT')
    logging.info(f"Using endpoint: {translator_endpoint}")

    if not translator_key or not translator_endpoint:
        return func.HttpResponse(
            json.dumps({"error": "Translator configuration missing"}),
            status_code=500,
            mimetype="application/json"
        )

    # Construct Translator API call
    translate_url = f"{translator_endpoint}translate"
    params = {
        'api-version': '3.0',
        'to': target_language
    }
    if source_language:
        params['from'] = source_language

    headers = {
    'Ocp-Apim-Subscription-Key': translator_key,
    'Ocp-Apim-Subscription-Region': 'eastus',  # Add this line
    'Content-type': 'application/json'
}

    body = [{'text': text}]

    try:
        logging.info(f"Calling translator API with params: {params}")
        response = requests.post(translate_url, params=params, headers=headers, json=body)
        logging.info(f"Response status code: {response.status_code}")
        logging.info(f"Response content: {response.text}")

        response.raise_for_status()
        translation_result = response.json()

        # Extract the translated text from the JSON response
        translated_text = translation_result[0]['translations'][0]['text']

        # Apply optional UN terminology enforcement
        if use_strict_mode:
            terminology_dict = {
                'Palestine': 'occupied Palestinian territory',
                'فلسطين': 'occupied Palestinian territory',
                'Secretary-General': 'Secretary-General of the United Nations',
                'SG': 'Secretary-General of the United Nations'
            }
            for term, replacement in terminology_dict.items():
                translated_text = translated_text.replace(term, replacement)

        return func.HttpResponse(
            json.dumps({
                "originalText": text,
                "translatedText": translated_text,
                "targetLanguage": target_language,
                "strictModeApplied": use_strict_mode
            }),
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Translation failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )