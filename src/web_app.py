from flask import Flask, request, render_template, jsonify
from run_from_url import analyze_job_from_url

app = Flask(__name__, template_folder="../templates")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    url = request.form.get("job_url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    result = analyze_job_from_url(url)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
