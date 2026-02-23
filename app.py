import os
import csv
import io
from flask import Flask, request, jsonify, render_template
import requests
from google import genai
from dotenv import load_dotenv
import re

load_dotenv()

app = Flask(__name__)

def get_ado_work_item(work_item_id, ado_pat, organization="venkathcl2023", project="Minerva"):
    if not ado_pat:
        raise Exception("Azure DevOps PAT is required to connect to the actual work item.")
        
    url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers, auth=('', ado_pat))
    if response.status_code == 200:
        data = response.json()
        fields = data.get('fields', {})
        acceptance_criteria = fields.get('Microsoft.VSTS.Common.AcceptanceCriteria', '')
        if not acceptance_criteria:
            acceptance_criteria = fields.get('System.Description', '')
        
        # simple html stripping
        return re.sub('<[^<]+>', '', acceptance_criteria)
    else:
        raise Exception(f"Failed to fetch ADO work item: {response.status_code} - {response.text}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate_test_cases', methods=['POST'])
def generate_test_cases():
    data = request.json
    work_item_id = data.get('work_item_id')
    ado_pat = data.get('ado_pat')
    gemini_api_key = data.get('gemini_api_key')
    
    if not work_item_id:
        return jsonify({'error': 'work_item_id is required'}), 400
        
    try:
        acceptance_criteria = get_ado_work_item(work_item_id, ado_pat)
        
        if not gemini_api_key:
             raise Exception("Gemini API Key is required to generate test cases.")


        # Create a client using the provided API key
        client = genai.Client(api_key=gemini_api_key)

        prompt = f"""
        Given the following Acceptance Criteria from a user story, generate exactly 5 test cases in Gherkin (Given-When-Then) format.
        
        Acceptance Criteria:
        {acceptance_criteria}
        
        Return ONLY the Gherkin test cases, without any surrounding markdown or explanations. Separate each test case clearly.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        return jsonify({'gherkin': response.text, 'acceptance_criteria': acceptance_criteria})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_test_strategy', methods=['POST'])
def generate_test_strategy():
    data = request.json
    organization = data.get('organization')
    project = data.get('project')
    work_item_id = data.get('work_item_id')
    ado_pat = data.get('ado_pat')
    gemini_api_key = data.get('gemini_api_key')
    
    if not work_item_id or not organization or not project:
        return jsonify({'error': 'organization, project, and work_item_id are required'}), 400
        
    try:
        acceptance_criteria = get_ado_work_item(work_item_id, ado_pat, organization, project)
        
        if not gemini_api_key:
             raise Exception("Gemini API Key is required to generate test strategy.")

        client = genai.Client(api_key=gemini_api_key)

        prompt = f"""
        Given the following Acceptance Criteria from a user story, generate a Detailed Test Plan/Strategy.
        
        Acceptance Criteria:
        {acceptance_criteria}
        
        Return ONLY the Detailed Test Plan/Strategy in a clear, structured markdown format.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        return jsonify({'test_strategy': response.text, 'acceptance_criteria': acceptance_criteria})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_sql', methods=['POST'])
def generate_sql():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        headers = next(csv_input)
        
        # Process headers to be valid SQL column names
        clean_headers = []
        for header in headers:
            clean = re.sub(r'\W+', '_', header).strip('_')
            clean_headers.append(clean if clean else 'column')
            
        table_name = "test_data_table"
        create_table_sql = f"CREATE TABLE {table_name} (\n"
        for i, col_name in enumerate(clean_headers):
            create_table_sql += f"    {col_name} VARCHAR(255)"
            if i < len(clean_headers) - 1:
                create_table_sql += ",\n"
            else:
                create_table_sql += "\n"
        create_table_sql += ");"
        
        cols = ", ".join(clean_headers)
        completeness_sql = f"SELECT {cols} FROM source_table\nEXCEPT\nSELECT {cols} FROM target_table;"
        
        return jsonify({
            'create_table_sql': create_table_sql,
            'completeness_sql': completeness_sql
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
