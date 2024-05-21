from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
import random
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from sqlalchemy import desc, asc
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from flask_mail import Message
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
import json
from sqlalchemy.orm.attributes import flag_modified
from flask_socketio import emit,  SocketIO
from sqlalchemy import func