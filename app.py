import os
from flask import Flask, request, jsonify
from flask_cors import cross_origin, CORS
from ingestion import upsert_post, delete_post
from retrieval import ask_ai    
from utility.prompt_injection_filtering import is_prompt_injection
from utility.prompts.system import SYSTEM_PROMPT
from utility.config import build_response
app = Flask(__name__)

frontend_url = os.getenv('FRONTEND_END_URL')
MAX_QUERY_LENGTH = os.getenv('MAX_QUERY_LENGTH')
# CORS(app, resources={r"/ask": {"origins": "*"}})


CORS(app, resources={
    r"/ask": {"origins": [frontend_url,"http://localhost:5173"]},
    r"/ingest": {"origins": [frontend_url,"http://localhost:5173"]}
})

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

    if not query:
       return jsonify(
        build_response(
            content="Please enter a question to continue.",
            posts=None,
            videos=None,
            suggestions=[],
            response_type="text"
        )
    ), 400

    if len(query) > int(MAX_QUERY_LENGTH):
        return jsonify(
        build_response(
            content="Your question is too long. Please shorten it.",
            posts=None,
            videos=None,
            suggestions=[],
            response_type="text"
        )
    ), 400
    
    if is_prompt_injection(query):
        return jsonify(
        build_response(
            content="I can only help with questions related to the post content.",
            posts=None,
            videos=None,
            suggestions=[],
            response_type="text"
        )
    ), 400
    
    current_post_id = request.json.get("current_post_id", "")
    result = ask_ai(query,current_post_id, SYSTEM_PROMPT)
    return jsonify(result)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)