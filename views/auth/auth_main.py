from flask import Blueprint, request, redirect, url_for, render_template, abort, g
from models import User
from flask_login import login_user, current_user, login_required
from forms import LoginForm
auth = Blueprint(
    'auth',
    __name__,
    url_prefix='/auth'
)


@auth.before_request
def get_current_user():
    g.user = current_user


@auth.route('/', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        remember_me = request.form.get('remember_me')
        user = User.query.filter_by(username=username).first()
        if user.check_password(password) and ((user.role == 1 and user_type == 'student') or
                                                          user.role == 2 and user_type == 'tutor'):
            login_user(user, remember=remember_me)
            if user.role == 1:
                return redirect(url_for('student.send_report'))
            if user.role == 2:
                return redirect(url_for('tutor.tutor_home'))
        else:
            return abort(403)
    return render_template('login.html', form=form)


@auth.route('/logout/')
@login_required
def logout():
    login_user(current_user)
