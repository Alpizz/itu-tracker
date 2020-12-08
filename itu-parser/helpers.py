import os
import requests
import urllib.parse
import pandas as pd

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def get_departments():
    """Get dictionary of departments from ITU"""
    departments = {}
    url = r'http://www.sis.itu.edu.tr/eng/system/department.html'
    tables = pd.read_html(url)
    for i in range(len(tables[2][0])):
        try:
            if len(tables[2][0][i]) == 3 or len(tables[2][0][i]) == 4:
                departments[tables[2][0][i]] = tables[2][1][i]
        except:
            pass

    departments = dict(sorted(departments.items()))
    return departments

def get_course_table(dep_code):
    """Get all courses in plan"""
    try:
        url = r'http://www.sis.itu.edu.tr/eng/curriculums/plan/' + dep_code + '/201810.html'
        df_list = pd.read_html(url)
        df_list = df_list[2:]
        course_table = []

        for df in df_list:
            course_table.append(pd.DataFrame(df.values[1:], columns=df.values[0]))
        return course_table
    except:
        return apology("Department not found!")

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function