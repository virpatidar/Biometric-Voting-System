from flask import Flask,render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
from models import db, Vote, Candidate, User
from models import db
import pyotp
import random
import os
import sqlite3
import base64