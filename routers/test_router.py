from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import subprocess
import sys
from typing import Optional

router = APIRouter(prefix="/tests", tags=["Tests"])


@router.get("/run")
async def run_tests(
    test_type: Optional[str] = Query(
        "unit", enum=["unit", "integration", "e2e", "all"]
    ),
):
    """
    Run tests based on the specified type.
    """
    test_files = {
        "unit": ["tests/units_tests.py"],
        "integration": ["tests/integration_tests.py"],
        "e2e": ["tests/e2e_tests.py"],
        "all": ["tests/"],
    }

    target = test_files.get(test_type, ["tests/units_tests.py"])

    command = [sys.executable, "-m", "pytest"] + target

    try:
        # Run pytest and capture output
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "command": " ".join(command),
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "Tests timed out after 120 seconds.",
            "error": "",
            "command": " ".join(command),
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "command": " ".join(command),
        }


@router.get("/ui", response_class=HTMLResponse)
async def test_ui():
    """
    Simple UI to run tests and see results.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Runner</title>
        <style>
            body { font-family: sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            .controls { margin-bottom: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            button:disabled { background: #ccc; }
            pre { background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; }
            .status { margin-top: 10px; font-weight: bold; }
            .success { color: green; }
            .failure { color: red; }
        </style>
    </head>
    <body>
        <h1>Test Runner</h1>
        
        <div class="controls">
            <label for="test-type">Test Type:</label>
            <select id="test-type">
                <option value="unit">Unit Tests</option>
                <option value="integration">Integration Tests</option>
                <option value="e2e">E2E Tests</option>
                <option value="all">All Tests</option>
            </select>
            <button onclick="runTests()" id="run-btn">Run Tests</button>
        </div>

        <div id="status" class="status"></div>
        <div id="results"></div>

        <script>
            async def runTests() {
                const type = document.getElementById('test-type').value;
                const btn = document.getElementById('run-btn');
                const status = document.getElementById('status');
                const results = document.getElementById('results');
                
                btn.disabled = true;
                status.textContent = 'Running tests... please wait.';
                status.className = 'status';
                results.innerHTML = '';
                
                try {
                    const response = await fetch(`/api/tests/run?test_type=${type}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        status.textContent = 'Tests Passed!';
                        status.className = 'status success';
                    } else {
                        status.textContent = 'Tests Failed or Error Occurred';
                        status.className = 'status failure';
                    }
                    
                    results.innerHTML = `<pre>${data.output || data.error}</pre>`;
                } catch (e) {
                    status.textContent = 'Error calling API: ' + e;
                    status.className = 'status failure';
                } finally {
                    btn.disabled = false;
                }
            }
            
            // Fix for the script tag above being treated as python by mistake in some editors/viewers
            // It is actually JavaScript inside HTML string.
            // Replacing async def with async function for JS
            document.querySelector('script').textContent = document.querySelector('script').textContent.replace('async def', 'async function');
        </script>
        <script>
            // Correcting the script content directly for the file write
            async function runTests() {
                const type = document.getElementById('test-type').value;
                const btn = document.getElementById('run-btn');
                const status = document.getElementById('status');
                const results = document.getElementById('results');
                
                btn.disabled = true;
                status.textContent = 'Running tests... please wait.';
                status.className = 'status';
                results.innerHTML = '';
                
                try {
                    // Note: The router prefix is /tests, but main.py might include it under /api or root.
                    // Assuming it will be included under /api based on main.py pattern, but let's check main.py inclusion.
                    // If main.py does app.include_router(..., prefix="/api"), then it is /api/tests/run
                    const response = await fetch(`/api/tests/run?test_type=${type}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        status.textContent = 'Tests Passed!';
                        status.className = 'status success';
                    } else {
                        status.textContent = 'Tests Failed or Error Occurred';
                        status.className = 'status failure';
                    }
                    
                    results.innerHTML = `<pre>${data.output || data.error}</pre>`;
                } catch (e) {
                    status.textContent = 'Error calling API: ' + e;
                    status.className = 'status failure';
                } finally {
                    btn.disabled = false;
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content
