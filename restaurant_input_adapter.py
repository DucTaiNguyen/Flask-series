# def convert_input(ingredients):
#     ingredients = "".join(ingredients.split())
#     converted = ",".join(map((lambda s: "+" + s), ingredients.split(",")))[1:]
#     return converted

def convert_input(ingredients):
    ingredients = "".join(ingredients.split())
    return ",".join(map((lambda s: "+" + s), ingredients.split(",")))[1:]