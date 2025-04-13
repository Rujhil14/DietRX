export FLASK_APP='app.py'
export FLASK_DEBUG=True

rm -rf migrations/ dietrx/app.db
flask db init
flask db migrate
flask db upgrade