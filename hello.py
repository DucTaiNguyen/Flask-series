from flask import Flask, render_template,request, url_for, make_response
import requests
import json
from pony.orm import *
from pony.flask import Pony
from restaurant_input_adapter import convert_input




from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from flask_login import UserMixin
app = Flask(__name__)


class UserRegistryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')


app.config.update(dict(DEBUG=False, SECRET_KEY='secret_xxx',
    PONY={
        'provider': 'sqlite',
        'filename': 'suggestions.sqlite3',
        'create_db': True
    }
))

db = Database()


class User(db.Entity, UserMixin):
    login = Required(str, unique=True)
    username = Required(str)
    password = Required(str)
    is_active = Required(bool)
    recipes = Set("UserCreatedRecipe")

class UserCreatedRecipe(db.Entity):
    name = Required(str)
    ingredients = Required(str)
    instructions = Required(str)
    user = Required(User)
class SearchSuggestion(db.Entity):
    ingredient = Required(str)

class IngredientChip(db.Entity):
    chip_ingredients= Required(str)
    

db.bind(**app.config['PONY'])
db.generate_mapping(create_tables=True)

Pony(app)



API_KEY='f4bc85df536e4e929a5b2a7e5edb2028'







# @app.before_request
# def enforce_https_in_heroku():
#     if request.headers.get('X-Forwarded-Proto') == 'http':
#         url = request.url.replace('http://', 'https://', 1)
#         code = 301
#         return redirect(url, code=code)

# def hash_password(password):
#     """Hash a password for storing."""
#     salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
#     pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
#                                   salt, 100000)
#     pwdhash = binascii.hexlify(pwdhash)
#     return (salt + pwdhash).decode('ascii')

# def verify_password(stored_password, provided_password):
#     """Verify a stored password against one provided by user"""
#     salt = stored_password[:64]
#     stored_password = stored_password[64:]
#     pwdhash = hashlib.pbkdf2_hmac('sha512',
#                                   provided_password.encode('utf-8'),
#                                   salt.encode('ascii'),
#                                   100000)
#     pwdhash = binascii.hexlify(pwdhash).decode('ascii')
#     return pwdhash == stored_password

# def retrieve_ingredients_from_api_and_users(chip_ingredients):
#     ing_suggestions = select(prod for prod in IngredientChip)
#     for entry in ing_suggestions:
#         chip_ingredients.append(entry)
#     chip_ingredients_as_json = {"chipIngredients": chip_ingredients}
#     ingredients = ",".join(map(lambda db_entry: db_entry.ingredient, chip_ingredients))
#     print("Ingredients ", ingredients)
#     recipes = UserCreatedRecipe.select(
#         lambda recipe1: ingredients in recipe1.ingredients)  # if ingredients in userRecipe.ingredients
#     print("Recipes", recipes)
#     return chip_ingredients_as_json, ingredients, recipes

# def build_user_plus_api_json_responses(ingredients, recipes, user_recipes, user_recipes_as_json):
#     for recipe_from_user in recipes:
#         print(recipe_from_user.name)
#         user_recipes.append({"name": recipe_from_user.name, "ingredients": recipe_from_user.ingredients,
#                              "instructions": recipe_from_user.instructions,
#                              "user_recipe_id": recipe_from_user.id})
#     user_recipes_as_json = {"userRecipes": user_recipes}
#     print(user_recipes_as_json)
#     content = requests.get(
#         "https://api.spoonacular.com/recipes/findByIngredients?ingredients=" +
#         convert_input(ingredients) +
#         "&apiKey=" + API_KEY)
#     json_response = json.loads(content.text)
#     return json_response, user_recipes_as_json

# @db_session
# @app.route('/userRegistry', methods=['GET', 'POST'])
# def user_registry():
#     form = UserRegistryForm()
#     if form.validate_on_submit():
#         if request.method == 'POST':
#             email = request.form['email']
#             password = hash_password(request.form['password'])
#             name = request.form['name']
#             exist = User.get(login=email)
#             if exist:
#                 flash('The address %s is already in use, choose another one' % email)
#                 return redirect('/userRegistry')
#             curr_user = User(login=email, username=name, password=password, is_active=False)
#             commit()
#             localhost_url = 'http://0.0.0.0:5000'
#             message = Mail(
#                 from_email='<sender_email>',
#                 to_emails=To(email),
#                 subject='Confirm your account',
#                 html_content='<h2>Hello,<h2> to complete your registration click  <a href="' + (
#                         os.environ.get("HEROKU_URL") or localhost_url) + '/activate/' + str(
#                     curr_user.id) + '"> here </a>.'
#             )
#             try:
#                 sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
#                 response = sg.send(message)
#             except Exception as e:
#                 print(e.message)
#             return redirect('/')
#     else:
#         return render_template('registry_form.html', title='Register', form=form)



# @app.route('/', methods=['GET', 'POST'])
# def get_recipe():
#     ingredients_searched = []
#     chip_ingredients = []
#     user_recipes = []
#     suggestions_as_json = {"searches": ingredients_searched}
#     chip_ingredients_as_json = {"chipIngredients": chip_ingredients}
#     user_recipes_as_json = {"userRecipes": user_recipes}
#     if request.method == 'POST':
#         suggestions_as_json = handle_searches(ingredients_searched, suggestions_as_json)
#         chip_ingredients_as_json, ingredients, recipes = retrieve_ingredients_from_api_and_users(chip_ingredients,chip_ingredients_as_json)
#         json_response, user_recipes_as_json = build_user_plus_api_json_responses(ingredients, recipes, user_recipes, user_recipes_as_json)
#         return render_template("recipes_list.html", ans=json_response, searchHistory=suggestions_as_json,
#                                chipIngredients=chip_ingredients_as_json, userRecipes=user_recipes_as_json['userRecipes'])
#     else:
#         delete(ingredient for ingredient in IngredientChip)
#         return render_template("recipes_list.html", searchHistory=suggestions_as_json,
#                                chipIngredients=chip_ingredients_as_json, userRecipes=user_recipes_as_json['userRecipes'])














@app.route('/', methods=['GET', 'POST'])
def get_recipe():
    ingredients_searched = []
    suggestions_as_json = {"searches": ingredients_searched}
    if request.method == 'POST':
        ingredients = "".join(request.form['restaurant_name'].split()).split(",")
        with db_session:
            [SearchSuggestion(ingredient=suggestion) for suggestion in ingredients]

        search_suggestions = select(prod for prod in SearchSuggestion).order_by(lambda prod: desc(prod.id))[:5]
        for entry in search_suggestions:
            ingredients_searched.append(entry.ingredient)
        suggestions_as_json = {"searches": ingredients_searched}

        content = requests.get(
            "https://api.spoonacular.com/recipes/findByIngredients?ingredients=" +
            convert_input(request.form['restaurant_name']) +
            "&apiKey=" + API_KEY)
        json_response = json.loads(content.text)
        print(json_response)
        return render_template("restaurant_list.html", response=json_response,searchHistory = suggestions_as_json) if json_response != [] else render_template(
            "restaurant_list.html", response="",searchHistory=suggestions_as_json)
    else:
        return render_template("restaurant_list.html",searchHistory=suggestions_as_json)        

    #     return render_template("restaurant_list.html", ans = json_response, searchHistory = suggestions_as_json) if json_response != [] else render_template("restaurant_list.html",ans="",searchHistory=suggestions_as_json)
    # else:
    #     return render_template("restaurant_list.html",searchHistory=suggestions_as_json)





@app.route('/recipe/<recipe_id>', methods=['GET'])
def recipe(recipe_id):
    response = requests.get("https://api.spoonacular.com/recipes/informationBulk?ids="+recipe_id+"&includeNutrition=true&apiKey="+API_KEY)
    # print(recipe_id)
    return make_response(render_template("recipe_details.html", recipe_id=json.loads(response.text)), 200)

#if __main__ = '__name__':