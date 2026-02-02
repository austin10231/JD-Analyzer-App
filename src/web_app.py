# src/web_app.py
from flask import Flask, request, render_template, jsonify

from run import analyze_jd  # Text analyzer (稳定)

# URL analyzer（能爬就爬）
# 你项目里已有：src/run_from_url.py -> analyze_job_from_url(url)
try:
    from run_from_url import analyze_job_from_url
    URL_ENABLED = True
except Exception:
    analyze_job_from_url = None
    URL_ENABLED = False

app = Flask(__name__, template_folder="../templates")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    mode = (request.form.get("mode") or "text").strip().lower()

    # -------- Text mode (recommended) --------
    if mode == "text":
        jd_text = (request.form.get("jd_text") or "").strip()
        if not jd_text:
            return jsonify({"error": "JD text is required"}), 400

        try:
            result = analyze_jd(jd_text)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": f"Text analysis failed: {str(e)}"}), 500

    # -------- URL mode (best-effort) --------
    if mode == "url":
        job_url = (request.form.get("job_url") or "").strip()
        if not job_url:
            return jsonify({"error": "URL is required"}), 400

        if not URL_ENABLED or analyze_job_from_url is None:
            return jsonify({"error": "URL mode is not available (run_from_url import failed). Use Text mode."}), 400

        try:
            result = analyze_job_from_url(job_url)
            return jsonify(result)
        except Exception as e:
            # URL 爬不了很正常（LinkedIn / 反爬 / 登录墙）
            return jsonify({"error": f"URL fetch failed (try Text mode): {str(e)}"}), 400

    return jsonify({"error": "Invalid mode. Use mode=text or mode=url."}), 400


if __name__ == "__main__":
    app.run(debug=True)
