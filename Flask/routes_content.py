# CONSTANTS
search_min_length = 3
search_max_length = 100

user_max_length = 30
pass_max_length = 100

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# MESSAGES
# >Login
login_failure = "Incorrect username or password"
user_too_long = "Username too long"
pass_too_long = "Password too long"
login_success = "Login successful"
# >Admin panel
no_image = "Please upload an image"
invalid_image = "Only png, jpg, and jpeg are supported"

# RESOURCE CONFIGS
# tags should include:
# 1. the grouped folder (e.g ballistics),
# 2. the image folder,
# 3. the redirect link, in this order
resource_configs = {
    "weapons": ("ballistics", "weapons", "weapon"),
    "ammunition": ("ballistics", "ammunition", "ammo"),
    "parts": ("ballistics", "parts", "part"),
    "attachments": ("ballistics", "attachments", "attachment"),
    "magazines": ("ballistics", "magazines", "magazine"),
    "helmets": ("gear", "helmets", "helmet"),
    "visors": ("gear", "visors", "visor"),
    "chest_rigs": ("gear", "chest_rigs", "rig"),
    "leg_armor": ("gear", "leg_armor", "leg_armor"),
    "wearables": ("gear", "wearables", "wearable"),
    "consumables": ("items", "consumables", "consumable"),
    "junk": ("items", "junk", "junk"),
    "keys": ("items", "keys", "key"),
    "badges": ("game", "badges", "badge")
    # extend dictionary when new resource is added
}
