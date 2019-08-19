from flask import Flask, render_template, request, json, jsonify
import os
import json
import numpy as np
import io
from PIL import Image

from base64 import b64encode, b64decode
import requests
from math import pi
from watson_machine_learning_client import WatsonMachineLearningAPIClient

app = Flask(__name__)
app.config.from_object(__name__)
port = int(os.getenv('PORT', 8080))

@app.route("/", methods=['GET'])
def hello():
    error=None
    return render_template('index.html', error=error)

@app.route("/iot", methods=['GET'])
def result():
    print(request)

    api_key = 'a-y76ylb-ckj29x2v6b'
    token = 'IoZc5eC_lxrtJdmi4O'
    device_type = 'maratona'
    device_id = 'd9'
    event_id = 'sensor'

    org_id = api_key.split('-')[1]

    credentials = api_key + ':' + token
    auth = b64encode(credentials.encode()).decode('ascii')

    url = 'https://' + org_id + '.internetofthings.ibmcloud.com/api/v0002/device/types/' + device_type + '/devices/' + device_id + '/events/' + event_id
    response = requests.get(url, headers = {
        'Authorization': 'Basic ' + auth
    })
    payload = json.loads(b64decode(response.json()['payload']).decode('ascii'))

    data = payload['data']
    temperatura_celsius = data['temperatura']
    umidade_ar = data['umidade_ar']
    umidade_solo = data['umidade_solo']

    temperatura_fahrenheit = temperatura_celsius * 1.8 + 32
    itu = temperatura_celsius - 0.55 * (1 - umidade_ar) * (temperatura_celsius - 14)
    volume_agua = umidade_solo * (4 / 3 * pi / 2)

    resposta = {
        "iotData": data,
        "itu": itu,
        "volumeAgua": volume_agua
        "fahrenheit": temperatura_fahrenheit
    }
    response = app.response_class(
        response=json.dumps(resposta),
        status=200,
        mimetype='application/json'
    )
    return response

def prepare_image(image):
    image = image.resize(size=(96,96))
    image = np.array(image, dtype="float") / 255.0
    image = np.expand_dims(image,axis=0)
    image = image.tolist()
    return image

@app.route('/predict', methods=['POST'])
def predict():
    print(request)
    image = request.files["image"].read()
    image = Image.open(io.BytesIO(image))
    image = prepare_image(image)

    classes = ['normal', 'praga']
			
    wml_credentials = {
        'apikey': 'B-H331DpFRKwapGsKOLjOBrnShvRCOQxokLvTbqM2OTq',
        'instance_id': '6d54ebaf-26c9-43a4-b69c-e9b8e30c138a',
        'url': 'https://us-south.ml.cloud.ibm.com'
    }
    client = WatsonMachineLearningAPIClient(wml_credentials)

    url = 'https://us-south.ml.cloud.ibm.com/v3/wml_instances/6d54ebaf-26c9-43a4-b69c-e9b8e30c138a/deployments/c1a44b0a-5106-45d5-bd2b-6c20aca51ab1/online'
    response = client.deployments.score(url, {
        'values': image
    })
	    		    
    resposta = {
        "class": classes[response['values'][0][1]]
    }
    return resposta

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)