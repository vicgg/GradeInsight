from app import app
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug import secure_filename
import time
import json
import app.cos as cos
import app.data as data

import ibm_boto3
from ibm_botocore.client import Config

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = set(['csv'])#set(['txt', 'png', 'jpg', 'jpeg', 'csv'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER 
app.secret_key = b'ds"5#jq_L3kwe8f-\sfdn\rg]/'
#Connect to IBM Cloud Object Storage
cos.initConnection()
global filenames

@app.route('/')
@app.route('/index')
def home():
    return render_template('index.html')

@app.route('/details')
def data_details():
    dfs_data = data.prepare_data(list_of_dfs)
    return render_template('details.html',dfs_data=dfs_data)
	
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        global filenames
        paths, filenames = [],[]
      # check if the post request has the file part
        if 'file' not in request.files:
            flash('Choose a file')
            return redirect(url_for('home'))
        file = request.files['file']
        for file in request.files.getlist('file'):
    #        print (request.files.getlist('file'))
            if file.filename == '':
                flash('No selected file')
                return redirect(url_for('home'))
            if not allowed_file(file.filename):
                flash('The extension is not valid. Please provide a csv file.')
                return redirect(url_for('home'))
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                paths.append(path)
                filenames.append(filename)
        global list_of_dfs
        list_of_dfs = data.import_csvs(paths,filenames)
        return redirect(url_for('data_details'))

def allowed_file(filename):
    """Does filename have the right extension?"""
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/test')
def test():
    return render_template('details.html')


@app.route('/get_word',methods=['GET', 'POST'])
def get_prediction():
    word = request.args.get('word')
    test_list = {"uno":"1","dos":"2","tres":"3"}
    variable = jsonify(test_list)
    return (variable)

@app.route('/values',methods=['GET', 'POST'])
def get_variable_values():
    var_name = request.args.get('variable')
    var_filename = request.args.get('filename')
    col_values = data.getColumnValues(list_of_dfs,var_filename,var_name)
    variable = json.dumps(col_values.tolist())
    return (variable)

@app.route('/total',methods=['GET', 'POST'])
def get_total_values():
    var_name = request.args.get('variable')
    var_filename = request.args.get('filename')
    total_values = data.getTotalColumnValues(list_of_dfs,var_filename,var_name)
    print(total_values)
    variable = json.dumps(total_values)
    return (variable)

@app.route('/preview',methods=['GET', 'POST'])
def preview_data():
    var_filename = request.args.get('filename')
    response = {        "df_preview":data.getPreviewData(list_of_dfs,var_filename).to_json(orient='records'),
     "column_names":jsonify(data.getColumnNames(list_of_dfs,var_filename))
    }
    print (data.getColumnNames(list_of_dfs,var_filename))
    print (type(response['df_preview']))
    return (response["df_preview"])

@app.route('/prepare',methods=['GET', 'POST'])
def prepare_data():
    target_columns = data.target_data(list_of_dfs)
    variable = json.dumps(target_columns)
    return (variable)

@app.route('/upload_target',methods=['GET', 'POST'])
def upload_data():
    cos.upload_file('target_dataset.csv')
    variable = json.dumps("success")
    return (variable)