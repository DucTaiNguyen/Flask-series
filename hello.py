from flask import Flask, render_template,request, url_for, make_response
import requests
import json
from pony.orm import *
app = Flask(__name__)


app.config.update(dict(DEBUG=False, SECRET_KEY='secret_xxx',
    PONY={
        'provider': 'sqlite',
        'filename': 'suggestions.sqlite3',
        'create_db': True
    }
))

db = Database()
class SearchSuggestion(db.Entity):
    ingredient = Required(str)

db.bind(**app.config['PONY'])
db.generate_mapping(create_tables=True)
Pony(app)

# @app.route('/')
# def hello_world():
#     return 'Hello, World!'

API_KEY='f4bc85df536e4e929a5b2a7e5edb2028'
@app.route('/', methods=['GET', 'POST'])
def recipes():
    if request.method == 'POST':
        content = requests.get(
            "https://api.spoonacular.com/recipes/findByIngredients?ingredients=" +
            str(request.form['restaurant_name']) +
            "&apiKey=" + API_KEY)
        json_response = json.loads(content.text)
        print(json_response)
        return render_template("restaurant_list.html", response=json_response) if json_response != [] else render_template(
            "restaurant_list.html", response="")
    else:
        return render_template("restaurant_list.html")




@app.route('/recipe/<recipe_id>', methods=['GET'])
def recipe(recipe_id):
    response = requests.get("https://api.spoonacular.com/recipes/informationBulk?ids="+recipe_id+"&includeNutrition=true&apiKey="+API_KEY)
    # print(recipe_id)
    return make_response(render_template("recipe_details.html", recipe_id=json.loads(response.text)), 200)

#if __main__ = '__name__':