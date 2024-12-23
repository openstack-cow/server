from flask import Blueprint, request, jsonify, render_template
import json

websites = Blueprint('websites', __name__)

@websites.route("/<string:id>", methods=["GET"])
def get_website_info(id):
    print(id)
    with open("app/fake_data/website_info.json", "r") as json_file:
            data = json.load(json_file)
    return jsonify(data), 200


@websites.route("/create", methods=["POST"])
def create_website():
    data = request.get_json()
    print(data)

    # get nova VM info

    # save zipped code somewhere and get url
    

    return jsonify(data), 200