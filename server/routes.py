# routes in a separate file just for them
import hashlib
from datetime import timedelta

from flask_login import login_user, logout_user, login_required

from server import app, db

import sys

from dataclasses import asdict
import json
from flask import request, render_template, flash, url_for
import server.tune as tune
from server.model.models import User, SpsaParam, SpsaTest, Param
from server.tune import push_result_json, push_test, push_test_json
from common import spsa

sys.path.append("/")


@app.route("/test", methods=["POST"])
def submit_test():
    content = request.get_json()
    push_test_json(content)
    return ""


@app.route("/result", methods=["POST"])
def submit_result():
    content = request.get_json()
    push_result_json(content)
    return ""


@app.route("/get")
def get_test():
    test = tune.get_test()
    if test is not None:
        return json.dumps(asdict(test))
    return ""


@app.route("/params/<test_id>")
def get_params(test_id):
    test = tune.get_test_by_id(test_id)
    if test is not None:
        return json.dumps(test)
    return ""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/loginPage")
def login():
    return render_template("login.html")


@app.route("/signupPage")
def registrationPage():
    return render_template("sign_up.html")


@app.route("/signup", methods=["POST"])
def signup():
    """
    Reads the user credentials from a http request and adds him to the project database
        :return: redirect to index page
    """
    email = request.form.get("email")
    password = request.form.get("password")
    hashed_password = hashlib.sha512(password.encode()).hexdigest()
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    if user:
        flash("Username is invalid or already taken", "error")
        return render_template("sign_up.html")

    utente = User(email=email, password=hashed_password, username=username)

    db.session.add(utente)
    db.session.commit()

    login_user(utente, duration=timedelta(days=365), force=True)
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def Login():
    """
    reads a user login credentials from a http request and if they are valid logs the user in with those same
    credentials,changing his state from anonymous  user to logged user
    :return: redirect to index page
    """
    email = request.form.get("email")
    password = request.form.get("password")
    hashed_password = hashlib.sha512(password.encode()).hexdigest()
    attempted_user: User = User.query.filter_by(email=email).first()
    if not attempted_user:
        print(attempted_user.__class__)
        flash("User doesn't exist", "error")
        return render_template("login.html")

    if attempted_user.password == hashed_password:
        login_user(attempted_user, duration=timedelta(days=365), force=True)
    else:
        flash("wrong password ", "error")
        return render_template("login.html")
    return render_template("index.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    """
    logs a user out, changing his state from logged user to anonymous user
        :return:redirect to index page
    """
    logout_user()
    return render_template("index.html")


@app.route("/TestPage", methods=["GET", "POST"])
@login_required
def TestPage():
    return render_template("test.html")


@app.route("/Test", methods=["GET", "POST"])
@login_required
def addTest():
    spsa_test = SpsaTest(
        test_id=request.form.get("test_id", type=str),
        engine=request.form.get("engine", type=str),
        branch=request.form.get("branch", type=str),
        book=request.form.get("book", type=str),
        hash_size=request.form.get("hash_size", type=int),
        tc=request.form.get("tc", type=float),
    )
    db.session.add(spsa_test)
    db.session.commit()

    Spsaparam = SpsaParam(
        max_iter=request.form.get("max_iter", type=int),
        a=request.form.get("a", type=float),
        c=request.form.get("c", type=float),
        _A=request.form.get("_A", type=float),
        alpha=request.form.get("alpha", type=float),
        gamma=request.form.get("gamma", type=float),
    )

    db.session.add(Spsaparam)
    db.session.commit()
    parameters = dict()
    parameters_number = request.form.get("parameters", type=int)
    for x in range(1, parameters_number + 1):
        paramDB = Param(
            param_name=request.form.get("param_name" + x.__str__()),
            value=request.form.get("value" + x.__str__(), type=float),
            lowest=request.form.get("lowest" + x.__str__(), type=float),
            highest=request.form.get("highest" + x.__str__(), type=float),
            step=request.form.get("step" + x.__str__(), type=float),
            test_id=spsa_test.test_id,
        )
        db.session.add(paramDB)
        db.session.commit()
        param = spsa.Param(
            paramDB.value, paramDB.lowest, paramDB.highest, paramDB.step,
        )
        parameters[paramDB.param_name] = param

    test = spsa.SpsaTest(
        spsa_test.test_id,
        spsa_test.engine,
        spsa_test.branch,
        spsa_test.book,
        spsa_test.hash_size,
        spsa_test.tc,
    )

    spsa_params = spsa.SpsaParam(
        Spsaparam.max_iter,
        Spsaparam.a,
        Spsaparam.c,
        Spsaparam._A,
        Spsaparam.alpha,
        Spsaparam.gamma,
    )

    print(parameters)
    push_test(test, spsa_params, parameters)

    return render_template("index.html")


@app.route("/TestList", methods=["GET", "POST"])
def ShowTests():
    tests = SpsaTest.query.filter_by(status="ongoing").all()
    return render_template("tests.html", tests=tests)
