from flask import Flask, render_template, request, abort, session
from math import ceil, floor
import sqlite3
import routes_content
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
DATABASE = "delta.db"
app.secret_key = "tGmesA3v77abYK3Y1UkUMlWJny6KAA"


# REQUESTS
def index_range_handler(results):  # call for any dynamic route that uses ID
    if not results:
        abort(404)  # if index doesn't exist, abort(404) instead of crashing


def searchbar_length_handler(search):
    # failsafe if searchbar is tampered with inspect tool
    if len(search) < routes_content.search_min_length:
        abort(400)
    if len(search) > routes_content.search_max_length:
        abort(400)
    search = ""


def allowed_file(filename):  # check form for correct filetype
    return '.' in filename and filename.rsplit('.', 1)[1].lower() \
        in routes_content.ALLOWED_EXTENSIONS

# GENERAL ROUTES
@app.route("/")  # home route
def home():
    if "admin" not in session:  # instantiate admin session
        session["admin"] = False
    return render_template('home.html', title="Home")


@app.route("/login")  # page for the admin login
def login():
    # get login message then clear it
    current_login_message = session.pop("login_message", "")

    # if user is already logged in, return to home page
    if session.get("admin"):
        return app.redirect("/")

    return render_template("login.html",
                           login_message=current_login_message,
                           admin=session.get("admin", False),
                           user_max_length=routes_content.user_max_length,
                           pass_max_length=routes_content.pass_max_length,
                           title='login')


@app.route("/loginregister", methods=['GET', 'POST'])  # check inputted details
def loginregister():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    success = False  # success bool for login
    userid = 0
    username = request.form.get("username")  # request username
    password = request.form.get("password")  # request password

    if not username or not password:  # check if user inputted anything
        session["login_message"] = routes_content.login_failure
        return app.redirect("/login")

    if len(username) > routes_content.user_max_length:
        session["login_message"] = routes_content.user_too_long
        return app.redirect("/login")

    if len(password) > routes_content.pass_max_length:
        session["login_message"] = routes_content.pass_too_long
        return app.redirect("/login")

    cur.execute("SELECT id, username FROM users")
    userdata = cur.fetchall()
    for user in userdata:  # check if user exists under inputted username
        if username == user[1]:
            success = True
            userid = user[0]
            print(userid)
            break
    if success:
        success = False
        # fetch and store password hash
        cur.execute("SELECT passwordhash FROM users WHERE id = ?", (userid,))
        stored_hash = cur.fetchone()
        print(stored_hash)
        # compare hashes to confirm/deny login
        if check_password_hash(stored_hash[0], password):
            session["admin"] = True
            session["login_message"] = routes_content.login_success
            success = True

    if not success:
        session["admin"] = False  # ensure admin session is false
        session["login_message"] = routes_content.login_failure
    return app.redirect("/login")


@app.route("/logout")  # replaces admin session to false
def logout():
    session["admin"] = False
    return app.redirect("/")  # redirect to homepage


@app.route("/contributors")  # list of people who helped me gather data
def contributors():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    cur.execute("SELECT name, description, image FROM contributors")
    contributors = cur.fetchall()

    conn.close()
    return render_template('contributors.html', contributors=contributors)


@app.route("/faq", methods=["GET", "POST"])  # frequently asked questions page
def faq():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')
    questions_by_type = {}
    categories = ['General', 'Game']

    # iterate for each element in categories,
    # then add values to questions_by_type dictionary
    for category in categories:
        if search_query:  # check for search query, if none pull everything
            cur.execute("SELECT id, question, type, answer "
                        "FROM faq "
                        "WHERE question "
                        "LIKE ? "
                        "AND type = ?",
                        ('%' + search_query + '%', category))
        else:
            cur.execute("SELECT id, question, type, answer "
                        "FROM faq "
                        "WHERE type = ?",
                        (category,))
        questions_by_type[category] = cur.fetchall()

    conn.close()
    return render_template('faq.html',
                           info=questions_by_type,
                           title="FAQ")


# INFORMATION ROUTES
@app.route("/items/<string:resource>", methods=["GET", "POST"])
def item_category_list(resource):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    # get resource configs dictionary from route_content.py file
    resource_configs = routes_content.resource_configs

    # if topic isn't in configs, return 404 error
    if resource not in resource_configs:
        abort(404)

    # set table to the key of configs,
    # set tags to the values of configs
    table = f'"{resource}"'
    tags = resource_configs[resource]
    search_query = request.args.get('search', '')
    items_by_type = {}

    if search_query:  # check if search is valid length
        searchbar_length_handler(search_query)

    # fetch columns from table
    cur.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cur.fetchall()]  # row[1] = name of column

    # check for column named "type"
    if "type" in columns:
        cur.execute(f"SELECT DISTINCT type FROM {table}")
        categories = cur.fetchall()
        categories = [", ".join(map(str, category)) for category in categories]
    else:
        categories = ["generic"]  # if there's no "types", set a dummy category

    # iterate through each category
    # fetch information from tables
    if categories[0] != "generic":
        for category in categories:  # if there are categories
            if search_query:  # check for search
                cur.execute(
                    f"SELECT id, name, description, image, type "
                    f"FROM {table} "
                    "WHERE name LIKE ? AND type = ? "
                    "ORDER BY id",
                    ('%' + search_query + '%', category)
                )
            else:  # if no search just fetch all
                cur.execute(
                    f"SELECT id, name, description, image, type "
                    f"FROM {table} "
                    "WHERE type = ? "
                    "ORDER BY id",
                    (category,)
                )
            items_by_type[category] = cur.fetchall()
    else:  # if there are no categories
        if search_query:  # check for search
            cur.execute(
                f"SELECT id, name, description, image "
                f"FROM {table} "
                "WHERE name LIKE ? "
                "ORDER BY id",
                ('%' + search_query + '%',)
            )
        else:  # if no search just fetch all
            cur.execute(
                f"SELECT id, name, description, image "
                f"FROM {table} "
                "ORDER BY id"
            )
        items_by_type["generic"] = cur.fetchall()

    # fetch description for this topic
    cur.execute(
        "SELECT description "
        "FROM class_descriptions "
        "WHERE name = ? ",
        (resource,)
    )
    description = cur.fetchone()

    conn.close()

    return render_template(
        'item_list.html',
        grouped_items=items_by_type,
        description=description,
        tags=tags,
        title=resource.capitalize(),
        search=search_query
    )


@app.route("/weapon/<int:id>")  # route for guns
def weapon(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()  # fetch caliber name based on caliber id
    cur.execute("SELECT "
                "weapons.id, "
                "weapons.name, "
                "weapons.type, "
                "calibers.name AS caliber_name, "
                "weapons.fire_mode, "
                "weapons.RPM, "
                "weapons.durability, "
                "weapons.description, "
                "weapons.image, "
                "weapons.dmg_mult "
                "FROM weapons "
                "JOIN calibers ON weapons.caliber_id = calibers.id "
                "WHERE weapons.id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    # fetch compatible optics
    cur.execute("SELECT id, name, image FROM attachments "
                "WHERE id IN (SELECT attachment_id FROM weapon_attachments "
                "WHERE weapon_id = ?) "
                "AND type = ?", (id, "Optic"))
    optics = cur.fetchall()

    # fetch compatible muzzles
    cur.execute("SELECT id, name, image FROM attachments "
                "WHERE id IN (SELECT attachment_id FROM weapon_attachments "
                "WHERE weapon_id = ?) "
                "AND type = ?", (id, "Muzzle"))
    muzzles = cur.fetchall()

    # fetch compatible extras
    cur.execute("SELECT id, name, image FROM attachments "
                "WHERE id IN (SELECT attachment_id FROM weapon_attachments "
                "WHERE weapon_id = ?) "
                "AND type = ?", (id, "Extra"))
    extras = cur.fetchall()

    # fetch compatible  magazines
    cur.execute("SELECT id, name, image FROM magazines "
                "WHERE id IN (SELECT magazine_id FROM weapon_magazines "
                "WHERE weapon_id = ?)", (id,))
    magazines = cur.fetchall()

    conn.close()
    return render_template('detail/weapon.html',
                           weapon=results,
                           optics=optics,
                           muzzles=muzzles,
                           extras=extras,
                           magazines=magazines,
                           title=results[1])


@app.route("/ammo/<int:id>")  # route for ammunition
def ammo(id):
    helmet_ballistics = {}
    visor_ballistics = {}
    rig_ballistics = {}
    num = 0  # used for iterating through tables

    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()  # fetch caliber name based on caliber id
    cur.execute("SELECT ammunition.id, "
                "calibers.name AS caliber_id, "
                "ammunition.name, "
                "ammunition.velocity, "
                "ammunition.damage, "
                "ammunition.penetration, "
                "ammunition.image, "
                "ammunition.description "
                "FROM ammunition "
                "JOIN calibers ON ammunition.caliber_id = calibers.id "
                "WHERE ammunition.id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    # fetch compatible weapons
    cur.execute("SELECT id, name, image FROM weapons "
                "WHERE id IN (SELECT weapon_id FROM weapon_ammo "
                "WHERE ammo_id = ?)", (id,))
    weapons = cur.fetchall()

    # pull protection from helmets
    cur.execute('SELECT ballistic, name, image, id FROM helmets')
    helmets = cur.fetchall()

    # calculate damage against armors
    # true damage = damage * (penetration / protection)
    # store name of armor as key
    # store calculated damage, image, shots to kill, and armor ID
    num = 0
    for helmet in helmets:
        # if penetration more than protection, use damage without calculation
        if results[5] < helmets[num][0]:
            helmet_ballistics[helmets[num][1]] = (
                floor(2 * results[4] * results[5] / helmets[num][0]),
                helmets[num][2],
                ceil(50 / floor(results[4] * results[5] / helmets[num][0])),
                helmets[num][3])
        else:
            helmet_ballistics[helmets[num][1]] = (
                2 * results[4],
                helmets[num][2],
                ceil(50 / (results[4])),
                helmets[num][3])
        num += 1

    # pull protection from visors
    cur.execute('SELECT ballistic, name, image, id FROM visors')
    visors = cur.fetchall()

    # calculate damage against visors
    num = 0
    for visor in visors:
        if results[5] < visors[num][0]:
            visor_ballistics[visors[num][1]] = (
                floor(2 * results[4] * results[5] / visors[num][0]),
                visors[num][2],
                ceil(50 / floor(results[4] * results[5] / visors[num][0])),
                visors[num][3])
        else:
            visor_ballistics[visors[num][1]] = (
                2 * results[4], visors[num][2],
                ceil(50 / results[4]),
                visors[num][3])
        num += 1

    # pull protection from rigs
    cur = conn.cursor()
    cur.execute('SELECT ballistic, name, image, id FROM chest_rigs')
    rigs = cur.fetchall()

    # calculate damage against rigs
    num = 0
    for rig in rigs:
        if results[5] < rigs[num][0]:
            rig_ballistics[rigs[num][1]] = (
                floor(results[4] * results[5] / rigs[num][0]),
                rigs[num][2],
                ceil(100 / floor(results[4] * results[5] / rigs[num][0])),
                rigs[num][3])
        else:
            rig_ballistics[rigs[num][1]] = (
                results[4], rigs[num][2],
                ceil(100 / results[4]),
                rigs[num][3])
        num += 1

    conn.close()
    return render_template('detail/ammo.html',
                           ammo=results,
                           weapons=weapons,
                           helmet_ballistics=helmet_ballistics,
                           visor_ballistics=visor_ballistics,
                           rig_ballistics=rig_ballistics,
                           title=results[1])


@app.route("/part/<int:id>")  # route for gun parts
def part(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM parts WHERE parts.id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    # fetch compatible weapons
    cur.execute("SELECT id, name, image FROM weapons "
                "WHERE id IN (SELECT weapon_id FROM weapon_parts "
                "WHERE part_id = ?)", (id,))
    weapons = cur.fetchall()
    print(weapons)
    conn.close()

    return render_template('detail/part.html',
                           part=results,
                           weapons=weapons,
                           title=results[1])


@app.route("/attachment/<int:id>")  # route for attachments
def attachment(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM attachments WHERE attachments.id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    # fetch compatible weapons
    cur.execute("SELECT id, name, image "
                "FROM weapons WHERE id "
                "IN (SELECT weapon_id "
                "FROM weapon_attachments where attachment_id = ?)",
                (id,))
    weapons = cur.fetchall()
    conn.close()

    return render_template('detail/attachment.html',
                           attachment=results,
                           weapons=weapons,
                           title=results[1])


@app.route("/magazine/<int:id>")  # route for magazines
def magazine(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()  # fetch caliber name based on caliber id
    cur.execute("SELECT "
                "magazines.id, "
                "magazines.name, "
                "calibers.name AS caliber_name, "
                "magazines.capacity, "
                "magazines.recoil_h, "
                "magazines.recoil_v, "
                "magazines.mobility, "
                "magazines.description, "
                "magazines.image "
                "FROM magazines "
                "JOIN calibers ON magazines.caliber_id = calibers.id "
                "WHERE magazines.id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    # fetch compatible weapons
    cur.execute("SELECT id, name, image FROM weapons "
                "WHERE id IN (SELECT weapon_id FROM weapon_magazines "
                "WHERE magazine_id = ?)", (id,))
    weapons = cur.fetchall()
    conn.close()

    return render_template('detail/magazine.html',
                           magazine=results,
                           weapons=weapons,
                           title=results[1])


@app.route("/helmet/<int:id>")  # route for helmets
def helmet(id):
    ballistics = {}
    num = 0  # used to iterate through tables

    conn = sqlite3.connect('delta.db')
    # pull helmets data
    cur = conn.cursor()
    cur.execute("SELECT * FROM helmets WHERE helmets.id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    # fetch compatible visors
    cur.execute("SELECT id, name, image FROM visors "
                "WHERE id IN (SELECT visor_id FROM helmet_attachments "
                "WHERE helmet_id = ?)", (id,))
    attachments = cur.fetchall()

    # pull damage and piercing from ammunition
    cur.execute('SELECT damage, penetration, name, image, id FROM ammunition')
    ammunition = cur.fetchall()

    # calculate damage against different ammunition
    # true damage = damage * (penetration / protection)
    # store name of ammo as key
    # store calculated damage, image, shots to kill, and the ammo's ID
    for ammo in ammunition:
        if ammunition[num][1] < results[4]:
            ballistics[ammunition[num][2]] = (
                floor(2 * ammunition[num][0] * ammunition[num][1] / results[4]),
                ammunition[num][3],
                ceil(50 / floor(ammunition[num][0] * ammunition[num][1] / results[4])),
                ammunition[num][4])
        else:  # if penetration > protection, store damage without calculation
            ballistics[ammunition[num][2]] = (
                int(2 * ammunition[num][0]),
                ammunition[num][3],
                ceil(50 / ammunition[num][0]),
                ammunition[num][4])
        num += 1

    conn.close()
    return render_template('detail/helmet.html',
                           helmet=results,
                           attachments=attachments,
                           ammunition=ammunition,
                           ballistics=ballistics,
                           title=results[1])


@app.route("/rig/<int:id>")  # route for chest rigs
def rig(id):
    ballistics = {}
    num = 0

    conn = sqlite3.connect('delta.db')
    # pull chest rigs data
    cur = conn.cursor()
    cur.execute("SELECT * FROM chest_rigs WHERE chest_rigs.id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    # pull damage and piercing from ammunition
    cur.execute('SELECT damage, penetration, name, image, id FROM ammunition')
    ammunition = cur.fetchall()

    # calculate damage against different ammunition
    # true damage = damage * (penetration / protection)
    # store name of ammo as key
    # store calculated damage, image, shots to kill, and the ammo's ID
    for ammo in ammunition:
        if ammunition[num][1] < results[4]:
            ballistics[ammunition[num][2]] = (
                floor(ammunition[num][0] * ammunition[num][1] / results[4]),
                ammunition[num][3],
                ceil(100 / floor(ammunition[num][0] * ammunition[num][1] / results[4])),
                ammunition[num][4])
        else:  # if penetration > protection, store damage without calculation
            ballistics[ammunition[num][2]] = (
                int(ammunition[num][0]),
                ammunition[num][3],
                ceil(100 / ammunition[num][0]),
                ammunition[num][4])
        num += 1

    conn.close()
    return render_template('detail/rig.html',
                           rig=results,
                           ammunition=ammunition,
                           ballistics=ballistics,
                           title=results[1])


@app.route("/visor/<int:id>")  # route for face shields/visors
def visor(id):
    ballistics = {}
    num = 0  # used to iterate through tables

    conn = sqlite3.connect('delta.db')
    # pull visor data
    cur = conn.cursor()
    cur.execute("SELECT * FROM visors WHERE visors.id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    # fetch compatible helmets
    cur.execute("SELECT id, name, image FROM helmets "
                "WHERE id IN (SELECT helmet_id FROM helmet_attachments "
                "WHERE visor_id = ?)", (id,))
    attachments = cur.fetchall()

    # pull damage and piercing from ammunition
    cur = conn.cursor()
    cur.execute('SELECT damage, penetration, name, image, id FROM ammunition')
    ammunition = cur.fetchall()

    # calculate damage against different ammunition
    # true damage = damage * (penetration / protection)
    # store name of ammo as key
    # store calculated damage, image, shots to kill, and the ammo's ID
    for ammo in ammunition:
        if ammunition[num][1] < results[4]:
            ballistics[ammunition[num][2]] = (
                floor(2 * ammunition[num][0] * ammunition[num][1] / results[4]),
                ammunition[num][3],
                ceil(50 / floor(ammunition[num][0] * ammunition[num][1] / results[4])),
                ammunition[num][4])
        else:
            ballistics[ammunition[num][2]] = (
                int(2 * ammunition[num][0]),
                ammunition[num][3],
                ceil(50 / ammunition[num][0]),
                ammunition[num][4])
        num += 1

    conn.close()
    return render_template('detail/visor.html',
                           visor=results,
                           attachments=attachments,
                           ammunition=ammunition,
                           ballistics=ballistics,
                           title=results[1])


@app.route("/leg_armor/<int:id>")  # route for leg armor
def leg_armor(id):
    ballistics = {}
    num = 0

    conn = sqlite3.connect('delta.db')
    # pull leg armor data
    cur = conn.cursor()
    cur.execute("SELECT * FROM leg_armor WHERE leg_armor.id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    # pull damage and piercing from ammunition
    cur = conn.cursor()
    cur.execute('SELECT damage, penetration, name, image, id FROM ammunition')
    ammunition = cur.fetchall()

    # calculate damage against different ammunition
    # true damage = damage * (penetration / protection)
    # store name of ammo as key
    # store calculated damage, image, shots to kill, and the ammo's ID
    for ammo in ammunition:
        if ammunition[num][1] < results[4]:
            ballistics[ammunition[num][2]] = (
                floor(2 * ammunition[num][0] * ammunition[num][1] / results[4]),
                ammunition[num][3],
                ceil(50 / floor(ammunition[num][0] * ammunition[num][1] / results[4])),
                ammunition[num][4])
        else:  # if penetration > protection, store damage without calculation
            ballistics[ammunition[num][2]] = (
                int(2 * ammunition[num][0]),
                ammunition[num][3],
                ceil(50 / ammunition[num][0]),
                ammunition[num][4])
        num += 1

    conn.close()
    return render_template('detail/leg_armor.html',
                           armor=results,
                           ammunition=ammunition,
                           ballistics=ballistics,
                           title=results[1])


@app.route("/wearable/<int:id>")  # route for wearables
def wearable(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM wearables WHERE id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    conn.close()
    return render_template('detail/wearable.html',
                           wearable=results,
                           title=results[1])


@app.route("/consumable/<int:id>")  # route for consumables
def consumable(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM consumables WHERE id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    conn.close()
    return render_template('detail/consumable.html',
                           consumable=results,
                           title=results[1])


@app.route("/junk/<int:id>")  # route for junk
def junk(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM junk WHERE id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    conn.close()
    return render_template('detail/junk.html',
                           item=results,
                           title=results[1])


@app.route("/key/<int:id>")  # route for keys
def key(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM keys WHERE id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    conn.close()
    return render_template('detail/key.html',
                           key=results,
                           title=results[1])


@app.route("/admin/add-weapon", methods=["GET", "POST"])  # add weapons to db
def add_weapon():
    if not session.get("admin"):
        return app.redirect("/")

    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    # generate new weapon ID
    cur.execute("SELECT id FROM weapons")
    weapon_id = cur.fetchall()[-1][0] + 1

    if request.method == "POST":
        # request general data
        name = request.form.get("name")
        weapon_type = request.form.get("weapon_type")
        caliber_id = request.form.get("calibers")
        fire_mode = request.form.get("fire_mode")
        rpm = request.form.get("RPM")
        durability = request.form.get("durability")
        dmg_mult = request.form.get("dmg_mult")
        description = (request.form.get("description") or "").replace("\n", " ")

        # fetch checkbox results
        selected_parts = request.form.getlist("parts")
        selected_attachments = request.form.getlist("attachments")

        # request image
        image_file = request.files.get("image")
        image_path = None
        if image_file and allowed_file(image_file.filename):
            os.makedirs('static/images/ballistics/weapons', exist_ok=True)
            filename = secure_filename(image_file.filename)
            image_path = os.path.join('static/images/ballistics/weapons', filename)
            image_file.save(image_path)

        # insert new weapon
        cur.execute(
            "INSERT INTO weapons "
            "(name, "
            "type, "
            "caliber_id, "
            "fire_mode, "
            "rpm, "
            "durability, "
            "dmg_mult, "
            "description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name,
             weapon_type,
             caliber_id,
             fire_mode,
             rpm,
             durability,
             dmg_mult,
             description),
        )
        conn.commit()

        weapon_id = cur.lastrowid

        # insert new part IDs into bridging table
        for part_id in selected_parts:
            cur.execute(
                "INSERT INTO weapon_parts (weapon_id, part_id) "
                "VALUES (?, ?)",
                (weapon_id, part_id)
            )

        # insert new attachment IDs into bridging table
        for attachment_id in selected_attachments:
            cur.execute(
                "INSERT INTO weapon_attachments (weapon_id, attachment_id) "
                "VALUES (?, ?)",
                (weapon_id, attachment_id)
            )

        conn.close()
        return app.redirect("/items/weapons")

    # fetch weapon_types for dropdown
    cur.execute("SELECT type FROM weapon_types")
    weapon_types = [row[0] for row in cur.fetchall()]

    # fetch calibers for dropdown
    cur.execute("SELECT id, name FROM calibers")
    calibers = cur.fetchall()

    # fetch parts for dropdown
    cur.execute("SELECT id, name FROM parts")
    parts = cur.fetchall()

    # fetch parts for checkboxes
    cur.execute("SELECT id, name, type FROM parts")
    parts = cur.fetchall()

    # fetch attachments for checkboxes
    cur.execute("SELECT id, name, type FROM attachments")
    attachments = cur.fetchall()
    print(parts)

    return render_template("admin/add_weapon.html",
                           weapon_id=weapon_id,
                           weapon_types=weapon_types,
                           calibers=calibers,
                           parts=parts,
                           attachments=attachments,
                           title="")


# ERROR ROUTES
@app.errorhandler(404)
def page_not_found(error):
    return render_template('error_page.html',
                           error=404,
                           issue="Page not found")


@app.errorhandler(400)
def bad_request(error):
    return render_template('error_page.html',
                           error=400,
                           issue="Bad request, try a different search")


@app.errorhandler(414)
def url_too_long(error):
    return render_template('error_page.html',
                           error=414,
                           issue="URL too long")


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error_page.html',
                           error=500,
                           issue="Internal server error")


if __name__ == '__main__':
    app.run(debug=True)
