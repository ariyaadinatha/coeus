from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/login')
def login():
    return 'Login'

# from flask import Flask
# from flaskr import auth, blog

# def create_app():
#     app = Flask(__name__)
#     @app.route("/hello")
#     def hello():
#         return "Hello, World!"
#     app.register_blueprint(auth.bp)
#     app.register_blueprint(blog.bp)