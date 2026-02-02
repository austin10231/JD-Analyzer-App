from flask import Flask, request, render_template, jsonify
from run_from_url import analyze_job_from_url
from run import analyze_jd

app = Flask(__name__, template_folder="../templates")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    mode = (request.form.get("mode") or "url").strip().lower()

    try:
        if mode == "text":
            jd_text = (request.form.get("jd_text") or "").strip()
            if not jd_text:
                return jsonify({"error": "JD text is required in Text mode."}), 400
            result = analyze_jd(jd_text)
            return jsonify(result)

        # mode == "url" (best-effort)
        job_url = (request.form.get("job_url") or "").strip()
        if not job_url:
            return jsonify({"error": "URL is required in URL mode."}), 400

        result = analyze_job_from_url(job_url)
        return jsonify(result)

    except Exception as e:
        # URL模式失败很常见（LinkedIn/公司反爬），给明确提示
        msg = str(e) if str(e) else "Failed to analyze."
        if mode == "url":
            msg = f"URL fetch failed (best-effort). Please paste JD text instead. Details: {msg}"
        return jsonify({"error": msg}), 400

if __name__ == "__main__":
    app.run(debug=True)
