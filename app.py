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
    defaults = {
        'ado_pat': os.environ.get('ADO_PAT', ''),
        'ado_org': os.environ.get('ADO_ORG', ''),
        'ado_project': os.environ.get('ADO_PROJECT', ''),
        'gemini_api_key': os.environ.get('GEMINI_API_KEY', '')
    }
    return render_template('index.html', defaults=defaults)

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

@app.route('/api/generate_java_from_gherkin', methods=['POST'])
def generate_java_from_gherkin():
    data = request.json
    gherkin_code = data.get('gherkin_code')
    gemini_api_key = data.get('gemini_api_key')
    
    if not gherkin_code:
        return jsonify({'error': 'gherkin_code is required'}), 400
        
    try:
        if not gemini_api_key:
             raise Exception("Gemini API Key is required.")

        client = genai.Client(api_key=gemini_api_key)

        prompt = f"""
        Given the following Gherkin scenarios, generate a complete and well-structured Java class implementing these scenarios (e.g., using Cucumber annotations, or just standard Java unit test methods).
        
        Gherkin:
        {gherkin_code}
        
        Return exactly ONLY the valid Java code snippet. No markdown blocks, no HTML, no explanation, just the raw Java source code.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        text = response.text.replace('```java', '').replace('```', '').strip()
        
        return jsonify({'java': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert_code', methods=['POST'])
def convert_code():
    data = request.json
    java_code = data.get('java_code')
    gemini_api_key = data.get('gemini_api_key')
    
    if not java_code:
        return jsonify({'error': 'java_code is required'}), 400
        
    try:
        if not gemini_api_key:
             raise Exception("Gemini API Key is required to convert code.")

        client = genai.Client(api_key=gemini_api_key)

        prompt = f"""
        Given the following Java code, convert it into both Python and C#.
        
        Java Code:
        {java_code}
        
        Please return a strictly valid JSON object with exactly two keys: "python" (containing the Python code string) and "csharp" (containing the C# code string). Do not include any other text or markdown formatting.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        import json
        text = response.text.replace('```json', '').replace('```', '').strip()
        result_json = json.loads(text)
        
        return jsonify(result_json)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attach_test_cases', methods=['POST'])
def attach_test_cases():
    organization = request.form.get('organization')
    project = request.form.get('project')
    work_item_id = request.form.get('work_item_id')
    ado_pat = request.form.get('ado_pat')
    
    if not all([organization, project, work_item_id, ado_pat]):
        return jsonify({'error': 'organization, project, work_item_id, and ado_pat are required'}), 400
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    created_test_cases = []
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        headers = {
            'Content-Type': 'application/json-patch+json'
        }
        
        for row in csv_input:
            title = row.get('Title', 'Untitled Test Case')
            steps = row.get('Steps', '')
            expected = row.get('Expected Result', '')
            tags = row.get('Tags', '')
            
            # Simple description formatting for the test case
            description = f"<b>Steps:</b><br>{steps}<br><br><b>Expected Result:</b><br>{expected}"
            
            # Create Test Case payload
            payload = [
                {"op": "add", "path": "/fields/System.Title", "value": title},
                {"op": "add", "path": "/fields/System.Description", "value": description},
                {"op": "add", "path": "/relations/-", "value": {
                    "rel": "Microsoft.VSTS.Common.TestedBy-Reverse",
                    "url": f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{work_item_id}",
                    "attributes": {"comment": "Attached by Agent"}
                }}
            ]
            
            if tags:
                payload.append({"op": "add", "path": "/fields/System.Tags", "value": tags})
            
            url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/$Test Case?api-version=7.1"
            res = requests.post(url, headers=headers, json=payload, auth=('', ado_pat))
            
            if res.status_code in [200, 201]:
                tc_data = res.json()
                created_test_cases.append({'id': tc_data['id'], 'title': title, 'status': 'Success'})
            else:
                try:
                    error_msg = res.json().get('message', res.text)
                except:
                    error_msg = res.text
                created_test_cases.append({'title': title, 'status': f'Failed: {error_msg}'})
                
        return jsonify({
            'message': 'Processed test cases',
            'results': created_test_cases
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
