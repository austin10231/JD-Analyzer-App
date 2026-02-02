# src/web_app.py
from flask import Flask, request, render_template, jsonify
from run import analyze_jd

app = Flask(__name__, template_folder="../templates")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    mode = (request.form.get("mode") or "text").strip().lower()

    # 只抓 text（你当前目标）
    if mode == "text":
        jd_text = (request.form.get("jd_text") or "").strip()
        if not jd_text:
            return jsonify({"error": "JD text is required"}), 400
        result = analyze_jd(jd_text)
        return jsonify(result)

    # URL：先留着占位，不影响你现在交付 text 成果
    return jsonify({"error": "URL mode not enabled yet. Please use Text mode."}), 400

if __name__ == "__main__":
    app.run(debug=True)
