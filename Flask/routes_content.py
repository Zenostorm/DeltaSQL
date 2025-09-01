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
    "chest_rigs": ("gear", "chest rigs", "rig"),
    "leg_armor": ("gear", "leg armor", "leg armor"),
    "wearables": ("gear", "wearables", "wearable")
    # extend dictionary when new resource is added
}
