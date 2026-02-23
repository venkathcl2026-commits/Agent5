# AI ETL Testing Agent Architecture

## Overview
The AI ETL Testing Agent is a Flask-based web application designed to automate testing workflows. Its primary features include generating Gherkin test cases from Azure DevOps (ADO) Work Items, generating Detailed Test Strategies based on ADO Acceptance Criteria, and automatically creating SQL queries for Data Completeness testing using uploaded CSV files.

## Technology Stack
- **Frontend**: HTML5, Vanilla JavaScript, CSS3
- **Backend**: Python 3.x, Flask (RESTful API endpoints)
- **External Integrations**:
  - Azure DevOps (ADO) REST API for fetching work item Acceptance Criteria
  - Google Gemini API (gemini-2.5-flash) for generative AI tasks (Test Cases & Test Strategies)

## Application Structure

### Frontend (`templates/index.html`, `static/main.js`, `static/style.css`)
- **Single Page Application (SPA) feel:** Uses a tabbed interface.
- **Tabs**:
  1. **Test Strategy Generator**: Prompts for ADO Organization, Project, Work Item ID, ADO PAT, and Gemini API key. Calls the `/api/generate_test_strategy` backend endpoint and renders the Detailed Test Plan structure.
  2. **TestCaseGenerator**: Prompts for Work Item ID, ADO PAT, and Gemini API key. Calls the `/api/generate_test_cases` backend endpoint and renders the resulting Gherkin test cases.
  3. **DataCompleteness SQL Creation**: Provides a drag-and-drop CSV file upload interface. Calls `/api/generate_sql` endpoint to parse headers and generate table creation/completeness validation SQL scripts.

### Backend (`app.py`)
- **Web Server Configuration:** Flask app running locally on port 5000 setting up routes.
- **REST Endpoints**:
  - `GET /`: Renders the main frontend (`index.html`).
  - `POST /api/generate_test_strategy`:
    - Validates presence of `organization`, `project`, `work_item_id`, `ado_pat`, and `gemini_api_key`.
    - Invokes `get_ado_work_item(id, pat, org, proj)` to fetch ADO data.
    - Connects to Google Gemini Client.
    - Prompts Gemini to generate a Detailed Test Strategy/Plan based on retrieved Acceptance Criteria.
    - Returns JSON response with `test_strategy` and `acceptance_criteria`.
  - `POST /api/generate_test_cases`:
    - Validates presence of `work_item_id`, `ado_pat`, and `gemini_api_key`.
    - Invokes `get_ado_work_item` (with defaults for org/proj) to fetch ADO data.
    - Connects to Google Gemini Client.
    - Prompts Gemini to generate exactly 5 Gherkin-formatted test cases.
    - Returns JSON response with `gherkin` and `acceptance_criteria`.
  - `POST /api/generate_sql`:
    - Expects a multipart form-data request containing a `.csv` file.
    - Parses CSV headers.
    - Cleans headers to valid SQL columns.
    - Constructs and returns `create_table_sql` and `completeness_sql` strings.

### Environment & Dependencies (`requirements.txt`, `.env.example`)
- Loads environment variables using `python-dotenv`.
- Major Dependencies:
  - `flask`: Web server framework.
  - `requests`: HTTP client for triggering the ADO API.
  - `google-genai`: Official Google Generative AI SDK used for prompts to Gemini.

## Data Flow (Test Strategy / Test Cases)
1. User supplies inputs containing ADO details and the Gemini Key from the UI, and clicks "Generate".
2. JS event listener triggers and fires a POST fetch request to the respective `/api/...` backend endpoint.
3. Flask backend receives the payload and issues a GET request to the ADO REST API endpoint (`https://dev.azure.com/{org}/{proj}/_apis/wit/workitems/{id}?api-version=7.1`) using basic authentication configured with the ADO PAT to fetch the item's Acceptance Criteria.
4. Flask connects to the Gemini SDK using the provided Gemini Key and passes a constructed prompt containing the Acceptance Criteria to `gemini-2.5-flash`.
5. The generated markdown from Gemini (Test Strategy or Gherkin cases) is passed back to the frontend in a JSON block.
6. The frontend renders the markdown content in dedicated code blocks.

## Data Flow (SQL Generation)
1. User drops a CSV file onto the SQL Generator dropzone and clicks "Generate".
2. JS code appends the file to a standard FormData payload and sends a POST request to `/api/generate_sql`.
3. The Flask app accepts the stream, decodes to UTF-8 using `csv.reader`, and captures the first line containing the headers.
4. Spaces or special characters in headers are sanitized into strictly alphanumeric + underscore strings.
5. `CREATE TABLE` and simple `EXCEPT` SQL strings are formed and returned to frontend.
6. UI blocks populate with the results.
