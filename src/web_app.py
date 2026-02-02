from flask import Flask, request, render_template, jsonify
from run_from_url import analyze_job_from_url
from run import analyze_jd

app = Flask(__name__, template_folder="../templates")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()

    mode = data.get("mode")

    try:
        if mode == "url":
            url = data.get("job_url", "").strip()
            if not url:
                return jsonify({"error": "URL is required"}), 400

            result = analyze_job_from_url(url)

        elif mode == "text":
            text = data.get("job_text", "").strip()
            if not text:
                return jsonify({"error": "Job text is required"}), 400

            result = analyze_jd(text)

        else:
            return jsonify({"error": "Invalid mode"}), 400

        return jsonify(result)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Error analyzing job description"}), 500


if __name__ == "__main__":
    app.run(debug=True)
