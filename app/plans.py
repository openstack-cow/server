from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import Schema, fields, ValidationError
from .models import db, Plan

# Tạo Blueprint cho /plans
plans = Blueprint('plans', __name__)

# Schema để validate và serialize dữ liệu
class PlanSchema(Schema):
    id = fields.Int(dump_only=True)
    type = fields.Str(required=True)
    name = fields.Str(required=True)
    storage_in_gb = fields.Float(required=True)
    ram_in_gb = fields.Float(required=True)
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

"""# Route để thêm plan mới
@plans_bp.route('/', methods=['POST'])
def add_plan():
    try:
        new_plan_data = plan_schema.load(request.json)
        new_plan = Plan(**new_plan_data)
        db.session.add(new_plan)
        db.session.commit()
        return jsonify(plan_schema.dump(new_plan)), 201
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Route để cập nhật plan theo id
@plans_bp.route('/<int:plan_id>', methods=['PUT'])
def update_plan(plan_id):
    plan = Plan.query.get(plan_id)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    try:
        updated_data = plan_schema.load(request.json, partial=True)
        for key, value in updated_data.items():
            setattr(plan, key, value)
        db.session.commit()
        return jsonify(plan_schema.dump(plan)), 200
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Route để xóa plan theo id
@plans_bp.route('/<int:plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    plan = Plan.query.get(plan_id)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    try:
        db.session.delete(plan)
        db.session.commit()
        return jsonify({"message": f"Plan with id {plan_id} deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
"""
