from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields
from ..models import db, Plan

# Tạo Blueprint cho /plans
plans = Blueprint('plans', __name__)

# Schema để validate và serialize dữ liệu
class PlanSchema(Schema):
    id = fields.Int(dump_only=True)
    type = fields.Str(required=True)
    name = fields.Str(required=True)
    storage_in_mb = fields.Int(required=True)
    ram_in_mb = fields.Int(required=True)
    cpu_cores = fields.Int(required=True)
    has_redis = fields.Bool(required=True)
    has_mysql = fields.Bool(required=True)
    monthly_fee_in_usd = fields.Float(required=True)
    image_reference = fields.Str(required=True, example="registry.example.com/myrepository:1.0")

# Tạo instance của PlanSchema
plan_schema = PlanSchema()
plans_schema = PlanSchema(many=True)

# Route để lấy tất cả các plan
@plans.route('/', methods=['GET'])
def get_all_plans():
    plans = Plan.query.all()
    return jsonify(plans_schema.dump(plans)), 200

# Route để lấy thông tin plan cụ thể theo id
@plans.route('/<int:plan_id>', methods=['GET'])
def get_plan_by_id(plan_id):
    plan = Plan.query.get(plan_id)
    if plan:
        return jsonify(plan_schema.dump(plan)), 200
    return jsonify({"error": "Plan not found"}), 404
