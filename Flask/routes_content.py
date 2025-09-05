# constants
username_max_length = 30
password_max_length = 100


# define resources and their tags
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
    "keys": ("items", "keys", "key")
    # extend dictionary when new resource is added
}
