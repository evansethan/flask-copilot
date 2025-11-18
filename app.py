import os
from flask import Flask, request, session, render_template_string, redirect, url_for, Response
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

TEMPLATE = """
<!doctype html>
<title>Civicscape Chatbot (Beta)</title>
<style>
    html {
        background-color: #fff;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #fff;
        margin: 0;
    }
    .content-wrapper {
        padding: 2rem;
    }
    h1 { text-align: center; color: #1c1e21; margin-top: 0; }
    textarea, input[type="text"] {
        width: 100%;
        padding: 10px;
        background-color: #f0f2f5;
        margin-bottom: 10px;
        border: 1px solid #ddd;
        border-radius: 6px;
        box-sizing: border-box;
        resize: none; /* Disable manual resizing */
        overflow-y: hidden; /* Hide vertical scrollbar */
        font-size: 1rem;
    }
    button, a button {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 1rem;
        margin-top: 5px;
    }
    button:hover, a button:hover { background-color: #0056b3; }
    hr { border: none; border-top: 1px solid #eee; margin: 2rem 0; }
    a { text-decoration: none; }
    .edit-controls {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .editable-notice {
        font-size: 0.85rem;
        color: #666;
        margin: 0;
    }
</style>
<div class="content-wrapper">
    <h1>Civicscape Chatbot (Beta)</h1>
    <p class="editable-notice">NOTE: Responses can take up to a minute while agent is thinking. This ensures better quality output.</p>
    <form method="post" action="{{ url_for('update_history') }}">
        {% for entry in history %}
            <textarea name="history_{{ loop.index0 }}" rows="2">{{ entry }}</textarea>
        {% endfor %}
        {% if history %}
        <div class="edit-controls">
            <button type="submit">Save Edits</button>
            <p class="editable-notice">Click text to edit chat history</p>
        </div>
        {% endif %}
    </form>
    <hr>
    <form method="post" action="{{ url_for('chat') }}">
        <input type="text" name="user_input" autofocus placeholder="Create an activity or type 'help' for guidance">
        <button type="submit">Run New Prompt</button>
        <a href="{{ url_for('download_history') }}"><button type="button">Download History</button></a>
    </form>
    <script>
        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        }
        document.addEventListener('DOMContentLoaded', () => {
            const textareas = document.querySelectorAll('textarea');
            textareas.forEach(autoResize);
        });
    </script>
</div>
"""

@app.route("/", methods=["GET", "POST"])
def chat():
    if "history" not in session:
        session["history"] = []

    if request.method == "POST":
        # This route only handles submitting new prompts
        user_input = request.form["user_input"]
        full_input = "\n".join(session["history"]) + f"\n\nUser: {user_input}"
        response = client.responses.create(
            prompt={"id": "pmpt_68f92dfb62f481978dc0cb918464c8660de08a28f99a7e59"},
            input=full_input,
        )
        session["history"].extend([f"User: {user_input}", f"Assistant: {response.output_text.strip()}"])
        session.modified = True
        return redirect(url_for("chat"))

    return render_template_string(TEMPLATE, history=session["history"])

@app.route("/update", methods=["POST"])
def update_history():
    if "history" in session:
        # Rebuild history from the submitted form, handling empty fields correctly.
        # This is more robust than iterating by the old history length.
        session["history"] = [value for key, value in sorted(request.form.items()) if key.startswith('history_')]
        session.modified = True
    return redirect(url_for("chat"))

@app.route("/download")
def download_history():
    if "history" not in session or not session["history"]:
        return "No history to download.", 404
    
    plain_text_history = "\n\n--------------------------\n\n".join(
        entry for entry in session["history"]
    )

    return Response(
        plain_text_history,
        mimetype="text/plain",
        headers={"Content-disposition": "attachment; filename=chat_history.txt"}
    )

if __name__ == "__main__":
    app.run(debug=True)
