from flask import request
import base64
from flask_login import current_user


def add_context_processors(app):
    @app.context_processor
    def inject_profile_image():
        included_endpoints = ['index','find_session','user_messages','scheduler','profile']

        # Get the current endpoint
        current_endpoint = request.endpoint

        # Check if the current endpoint is in the excluded list
        if current_endpoint not in included_endpoints:
            return {}

        # If not excluded, inject the profile image
        profile_image = base64.b64encode(current_user.image_data).decode('utf-8') if current_user.image_data else None
        return {'profile_image':profile_image}
