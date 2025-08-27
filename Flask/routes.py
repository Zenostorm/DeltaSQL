from flask import Flask, render_template, request
from math import ceil, floor
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


easter_egg_queries = ["contributors"]

app = Flask(__name__)
DATABASE = "delta.db"


# general routes
@app.route("/")
def home():
    return render_template('home.html', title="Home")


@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template('login.html')


@app.route("/faq", methods=["GET", "POST"])
def faq():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')
    questions_by_type = {}
    categories = ['General', 'Game']

    for category in categories:
        if search_query:
            cur.execute("SELECT id, question, type, answer FROM faq WHERE question LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', category))
        else:
            cur.execute("SELECT id, question, type, answer FROM faq WHERE type = ? ORDER BY id", (category,))
        questions_by_type[category] = cur.fetchall()

    conn.close()
    return render_template('faq.html',
                           info=questions_by_type,
                           title="FAQ")


@app.route("/contributors")
def contributors():
    return render_template('contributors.html')


# information routes
@app.route("/weapons", methods=["GET", "POST"])
def all_weapons():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("ballistics", "weapons", "weapon")
    # tags should include the image folder group (e.g ballistics),
    # the image folder,
    # then the topic link, in this order.
    # because list templates use these tags to fetch images and redirects.

    search_query = request.args.get('search', '')
    items_by_type = {}
    categories = []

    # fetch each unique instant of type within the table (e.g pistols, rifles)
    cur.execute("SELECT DISTINCT type FROM weapons")
    categories = cur.fetchall()
    categories = [", ".join(map(str, category)) for category in categories]

    # iterate through each category, and check for a search query.
    for category in categories:
        if search_query:
            cur.execute("SELECT id, name, type, description, image FROM weapons WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', category))
        else:
            cur.execute("SELECT id, name, type, description, image FROM weapons WHERE type = ? ORDER BY id", (category,))
        items_by_type[category] = cur.fetchall()

    # fetch topic description
    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("weapons",))
    description = cur.fetchone()

    print(items_by_type)

    conn.close()
    return render_template('complex_list.html',
                           grouped_items=items_by_type,
                           description=description,
                           tags=tags,
                           title="Weapons",
                           search=search_query,
                           easter_egg_queries=easter_egg_queries)


@app.route("/weapon/<int:id>")
def weapon(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT
    weapons.id,
    weapons.name,
    weapons.type,
    calibers.name AS caliber_name,
    weapons.fire_mode,
    weapons.RPM,
    weapons.durability,
    weapons.description,
    weapons.image,
    weapons.dmg_mult
FROM weapons
JOIN calibers ON weapons.caliber_id = calibers.id
WHERE weapons.id = ?''', (id,))
    results = cur.fetchall()[0]
    # fetch all information based on weapon's ID, and fetch caliber name from calibers table.

    # fetch compatible optics
    cur.execute('''SELECT id, name, image FROM attachments WHERE id IN (
                SELECT attachment_id FROM weapon_attachments WHERE weapon_id = ?) AND type = ?''', (id, "Optic"))
    optics = cur.fetchall()

    # fetch compatible muzzles
    cur.execute('''SELECT id, name, image FROM attachments WHERE id IN (
                SELECT attachment_id FROM weapon_attachments where weapon_id = ?) AND type = ?''', (id, "Muzzle"))
    muzzles = cur.fetchall()

    # fetch compatible extras
    cur.execute('''SELECT id, name, image FROM attachments WHERE id IN (
                SELECT attachment_id FROM weapon_attachments where weapon_id = ?) AND type = ?''', (id, "Extra"))
    extras = cur.fetchall()

    # fetch compatible  magazines
    cur.execute('''SELECT id, name, image FROM magazines WHERE id IN (
                SELECT magazine_id FROM weapon_magazines where weapon_id = ?)''', (id,))
    magazines = cur.fetchall()

    conn.close()
    return render_template('detail/weapon.html', weapon=results, optics=optics, muzzles=muzzles, extras=extras, magazines=magazines, title=results[1])


@app.route("/ammunition")
def ammunition():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("ballistics", "ammunition", "ammo")

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT id, name, description, image FROM ammunition WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT id, name, description, image FROM ammunition ORDER BY id')

    results = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("magazines",))

    description = cur.fetchone()

    conn.close()
    return render_template('simple_list.html',
                           params=results,
                           description=description,
                           tags=tags,
                           title="Ammunition",
                           search=search_query,
                           easter_egg_queries=easter_egg_queries)


@app.route("/ammo/<int:id>")
def ammo(id):
    helmet_ballistics = {}
    visor_ballistics = {}
    rig_ballistics = {}
    num = 0

    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT
    ammunition.id,
    calibers.name AS caliber_id,
    ammunition.name,
    ammunition.velocity,
    ammunition.damage,
    ammunition.penetration,
    ammunition.image,
    ammunition.description
FROM ammunition
JOIN calibers ON ammunition.caliber_id = calibers.id
WHERE ammunition.id = ?''', (id,))
    results = cur.fetchall()[0]

    cur.execute('''SELECT id, name, image FROM weapons WHERE id IN (
                SELECT weapon_id FROM weapon_ammo where ammo_id = ?)''', (id,))
    weapons = cur.fetchall()

    # pull protection from helmets
    cur = conn.cursor()
    cur.execute('SELECT ballistic, name, image, id FROM helmets')
    helmets = cur.fetchall()
    helmet_ballistics = {}
    visor_ballistics = {}
    rig_ballistics = {}

    # helmet damage function
    num = 0
    print(results[4])
    for helmet in helmets:
        if results[5] < helmets[num][0]:
            helmet_ballistics[helmets[num][1]] = floor(2 * results[4] * results[5] / helmets[num][0]), helmets[num][2], ceil(50 / floor(results[4] * results[5] / helmets[num][0])), helmets[num][3]
        else:
            helmet_ballistics[helmets[num][1]] = 2 * results[4], helmets[num][2], ceil(50 / (results[4])), helmets[num][3]
        num += 1

    # pull protection from visors
    cur = conn.cursor()
    cur.execute('SELECT ballistic, name, image, id FROM visors')
    visors = cur.fetchall()

    # visor damage function
    num = 0
    print(results[4])
    for visor in visors:
        if results[5] < visors[num][0]:
            visor_ballistics[visors[num][1]] = floor(2 * results[4] * results[5] / visors[num][0]), visors[num][2], ceil(50 / floor(results[4] * results[5] / visors[num][0])), visors[num][3]
        else:
            visor_ballistics[visors[num][1]] = 2 * results[4], visors[num][2], ceil(50 / results[4]), visors[num][3]
        num += 1

    # pull protection from rigs
    cur = conn.cursor()
    cur.execute('SELECT ballistic, name, image, id FROM chest_rigs')
    rigs = cur.fetchall()

    # rig damage function
    num = 0
    print(results[4])
    for rig in rigs:
        if results[5] < rigs[num][0]:
            rig_ballistics[rigs[num][1]] = floor(results[4] * results[5] / rigs[num][0]), rigs[num][2], ceil(100 / floor(results[4] * results[5] / rigs[num][0])), rigs[num][3]
        else:
            rig_ballistics[rigs[num][1]] = results[4], rigs[num][2], ceil(100 / results[4]), rigs[num][3]
        num += 1

    conn.close()
    return render_template('detail/ammo.html',
                           ammo=results,
                           weapons=weapons,
                           helmet_ballistics=helmet_ballistics,
                           visor_ballistics=visor_ballistics,
                           rig_ballistics=rig_ballistics,
                           title=results[1])


@app.route("/parts", methods=["GET", "POST"])
def all_parts():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("ballistics", "parts", "part")

    search_query = request.args.get('search', '')
    items_by_type = {}

    for category in ['Front', 'Handle', 'Stock']:
        if search_query:
            cur.execute("SELECT id, name, type, description, image FROM parts WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', category))
        else:
            cur.execute("SELECT id, name, type, description, image FROM parts WHERE type = ? ORDER BY id", (category,))
        items_by_type[category] = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("parts",))

    description = cur.fetchone()
    conn.close()
    return render_template('complex_list.html',
                           grouped_items=items_by_type,
                           description=description,
                           tags=tags,
                           title="Parts",
                           search=search_query,
                           easter_egg_queries=easter_egg_queries)


@app.route("/part/<int:id>")
def part(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM parts WHERE parts.id = ?''', (id,))
    results = cur.fetchall()[0]

    cur = conn.cursor()
    cur.execute('''SELECT id, name, image FROM weapons WHERE id IN (
                SELECT weapon_id FROM weapon_parts where part_id = ?)''', (id,))
    weapons = cur.fetchall()
    print(weapons)
    conn.close()
    return render_template('detail/part.html', part=results, weapons=weapons, title=results[1])


@app.route("/attachments", methods=["GET", "POST"])
def all_attachments():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("ballistics", "attachments", "attachment")

    search_query = request.args.get('search', '')
    items_by_type = {}

    for category in ['Optic', 'Muzzle', 'Extra']:
        if search_query:
            cur.execute("SELECT id, name, type, description, image FROM attachments WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', category))
        else:
            cur.execute("SELECT id, name, type, description, image FROM attachments WHERE type = ? ORDER BY id", (category,))
        items_by_type[category] = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("attachments",))

    description = cur.fetchone()
    conn.close()
    return render_template('complex_list.html',
                           grouped_items=items_by_type,
                           description=description,
                           tags=tags,
                           title="Attachments",
                           search=search_query,
                           easter_egg_queries=easter_egg_queries)

@app.route("/attachment/<int:id>")
def attachment(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM attachments WHERE attachments.id = ?''', (id,))
    results = cur.fetchall()[0]

    cur = conn.cursor()
    cur.execute('''SELECT id, name, image FROM weapons WHERE id IN (
                SELECT weapon_id FROM weapon_attachments where attachment_id = ?)''', (id,))
    weapons = cur.fetchall()
    conn.close()
    return render_template('detail/attachment.html', attachment=results, weapons=weapons, title=results[1])


@app.route("/magazines", methods=["GET", "POST"])
def all_magazines():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("ballistics", "magazines", "magazine")

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT id, name, description, image FROM magazines WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT id, name, description, image FROM magazines ORDER BY id')

    results = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("ammunition",))

    description = cur.fetchone()

    conn.close()
    return render_template('simple_list.html',
                           params=results,
                           description=description,
                           tags=tags,
                           title="Magazines",
                           search=search_query,
                           easter_egg_queries=easter_egg_queries)


@app.route("/magazine/<int:id>")
def magazine(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT
    magazines.id,
    magazines.name,
    calibers.name AS caliber_name,
    magazines.capacity,
    magazines.recoil_h,
    magazines.recoil_v,
    magazines.mobility,
    magazines.description,
    magazines.image
FROM magazines
JOIN calibers ON magazines.caliber_id = calibers.id
WHERE magazines.id = ?''', (id,))
    results = cur.fetchall()[0]

    cur = conn.cursor()
    cur.execute('''SELECT id, name, image FROM weapons WHERE id IN (
                SELECT weapon_id FROM weapon_magazines where magazine_id = ?)''', (id,))
    weapons = cur.fetchall()
    conn.close()
    return render_template('detail/magazine.html', magazine=results, weapons=weapons, title=results[1])


@app.route("/helmets")
def all_helmets():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("gear", "helmets", "helmet")

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT id, name, description, image FROM helmets WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT id, name, description, image FROM helmets ORDER BY id')

    results = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("helmets",))

    description = cur.fetchone()
    conn.close()
    return render_template('simple_list.html',
                           params=results,
                           description=description,
                           tags=tags,
                           title="Helmets",
                           search=search_query,
                           easter_egg_queries=easter_egg_queries)


@app.route("/helmet/<int:id>")
def helmet(id):
    ballistics = {}
    num = 0

    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM helmets WHERE helmets.id = ?''', (id,))
    results = cur.fetchall()[0]

    cur = conn.cursor()
    cur.execute('''SELECT id, name, image FROM visors WHERE id IN (
                SELECT visor_id FROM helmet_attachments where helmet_id = ?)''', (id,))
    attachments = cur.fetchall()

    # pull damage and piercing from ammunition
    cur = conn.cursor()
    cur.execute('SELECT damage, penetration, name, image, id FROM ammunition')
    ammunition = cur.fetchall()

    # calculate damage and add to a dictionary
    for ammo in ammunition:
        if ammunition[num][1] < results[4]:
            ballistics[ammunition[num][2]] = floor(2 * ammunition[num][0] * ammunition[num][1] / results[4]), ammunition[num][3], ceil(50 / floor(ammunition[num][0] * ammunition[num][1] / results[4])), ammunition[num][4]
        else:
            ballistics[ammunition[num][2]] = int(2 * ammunition[num][0]), ammunition[num][3], ceil(50 / ammunition[num][0]), ammunition[num][4]
        num += 1

    conn.close()
    return render_template('detail/helmet.html', helmet=results, attachments=attachments, ammunition=ammunition, ballistics=ballistics, title=results[1])


@app.route("/rigs")
def all_rigs():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("gear", "chest rigs", "rig")

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT id, name, description, image FROM chest_rigs WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT id, name, description, image FROM chest_rigs ORDER BY id')

    results = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("chest rigs",))

    description = cur.fetchone()
    conn.close()
    return render_template('simple_list.html', 
                           params=results, 
                           description=description, 
                           tags=tags,
                           title="Rigs", 
                           search=search_query, 
                           easter_egg_queries=easter_egg_queries)


@app.route("/rig/<int:id>")
def rig(id):
    ballistics = {}
    num = 0

    conn = sqlite3.connect('delta.db')
    # pull chest rig data
    cur = conn.cursor()
    cur.execute('''SELECT * FROM chest_rigs WHERE chest_rigs.id = ?''', (id,))
    results = cur.fetchall()[0]

    # pull damage and piercing from ammunition
    cur = conn.cursor()
    cur.execute('SELECT damage, penetration, name, image, id FROM ammunition')
    ammunition = cur.fetchall()

    # calculate damage and add to a dictionary
    for ammo in ammunition:
        if ammunition[num][1] < results[4]:
            ballistics[ammunition[num][2]] = floor(ammunition[num][0] * ammunition[num][1] / results[4]), ammunition[num][3], ceil(100 / floor(ammunition[num][0] * ammunition[num][1] / results[4])), ammunition[num][4]
        else:
            ballistics[ammunition[num][2]] = int(ammunition[num][0]), ammunition[num][3], ceil(100 / ammunition[num][0]), ammunition[num][4]
        num += 1

    conn.close()
    return render_template('detail/rig.html', rig=results, ammunition=ammunition, ballistics=ballistics, title=results[1])


@app.route("/visors")
def all_visors():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("gear", "visors", "visor")

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT id, name, description, image FROM visors WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT id, name, description, image FROM visors ORDER BY id')
    
    results = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("visors",))

    description = cur.fetchone()
    conn.close()
    return render_template('simple_list.html', 
                           params=results, 
                           description=description, 
                           tags=tags,
                           title="Visors", 
                           search=search_query, 
                           easter_egg_queries=easter_egg_queries)


@app.route("/visor/<int:id>")
def visor(id):
    ballistics = {}
    num = 0

    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM visors WHERE visors.id = ?''', (id,))
    results = cur.fetchall()[0]

    cur = conn.cursor()
    cur.execute('''SELECT id, name, image FROM helmets WHERE id IN (
                SELECT helmet_id FROM helmet_attachments where visor_id = ?)''', (id,))
    attachments = cur.fetchall()

    # pull damage and piercing from ammunition
    cur = conn.cursor()
    cur.execute('SELECT damage, penetration, name, image, id FROM ammunition')
    ammunition = cur.fetchall()

    # calculate damage and add to a dictionary
    for ammo in ammunition:
        if ammunition[num][1] < results[4]:
            ballistics[ammunition[num][2]] = floor(2 * ammunition[num][0] * ammunition[num][1] / results[4]), ammunition[num][3], ceil(50 / floor(ammunition[num][0] * ammunition[num][1] / results[4])), ammunition[num][4]
        else:
            ballistics[ammunition[num][2]] = int(2 * ammunition[num][0]), ammunition[num][3], ceil(50 / ammunition[num][0]), ammunition[num][4]
        num += 1

    conn.close()
    return render_template('detail/visor.html', visor=results, attachments=attachments, ammunition=ammunition, ballistics=ballistics, title=results[1])


@app.route("/leg armors")
def all_leg_armor():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("gear", "leg armor", "leg_armor")

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT id, name, description, image FROM leg_armor WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT id, name, description, image FROM leg_armor ORDER BY id')

    results = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("leg armor",))

    description = cur.fetchone()
    conn.close()
    return render_template('simple_list.html', 
                           params=results, 
                           description=description,
                           tags=tags,
                           title="Leg Armor", 
                           search=search_query, 
                           easter_egg_queries=easter_egg_queries)


@app.route("/leg armor/<int:id>")
def leg_armor(id):
    ballistics = {}
    num = 0

    conn = sqlite3.connect('delta.db')
    # pull leg armor data
    cur = conn.cursor()
    cur.execute('''SELECT * FROM leg_armor WHERE leg_armor.id = ?''', (id,))
    results = cur.fetchall()[0]

    # pull damage and piercing from ammunition
    cur = conn.cursor()
    cur.execute('SELECT damage, penetration, name, image, id FROM ammunition')
    ammunition = cur.fetchall()

    # calculate damage and add to a dictionary
    for ammo in ammunition:
        if ammunition[num][1] < results[4]:
            ballistics[ammunition[num][2]] = floor(0.25 * ammunition[num][0] * ammunition[num][1] / results[4]), ammunition[num][3], ceil(100 / floor(ammunition[num][0] * ammunition[num][1] / results[4])), ammunition[num][3]
        else:
            ballistics[ammunition[num][2]] = int(0.25 * ammunition[num][0]), ammunition[num][3], ceil(100 / ammunition[num][0]), ammunition[num][3]
        num += 1

    conn.close()
    return render_template('detail/leg_armor.html', armor=results, ammunition=ammunition, ballistics=ballistics, title=results[1])


@app.route("/wearables")
def all_wearables():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("gear", "wearables", "wearable")

    search_query = request.args.get('search', '')
    items_by_type = {}

    for category in ['Shirt', 'Pants', 'Mask', 'Gloves', 'Backpack']:
        if search_query:
            cur.execute("SELECT id, name, type, description, image FROM wearables WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', category))
        else:
            cur.execute("SELECT id, name, type, description, image FROM wearables WHERE type = ? ORDER BY id", (category,))
        items_by_type[category] = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("wearables",))

    description = cur.fetchone()
    conn.close()
    return render_template('complex_list.html', 
                           grouped_items=items_by_type, 
                           description=description,
                           tags=tags,
                           title="Wearables", 
                           search=search_query, 
                           easter_egg_queries=easter_egg_queries)


@app.route("/wearable/<int:id>")
def wearable(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM wearables WHERE id = ?''', (id,))
    results = cur.fetchall()[0]

    conn.close()
    return render_template('detail/wearable.html', wearable=results, title=results[1])


@app.route("/consumables")
def all_consumables():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("items", "consumables", "consumable")

    search_query = request.args.get('search', '')
    items_by_type = {}

    for category in ['Food', 'Drink', 'Medical', 'Stim']:
        if search_query:
            cur.execute("SELECT id, name, type, description, image FROM consumables WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', category))
        else:
            cur.execute("SELECT id, name, type, description, image FROM consumables WHERE type = ? ORDER BY id", (category,))
        items_by_type[category] = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("consumables",))

    description = cur.fetchone()
    conn.close()
    return render_template('complex_list.html', 
                           grouped_items=items_by_type, 
                           description=description,
                           tags=tags,
                           title="Consumables", 
                           search=search_query, 
                           easter_egg_queries=easter_egg_queries)


@app.route("/consumable/<int:id>")
def consumable(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM consumables WHERE id = ?''', (id,))
    results = cur.fetchall()[0]

    conn.close()
    return render_template('detail/consumable.html', consumable=results, title=results[1])


@app.route("/junks")
def all_junk():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("items", "junk", "junk")

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT id, name, description, image FROM junk WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute("SELECT id, name, description, image FROM junk ORDER BY id")
    results = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("junk",))

    description = cur.fetchone()
    conn.close()
    return render_template('simple_list.html', 
                           params=results, 
                           description=description,
                           tags=tags,
                           title="Junk", 
                           search=search_query, 
                           easter_egg_queries=easter_egg_queries)


@app.route("/junk/<int:id>")
def junk(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM junk WHERE id = ?''', (id,))
    results = cur.fetchall()[0]

    conn.close()
    return render_template('detail/junk.html', item=results, title=results[1])


@app.route("/containers")
def all_containers():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM containers WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute("SELECT * FROM containers ORDER BY id")
    results = cur.fetchall()
    conn.close()
    return render_template('containers.html', params=results, title="Containers", search=search_query, easter_egg_queries=easter_egg_queries)


@app.route("/keys")
def all_keys():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("items", "keys", "key")

    search_query = request.args.get('search', '')
    items_by_type = {}

    for category in ['Key', 'Card']:
        if search_query:
            cur.execute("SELECT id, name, type, description, image FROM keys WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', category))
        else:
            cur.execute("SELECT id, name, type, description, image FROM keys WHERE type = ? ORDER BY id", (category,))
        items_by_type[category] = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("keys",))

    description = cur.fetchone()
    conn.close()
    return render_template('complex_list.html', 
                           grouped_items=items_by_type, 
                           description=description,
                           tags=tags,
                           title="Keys", 
                           search=search_query, 
                           easter_egg_queries=easter_egg_queries)


@app.route("/key/<int:id>")
def key(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM keys WHERE id = ?''', (id,))
    results = cur.fetchall()[0]

    conn.close()
    return render_template('detail/key.html', key=results, title=results[1])


@app.route("/structures")
def all_landmarks():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    tags = ("locations", "structures", "structure")

    search_query = request.args.get('search', '')
    items_by_type = {}

    for category in ['Estonian Border', 'City-13']:
        if search_query:
            cur.execute("SELECT id, name, map, description, image FROM structures WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', category))
        else:
            cur.execute("SELECT id, name, map, description, image FROM structures WHERE type = ? ORDER BY id", (category,))
        items_by_type[category] = cur.fetchall()

    cur.execute("SELECT description FROM class_descriptions WHERE name = ?", ("structures",))

    description = cur.fetchone()
    conn.close()
    return render_template('locations_list.html', 
                           grouped_items=items_by_type, 
                           description=description,
                           tags=tags,
                           title="Structures",
                           search=search_query, 
                           easter_egg_queries=easter_egg_queries)


# routes for catching errors
@app.errorhandler(404)
def page_not_found(error):
    return render_template('error_page.html', error=404, issue="page not found"), 404


@app.errorhandler(400)
def bad_request(error):
    return render_template('error_page.html', error=400, issue="bad request"), 400


if __name__ == '__main__':
    app.run(debug=True)