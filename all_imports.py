from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint, Response, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from sqlalchemy import desc, asc, JSON
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
import json
from sqlalchemy.orm.attributes import flag_modified
from flask_socketio import emit,  SocketIO
from sqlalchemy import func
import base64
from PIL import Image
from io import BytesIO, StringIO
import io
import csv
from flask_mail import Mail, Message
import secrets
from functools import wraps