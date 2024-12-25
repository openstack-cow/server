from flask import Flask
from flask_login import LoginManager # type: ignore
from flask_migrate import Migrate

# from .utils.choose_plan import choose_plan
from .models import db
from flask_cors import CORS
from .routes.websites import websites
from .routes.plans import plans

from .openstack_service import openstack_service

from app.env import (
    MYSQL_HOSTNAME, MYSQL_HOSTPORT,
    MYSQL_USERNAME, MYSQL_PASSWORD,
    MYSQL_DATABASE, SECRET_KEY,
)

def create_app():
    app = Flask(__name__)
    CORS(app, allow_headers=["Content-Type", "Authorization"])

    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOSTNAME}:{MYSQL_HOSTPORT}/{MYSQL_DATABASE}"
    db.init_app(app)

    migrate = Migrate(app, db) # type: ignore

    # from .views import views
    from .auth import auth
    # from .api import api

    app.register_blueprint(auth,url_prefix='/')
    app.register_blueprint(websites,url_prefix='/websites')
    app.register_blueprint(plans,url_prefix='/plans')

    app.register_blueprint(openstack_service,url_prefix='/openstack_service')
    from .models import User

    # create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' # type: ignore
    login_manager.init_app(app) # type: ignore

    @login_manager.user_loader # type: ignore
    def load_user(id: int): # type: ignore
        return User.query.get(int(id))
    
    from app.utils.job_queue import get_job_queue
    from app.utils.websites.q_check_website_health import q_check_health_of_all_websites
    get_job_queue().enqueue(q_check_health_of_all_websites) # type: ignore

    return app
