import vwo
import threading
import json
import os

from flask import (
    Flask, g, render_template, session, redirect, url_for, request
)
from vwo import UserStorage, GOAL_TYPES, LOG_LEVELS

from os.path import join, dirname
from dotenv import load_dotenv
from flaskr.utils import user
from flaskr.models import home_model, history_model, about_model

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()

    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


# GLOBAL VARIABLES
vwo_client_instance = None
settings_file = None
user_storage_instance = None
vwo_logger = None


class UserStorage(UserStorage):
    def __init__(self):
        self._db = {}

    def get(self, user_id, campaign_key):
        return self._db.get((user_id, campaign_key))

    def set(self, user_storage_data):
        self._db[(user_storage_data['userId'], user_storage_data['campaignKey'])] = user_storage_data


class CustomLogger:
    def log(self, level, message):
        print(level, message)


def init_vwo_sdk_via_launch_func(account_id, sdk_key):
    global vwo_client_instance
    global settings_file
    global user_storage_instance
    global vwo_logger

    print('INIT SDK CALLED - POLLING - Launch Function')

    new_settings_file = vwo.get_settings_file(account_id, sdk_key)
    stringify_old_settings_file = json.dumps(settings_file)

    if new_settings_file != stringify_old_settings_file:
        print('SETTINGS UPDATED')
        settings_file = json.loads(new_settings_file)

        vwo_client_instance = vwo.launch(
            new_settings_file,
            None,
            user_storage_instance,
            False,
            log_level=LOG_LEVELS.DEBUG,
            goal_type_to_track=GOAL_TYPES.ALL,
            should_track_returning_user=True
        )

        print('VWO SDK INSTANCE CREATED')



def init_vwo_sdk_via_vwo_class(account_id, sdk_key):
    global vwo_client_instance
    global settings_file
    global user_storage_instance

    print('INIT SDK CALLED - POLLING - VWO Class')

    new_settings_file = vwo.get_settings_file(account_id, sdk_key)
    stringify_old_settings_file = json.dumps(settings_file)

    if new_settings_file != stringify_old_settings_file:
        print('SETTINGS UPDATED')
        settings_file = json.loads(new_settings_file)

        settings_file = new_settings_file
        user_storage = user_storage_instance
        is_development_mode = False
        goal_type_to_track = GOAL_TYPES.ALL
        should_track_returning_user = True
        # logger = CustomLogger()

        vwo_client_instance = vwo.VWO(
            settings_file,
            user_storage,
            is_development_mode,
            goal_type_to_track,
            should_track_returning_user,
            # logger
        )

        print('VWO SDK INSTANCE CREATED')


def create_app():
    global settings_file
    global user_storage_instance
    global vwo_client_instance
    global vwo_logger

    ACCOUNT_ID = os.environ.get("ACCOUNT_ID")
    SDK_KEY = os.environ.get("SDK_KEY")
    SECRET_KEY = os.environ.get("SECRET_KEY")

    user_storage_instance = UserStorage()
    vwo_logger = CustomLogger()

    # # Using VWO Class
    # init_vwo_sdk_via_vwo_class(ACCOUNT_ID, SDK_KEY)
    # POLL_TIME = 10
    # set_interval(lambda: init_vwo_sdk_via_vwo_class(ACCOUNT_ID, SDK_KEY), POLL_TIME)

    # Using launch function
    init_vwo_sdk_via_launch_func(ACCOUNT_ID, SDK_KEY)
    POLL_TIME = 10
    set_interval(lambda: init_vwo_sdk_via_launch_func(ACCOUNT_ID, SDK_KEY), POLL_TIME)

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config['DEBUG'] = True
    app.secret_key = SECRET_KEY

    @app.before_request
    def check_user():
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        user_valid = session.get('user_valid')
        user_special = session.get('user_special')

        if (
            user_id is None or
            user_name is None or
            user_valid is None or
            user_special is None
        ):
            session['user_id'] = user.get_random_user_id()
            session['user_name'] = user.get_random_name()
            session['user_valid'] = user.get_random_user_valid_status()
            session['user_special'] = user.get_random_user_special_status()

        g.user = {
            'user_name': session['user_name'],
            'user_id': session['user_id'],
            'user_valid': session['user_valid'],
            'user_special': session['user_special']
        }

    @app.route('/clear_session')
    def clear_session():
        session.clear()
        g.user = None
        return redirect(url_for('index_page'))

    @app.route('/')
    def index_page():
        return render_template('index.html')

    ###############################
    ######## FEATURE TEST #########
    ###############################
    @app.route('/home')
    def home_page():
        default_data = home_model.HOME_PAGE
        config = home_model.FEATURE_TEST_CONFIG

        is_user_part_of_feature_campaign = vwo_client_instance.is_feature_enabled(
            config.get('campaign_key'),
            session['user_id']
        )

        vwo_client_instance.track(
            config.get('campaign_key'),
            session['user_id'],
            config['goal_identifier'],
            custom_variables={'is_active': session['user_valid'], 'is_special': session['user_special']}
        )

        price_var = vwo_client_instance.get_feature_variable_value(
            config.get('campaign_key'),
            config.get('price_key'),
            session['user_id']
        )

        os_var = vwo_client_instance.get_feature_variable_value(
            config.get('campaign_key'),
            config.get('os_key'),
            session['user_id']
        )

        discount_var = vwo_client_instance.get_feature_variable_value(
            config.get('campaign_key'),
            config.get('discount_key'),
            session['user_id']
        )

        available_var = vwo_client_instance.get_feature_variable_value(
            config.get('campaign_key'),
            config.get('available_key'),
            session['user_id']
        )

        data = {'price': price_var, 'os': os_var, 'available': available_var, 'discount': discount_var}

        return render_template(
            'home.html',
            default_data=default_data,
            data=data,
            file=settings_file,
            is_user_part_of_feature_campaign=is_user_part_of_feature_campaign
        )

    ###############################
    ######### FEATURE AB ##########
    ###############################
    @app.route('/about')
    def about_page():
        default_data = about_model.CONTROL
        config = about_model.FEATURE_AB_CONFIG

        variation_name = vwo_client_instance.activate(config.get('campaign_key'), session['user_id'])

        if variation_name:
            is_part_of_campaign = True
        else:
            is_part_of_campaign = False

        if variation_name == 'Control':
            data = about_model.CONTROL
        elif variation_name == 'Variation-1':
            data = about_model.VARIATION_1
        elif variation_name == 'Variation-2':
            data = about_model.VARIATION_2
        elif variation_name == 'Variation-3':
            data = about_model.VARIATION_3

        vwo_client_instance.track(config.get('campaign_key'), session['user_id'], config.get('goal_identifier'))

        return render_template(
            'about.html',
            default_data=default_data,
            data=data,
            variation_name=variation_name,
            file=settings_file,
            is_part_of_campaign=is_part_of_campaign
        )

    ###############################
    ####### FEATURE ROLLOUT #######
    ###############################
    @app.route('/history')
    def history_page():
        default_data = history_model.HISTORY
        config = history_model.FEATURE_ROLLOUT_CONFIG

        is_user_part_of_feature_rollout_campaign = vwo_client_instance.is_feature_enabled(
            config.get('campaign_key'),
            session['user_id']
        )

        price_var = vwo_client_instance.get_feature_variable_value(
            config.get('campaign_key'),
            config.get('price_key'),
            session['user_id']
        )

        os_var = vwo_client_instance.get_feature_variable_value(
            config.get('campaign_key'),
            config.get('os_key'),
            session['user_id']
        )

        discount_var = vwo_client_instance.get_feature_variable_value(
            config.get('campaign_key'),
            config.get('discount_key'),
            session['user_id']
        )

        available_var = vwo_client_instance.get_feature_variable_value(
            config.get('campaign_key'),
            config.get('available_key'),
            session['user_id']
        )

        data = {'price': price_var, 'os': os_var, 'available': available_var, 'discount': discount_var}

        return render_template(
            'history.html',
            default_data=default_data,
            data=data,
            is_user_part_of_campaign=is_user_part_of_feature_rollout_campaign,
            file=settings_file
        )

    ###############################
    ####### CUSTOM DIMENSION #######
    ###############################
    @app.route('/push_tag')
    def push_tag():
        return render_template('push.html')

    @app.route('/handle_push_new_tag', methods=['POST'])
    def handle_push_new_tag():
        tag_name = request.form['tag_name']
        tag_value = request.form['tag_value']
        vwo_client_instance.push(tag_name, tag_value, session['user_id'])

        return redirect(url_for('push_tag'))

    return app
