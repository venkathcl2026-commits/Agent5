function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
}

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('csv-file');
const fileNameDisplay = document.getElementById('file-name-display');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
});

dropZone.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
        fileInput.files = files;
        updateFileName(files[0].name);
    }
}

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        updateFileName(e.target.files[0].name);
    }
});

function updateFileName(name) {
    fileNameDisplay.textContent = `Selected file: ${name}`;
}

document.getElementById('generate-test-cases-btn').addEventListener('click', async () => {
    const workItemId = document.getElementById('ado-item-id').value.trim();
    const adoPat = document.getElementById('ado-pat').value.trim();
    const geminiApiKey = document.getElementById('gemini-api-key').value.trim();
    if (!workItemId) {
        alert('Please enter a Work Item ID');
        return;
    }

    const btn = document.getElementById('generate-test-cases-btn');
    const loading = document.getElementById('tc-loading');
    const resultArea = document.getElementById('tc-result');

    btn.disabled = true;
    loading.style.display = 'flex';
    resultArea.style.display = 'none';

    try {
        const response = await fetch('/api/generate_test_cases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                work_item_id: workItemId,
                ado_pat: adoPat,
                gemini_api_key: geminiApiKey
            })
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('tc-criteria').textContent = data.acceptance_criteria;
            document.getElementById('tc-gherkin').textContent = data.gherkin;
            resultArea.style.display = 'block';
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`An error occurred: ${error.message}`);
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
});

document.getElementById('generate-sql-btn').addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a CSV file first');
        return;
    }

    const btn = document.getElementById('generate-sql-btn');
    const loading = document.getElementById('sql-loading');
    const resultArea = document.getElementById('sql-result');

    btn.disabled = true;
    loading.style.display = 'flex';
    resultArea.style.display = 'none';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/generate_sql', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('sql-create-table').textContent = data.create_table_sql;
            document.getElementById('sql-completeness').textContent = data.completeness_sql;
            resultArea.style.display = 'block';
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`An error occurred: ${error.message}`);
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
});

document.getElementById('generate-test-strategy-btn').addEventListener('click', async () => {
    const organization = document.getElementById('ts-organization').value.trim();
    const project = document.getElementById('ts-project').value.trim();
    const workItemId = document.getElementById('ts-ado-item-id').value.trim();
    const adoPat = document.getElementById('ts-ado-pat').value.trim();
    const geminiApiKey = document.getElementById('ts-gemini-api-key').value.trim();

    if (!organization || !project || !workItemId) {
        alert('Please enter Organization, Project, and Work Item ID');
        return;
    }

    const btn = document.getElementById('generate-test-strategy-btn');
    const loading = document.getElementById('ts-loading');
    const resultArea = document.getElementById('ts-result');

    btn.disabled = true;
    loading.style.display = 'flex';
    resultArea.style.display = 'none';

    try {
        const response = await fetch('/api/generate_test_strategy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                organization: organization,
                project: project,
                work_item_id: workItemId,
                ado_pat: adoPat,
                gemini_api_key: geminiApiKey
            })
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('ts-criteria').textContent = data.acceptance_criteria;
            document.getElementById('ts-plan').textContent = data.test_strategy;
            resultArea.style.display = 'block';
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`An error occurred: ${error.message}`);
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
});

document.getElementById('convert-code-btn').addEventListener('click', async () => {
    const javaCode = document.getElementById('cc-java-code').value.trim();
    const geminiApiKey = document.getElementById('cc-gemini-api-key').value.trim();

    if (!javaCode) {
        alert('Please enter Java code');
        return;
    }
    if (!geminiApiKey) {
        alert('Please enter a Gemini API Key');
        return;
    }

    const btn = document.getElementById('convert-code-btn');
    const loading = document.getElementById('cc-loading');
    const resultArea = document.getElementById('cc-result');

    btn.disabled = true;
    loading.style.display = 'flex';
    resultArea.style.display = 'none';

    try {
        const response = await fetch('/api/convert_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                java_code: javaCode,
                gemini_api_key: geminiApiKey
            })
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('cc-python').textContent = data.python;
            document.getElementById('cc-csharp').textContent = data.csharp;
            resultArea.style.display = 'block';
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`An error occurred: ${error.message}`);
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
});

document.getElementById('generate-java-btn').addEventListener('click', async () => {
    const gherkinCode = document.getElementById('cc-gherkin-code').value.trim();
    const geminiApiKey = document.getElementById('cc-gemini-api-key').value.trim();

    if (!gherkinCode) {
        alert('Please enter Gherkin code');
        return;
    }
    if (!geminiApiKey) {
        alert('Please enter a Gemini API Key');
        return;
    }

    const btn = document.getElementById('generate-java-btn');
    const javaTextarea = document.getElementById('cc-java-code');
    const loading = document.getElementById('cc-loading');

    btn.disabled = true;
    loading.style.display = 'flex';

    try {
        const response = await fetch('/api/generate_java_from_gherkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                gherkin_code: gherkinCode,
                gemini_api_key: geminiApiKey
            })
        });

        const data = await response.json();

        if (response.ok) {
            javaTextarea.value = data.java;
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`An error occurred: ${error.message}`);
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
});

// Attach Test Cases Tab Logic
const atcDropZone = document.getElementById('atc-drop-zone');
const atcFileInput = document.getElementById('atc-csv-file');
const atcFileNameDisplay = document.getElementById('atc-file-name-display');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    atcDropZone.addEventListener(eventName, preventDefaults, false);
});

['dragenter', 'dragover'].forEach(eventName => {
    atcDropZone.addEventListener(eventName, () => atcDropZone.classList.add('dragover'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    atcDropZone.addEventListener(eventName, () => atcDropZone.classList.remove('dragover'), false);
});

atcDropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
        atcFileInput.files = files;
        atcFileNameDisplay.textContent = `Selected file: ${files[0].name}`;
    }
}, false);

atcFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        atcFileNameDisplay.textContent = `Selected file: ${e.target.files[0].name}`;
    }
});

document.getElementById('attach-test-cases-btn').addEventListener('click', async () => {
    const file = atcFileInput.files[0];
    if (!file) {
        alert('Please select a CSV file containing test cases');
        return;
    }

    const organization = document.getElementById('atc-organization').value.trim();
    const project = document.getElementById('atc-project').value.trim();
    const workItemId = document.getElementById('atc-ado-item-id').value.trim();
    const adoPat = document.getElementById('atc-ado-pat').value.trim();

    if (!organization || !project || !workItemId || !adoPat) {
        alert('Organization, Project, Work Item ID, and ADO PAT are required');
        return;
    }

    const btn = document.getElementById('attach-test-cases-btn');
    const loading = document.getElementById('atc-loading');
    const resultArea = document.getElementById('atc-result');
    const outputDiv = document.getElementById('atc-output');

    btn.disabled = true;
    loading.style.display = 'flex';
    resultArea.style.display = 'none';

    const formData = new FormData();
    formData.append('file', file);
    formData.append('organization', organization);
    formData.append('project', project);
    formData.append('work_item_id', workItemId);
    formData.append('ado_pat', adoPat);

    try {
        const response = await fetch('/api/attach_test_cases', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            let outputHtml = `<strong>${data.message}</strong>\n\n`;
            data.results.forEach(res => {
                if (res.id) {
                    outputHtml += `✅ Created Test Case #${res.id}: ${res.title}\n`;
                } else {
                    outputHtml += `❌ Failed: ${res.title} - ${res.status}\n`;
                }
            });
            outputDiv.innerHTML = outputHtml;
            resultArea.style.display = 'block';
        } else {
            outputDiv.innerHTML = `<span style="color: #ef4444; font-weight: 500;">❌ Error: ${data.error}</span>`;
            resultArea.style.display = 'block';
        }
    } catch (error) {
        alert(`An error occurred: ${error.message}`);
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
});
