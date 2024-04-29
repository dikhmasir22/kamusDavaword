from flask import Flask, request, render_template, jsonify, redirect, url_for
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get('MONGODB_URI')
DB_NAME = os.environ.get('DB_NAME')


app = Flask(__name__)

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]


@app.route('/')
def main():
    words_result = db.kata.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definitions': definition,
        })
        msg = request.args.get('msg')
    return render_template('index.html', kata = words,msg=msg)

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = 'ae587410-358f-4335-8e23-4f0c00fc4d4a'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definisi = response.json()

    if not definisi:
        return redirect(url_for(
            'error',
            msg= keyword
        ))

    if type(definisi[0]) is str:
        definisi_array = ', '.join(definisi)
        return redirect(url_for(
            'error',
            msg=keyword,
            definisi = definisi_array
        ))

    status = request.args.get('status_give', 'new')
    return render_template(
        'detail.html', 
        word=keyword,
        definisi = definisi,
        status = status
        )

@app.route('/api/save_word', methods = ['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    tanggal = datetime.now().strftime('%Y-%m-%d')

    doc = {
        'word' : word,
        'definitions' : definitions,
        'date' : tanggal
    }

    db.kata.insert_one(doc)

    return jsonify({
        'result' : 'success',
        'msg' : f'kata "{word}", telah tersimpan!',
    })

@app.route('/api/delete_word', methods = ['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.kata.delete_one({'word' : word})
    db.example.delete_many({'word' : word})
    return jsonify({
        'result': 'success',
        'msg' : f'Kata, {word}, telah Terhapus!'
        })

@app.route('/error')
def error():

    msg = request.args.get('msg')

    if request.args.get('definisi'):
        definisi = request.args.get('definisi')
        definisi = definisi.split(', ')
        return render_template('error.html', msg = msg, definisi = definisi)
    else:
        return render_template('error.html', msg = msg)

@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = db.example.find({'word' : word})
    examples = []
    for example in example_data:
        examples.append({
            'example': example.get('example'),
            'id': str(example.get('_id')),
        })
    return jsonify({
        'result': 'success',
        'examples' : examples
        })

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word' : word,
        'example' : example
    }
    db.example.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg' : f'example, {example}, untuk kata, {word}, sudah tersimpan!'
    })


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.example.delete_one({'_id': ObjectId(id)})
    return jsonify({
        'result': 'success',
        'msg' : f'Contoh kalimat untuk, {word}, telah Terhapus!'
        })

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)