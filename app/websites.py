from flask import Blueprint, request, jsonify, render_template
import json

websites = Blueprint('websites', __name__)

@websites.route("/<string:id>", methods=["GET"])
def get_website_info(id):
    print(id)
    with open("app/fake_data/website_info.json", "r") as json_file:
            data = json.load(json_file)
    return jsonify(data), 200
