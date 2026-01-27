from flask import Flask, request, jsonify
from flask_cors import cross_origin, CORS
from ingestion import upsert_post, delete_post
from retrieval import ask_ai    


app = Flask(__name__)
CORS(app, resources={r"/ask": {"origins": "*"}})

@app.route("/ingest", methods=["POST"])
def ingest():
    post = request.json
    upsert_post(post)
    return {"status": "indexed"}

@app.route("/delete/<post_id>", methods=["DELETE"])
def remove(post_id):
    delete_post(post_id)
    return {"status": "deleted"}

@app.route("/ask", methods=["POST"])
def ask():
    query = request.json.get("query")
    current_post_id = request.json.get("current_post_id", "")
    result = ask_ai(query,current_post_id)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)