#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import DBcm
from flask import Flask, render_template, request, escape, session
from flask import copy_current_request_context
from checker import check_logged_in
from threading import Thread

app = Flask(__name__)
app.config['dbconfig'] = {'host': '127.0.0.1', 'user': 'vsearch', 'password': 'vsearchpasswd',
                          'database': 'vsearchlogDB',}


@app.route('/login')
def do_login() -> str:
    session['logged_in'] = True
    return 'You are now logged in'


@app.route('/logout')
def do_logout() -> str:
    session.pop('logged_in')
    return 'You are now logged out'


def search4letters(phrase: str, letters: str = 'aeiou') -> str:
    '''Returns the set of letters found in phrase'''
    return set(letters).intersection(set(phrase))

@app.route('/search', methods=['POST'])
def do_search() -> 'html':
    phrase = request.form['phrase']
    letters = request.form['letters']
    title = 'Here are your results'

    @copy_current_request_context
    def log_request(req: 'flask_request', res: str) -> None:
        with DBcm.UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """insert into log
                (phrase, letters, ip, browser_string, results)
                values
                (%s, %s, %s, %s, %s)"""
            cursor.execute(_SQL, (req.form['phrase'],
                                  req.form['letters'],
                                  req.remote_addr,
                                  req.user_agent.browser,
                                  res,))

    result = str(search4letters(phrase, letters))
    try:
        t = Thread(target=log_request, args=(request, result))
        t.start()
    except Exception as err:
        print('***** Logging failed with this error:', str(err))
    return render_template("results.html", the_title=title, the_phrase=phrase, the_letters=letters, the_results=result)


@app.route('/viewlog')
@check_logged_in
def view_the_log() -> 'html':
    contents = []
    try:
        with DBcm.UseDatabase(app.config['dbconfig']) as cursor:
            _SQL = """select phrase,
                         letters,
                         ip,
                         browser_string,
                         results
                    from log"""
            cursor.execute(_SQL)
            contents = cursor.fetchall()
        titles = ('Phrase', 'Letters', 'Remote_addr', 'User_agent', 'Results')
        return render_template('viewlog.html', the_title='View log', the_row_titles=titles, the_data=contents, )
    except DBcm.ConnectionError as err:
        print('Is your database on? Error:', str(err))
    except DBcm.CredentialsError as err:
        print('User-id/Password issues. Error:', str(err))
    except DBcm.SQLError as err:
        print('Is your query correct? Error:', str(err))
    except Exception as err:
        print('Something went wrong:', str(err))
    return 'Error'

@app.route('/')
@app.route('/entry')
def entry_page() -> 'html':
    return render_template("entry.html", the_title='Welcome!')

app.secret_key = 'EASYpeasyLemonsqEEZY'

if __name__ == '__main__':
    app.run(debug=True)
