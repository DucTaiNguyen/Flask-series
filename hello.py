from flask import Flask, render_template,request, url_for, make_response, flash,redirect
import requests
import json

from pony.orm import *
from pony.flask import Pony
from restaurant_input_adapter import convert_input


import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import hashlib
import binascii

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from flask_login import UserMixin,current_user,LoginManager,login_user
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







@app.before_request
def enforce_https_in_heroku():
    if request.headers.get('X-Forwarded-Proto') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

def retrieve_ingredients_from_api_and_users(chip_ingredients):
    ing_suggestions = select(prod for prod in IngredientChip)
    for entry in ing_suggestions:
        chip_ingredients.append(entry)
    chip_ingredients_as_json = {"chipIngredients": chip_ingredients}
    ingredients = ",".join(map(lambda db_entry: db_entry.ingredient, chip_ingredients))
    print("Ingredients ", ingredients)
    recipes = UserCreatedRecipe.select(
        lambda recipe1: ingredients in recipe1.ingredients)  # if ingredients in userRecipe.ingredients
    print("Recipes", recipes)
    return chip_ingredients_as_json, ingredients, recipes

def build_user_plus_api_json_responses(ingredients, recipes, user_recipes, user_recipes_as_json):
    for recipe_from_user in recipes:
        print(recipe_from_user.name)
        user_recipes.append({"name": recipe_from_user.name, "ingredients": recipe_from_user.ingredients,
                             "instructions": recipe_from_user.instructions,
                             "user_recipe_id": recipe_from_user.id})
    user_recipes_as_json = {"userRecipes": user_recipes}
    print(user_recipes_as_json)
    content = requests.get(
        "https://api.spoonacular.com/recipes/findByIngredients?ingredients=" +
        convert_input(ingredients) +
        "&apiKey=" + API_KEY)
    json_response = json.loads(content.text)
    return json_response, user_recipes_as_json

@db_session
@app.route('/userRegistry', methods=['GET', 'POST'])
def user_registry():
    form = UserRegistryForm()
    if form.validate_on_submit():
        if request.method == 'POST':
            email = request.form['email']
            print(email)
            password = hash_password(request.form['password'])
            name = request.form['name']
            exist = User.get(login=email)
            if exist:
               flash('The address %s is already in use, choose another one' % email)
               return redirect('/userRegistry')
            curr_user = User(login=email, username=name, password=password, is_active=False)
            commit()
            localhost_url = 'http://127.0.0.1:5000/'                 #'http://0.0.0.0:5000/'
            message = Mail(
                from_email='<sender_email>',
                to_emails=email,
                subject='Confirm your account',
                html_content='<h2>Hello,<h2> to complete your registration click  <a href="' + (
                        os.environ.get("HEROKU_URL") or localhost_url) + '/activate/' + str(
                    curr_user.id) + '"> here </a>.'
            )
            try:
                sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
                response = sg.send(message)
            except Exception as e:
                print(e)
            return redirect('/')
    else:
        return render_template('registry_form.html', title='Register', form=form)


@app.route('/', methods=['GET', 'POST'])
def get_recipe():
    ingredients_searched = []
    chip_ingredients = []
    user_recipes = []
    suggestions_as_json = {"searches": ingredients_searched}
    chip_ingredients_as_json = {"chipIngredients": chip_ingredients}
    user_recipes_as_json = {"userRecipes": user_recipes}
    if request.method == 'POST':
        search_suggestions = select(prod for prod in SearchSuggestion).order_by(lambda prod: desc(prod.id))[:5]
        for entry in search_suggestions:
            ingredients_searched.append(entry.ingredient)
        suggestions_as_json = {"searches": ingredients_searched}

        ing_suggestions = select(prod for prod in SearchSuggestion)#####  IngredientChip
        for entry in ing_suggestions:
            chip_ingredients.append(entry)
        chip_ingredients_as_json = {"chipIngredients": chip_ingredients}
        ingredients = ",".join(map(lambda db_entry: db_entry.ingredient, chip_ingredients))
        print ("Ingredients ",ingredients)
        recipes = UserCreatedRecipe.select(
            lambda recipe1: ingredients in recipe1.ingredients) # if ingredients in userRecipe.ingredients
        print ("Recipes",recipes)
        for recipe_from_user in recipes:
            print (recipe_from_user.name)
            user_recipes.append({"name":recipe_from_user.name,"ingredients":recipe_from_user.ingredients,
                                 "instructions":recipe_from_user.instructions,
                                 "user_recipe_id": recipe_from_user.id})
        user_recipes_as_json = {"userRecipes": user_recipes}
        print(user_recipes_as_json)
        content = requests.get(
            "https://api.spoonacular.com/recipes/findByIngredients?ingredients=" +
            convert_input(ingredients) +
            "&apiKey=" + API_KEY)
        json_response = json.loads(content.text)
        return render_template("recipes_list.html", ans=json_response, searchHistory=suggestions_as_json,
                               chipIngredients=chip_ingredients_as_json, userRecipes=user_recipes_as_json['userRecipes'])
    else:
        delete(ingredient for ingredient in IngredientChip)
        return render_template("recipes_list.html", searchHistory=suggestions_as_json,
                               chipIngredients=chip_ingredients_as_json, userRecipes=user_recipes_as_json['userRecipes'])


login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
@db_session
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == '' or password == '':
            flash("Enter a name and password")
            return redirect('/')
        possible_user = User.get(login=email)
        if not possible_user:
            flash('Wrong username')
            return redirect('/')
        if verify_password(possible_user.password, password) and possible_user.is_active is True:
            print("Logged in")
            set_current_user(possible_user)
            login_user(possible_user)
            return redirect('/')
        flash('Wrong password or account not confirmed')
        return redirect('/')
    else:
        return render_template('base_template.html')



@db_session
@app.route('/userRecipe', methods=['GET', 'POST'])
def add_user_recipe():
    form = UserRecipeForm()
    if form.validate_on_submit():
        if request.method == 'POST':
            name = request.form['name']
            ingredients = request.form['ingredients']
            instructions = request.form['instructions']
            UserCreatedRecipe(name=name, ingredients=ingredients, instructions=instructions, user=current_user)
            commit()
        return redirect('/')
    else:
        return render_template('user_recipe.html', title='Add your own recipe', form=form)


@app.route('/activate/<id>', methods=['GET', 'POST'])
def activate(id):
    with db_session:
        user = User.get(id=id)
        if user:
            user.is_active = True
            commit()
            print("Logged in")
            login_user(user)
            return redirect('/')

# @db_session
# @app.route('/autocomplete/<inp>', methods=['GET'])
# def autocomplete(inp):
#     ingredients = ["avocado", "apple", "allspice", "almonds", "aspargus", "aubergine", "arugula", "ananas",
#     "butter", "bread", "beef", "baking soda", "bell peper", "basil", "brown sugar", "broccoli", "banana",
#     "cinnamon", "carrot", "chicken", "cream", "cheese", "cauliflower",
#     "dijon", "dill", "dark chocolate", "dry mustard",
#     "egg", "entrecote", "egg yolk", "eggplant",
#     "flour", "fusilli", "farfalle",
#     "garlic", "ginger", "ground beef", "green pepper", "ground meat",
#     "honey", "heavy cream", "hot pepper sauce", "hot sauce",
#     "ice", "ice cream", "italian herbs",
#     "jalapeno", "jam",
#     "ketchup", "kale", "kiwi", "kosher salt",
#     "lemon", "lime", "light cream", "lettuce", "lentils", "leek",
#     "mayonnaise", "mustard", "meat", "milk", "mushrooms",
#     "nutmeg", "noodles", "nutella",
#     "olive oil", "onion", "olives", "oregano", "orange",
#     "pear", "peach", "parmesan", "potatoes", "pineapple",
#     "quinoa", "red lentils", "red pepper", "romaine lettuce",
#     "sugar", "sour cream", "soy sauce",
#     "tomatoes", "thyme", "tomato sauce", "tuna",
#     "vegetable oil", "vanilla", "vodka", "vinegar", "vegetable broth",
#     "wheat", "walnut", "white wine", "whipped cream", "worcestershire sauce",
#     "yoghurt", "yeast", "zuchinni"]
#     user_recipes = select(recipe for recipe in UserCreatedRecipe)
#     for recipe in user_recipes:
#         ingredients.extend(map(lambda st: st.strip(), map(lambda s: str(s), recipe.ingredients.split(','))))
#         filtered=filter(lambda ing: ing.startswith(inp),set(ingredients))
#     return make_response({"listaing":filtered}, 200)



# @app.route('/', methods=['GET', 'POST'])
# def get_recipe():
#     ingredients_searched = []
#     chip_ingredients = []
#     suggestions_as_json = {"searches": ingredients_searched}
#     chip_ingredients_as_json = {"chipIngredients": chip_ingredients}
#     if request.method == 'POST':
#         search_suggestions = select(prod for prod in SearchSuggestion).order_by(lambda prod: desc(prod.id))[:5]
#         print("search_suggestions",search_suggestions )
#         for entry in search_suggestions:
#             ingredients_searched.append(entry.ingredient)
#         print("ingredients_searched :" ,ingredients_searched)    
#         suggestions_as_json = {"searches": ingredients_searched}


#         ing_suggestions = select(prod for prod in SearchSuggestion)
#         print(ing_suggestions)
#         for entry in ing_suggestions:
#             chip_ingredients.append(entry)
#             print(entry)
#         chip_ingredients_as_json = {"chipIngredients": chip_ingredients}

#         ingredients = ",".join(map(lambda db_entry: db_entry.ingredient, chip_ingredients))
#         print(ingredients)
#         content = requests.get(
#             "https://api.spoonacular.com/recipes/findByIngredients?ingredients=" +
#             convert_input(ingredients) +
#             "&apiKey=" + API_KEY)
#         json_response = json.loads(content.text)
#         print(json_response)
#         return render_template("recipes_list.html", ans=json_response, searchHistory=suggestions_as_json,
#                                chipIngredients=chip_ingredients_as_json) if json_response != [] else render_template(
#             "recipes_list.html", ans="", searchHistory=suggestions_as_json, chipIngredients=chip_ingredients_as_json)
#     else:
#         delete(ingredient for ingredient in IngredientChip)
#         return render_template("recipes_list.html", searchHistory=suggestions_as_json,
#                                chipIngredients=chip_ingredients_as_json)





# @app.route('/', methods=['GET', 'POST'])
# def get_recipe():
#     ingredients_searched = []
#     suggestions_as_json = {"searches": ingredients_searched}
#     if request.method == 'POST':
#         ingredients = "".join(request.form['restaurant_name'].split()).split(",")
#         with db_session:
#             [SearchSuggestion(ingredient=suggestion) for suggestion in ingredients]

#         search_suggestions = select(prod for prod in SearchSuggestion).order_by(lambda prod: desc(prod.id))[:5]
#         for entry in search_suggestions:
#             ingredients_searched.append(entry.ingredient)
#         suggestions_as_json = {"searches": ingredients_searched}

#         content = requests.get(
#             "https://api.spoonacular.com/recipes/findByIngredients?ingredients=" +
#             convert_input(request.form['restaurant_name']) +
#             "&apiKey=" + API_KEY)
#         json_response = json.loads(content.text)
#         print(json_response)
#     #     return render_template("restaurant_list.html", response=json_response,searchHistory = suggestions_as_json) if json_response != [] else render_template(
#     #         "restaurant_list.html", response="",searchHistory=suggestions_as_json)
#     # else:
#     #     return render_template("restaurant_list.html",searchHistory=suggestions_as_json)        

#         return render_template("recipes_list.html", ans = json_response, searchHistory = suggestions_as_json) if json_response != [] else render_template("restaurant_list.html",ans="",searchHistory=suggestions_as_json)
#     else:
#         return render_template("recipes_list.html",searchHistory=suggestions_as_json)





@app.route('/recipe/<recipe_id>', methods=['GET'])
def recipe(recipe_id):
    response = requests.get("https://api.spoonacular.com/recipes/informationBulk?ids="+recipe_id+"&includeNutrition=true&apiKey="+API_KEY)
    # print(recipe_id)
    return make_response(render_template("recipe_details.html", recipe_id=json.loads(response.text)), 200)

#if __main__ = '__name__':