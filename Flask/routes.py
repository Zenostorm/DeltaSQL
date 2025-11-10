from flask import Flask, render_template, request, abort, session
from math import ceil, floor
import sqlite3
import routes_content
import os
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

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
    current_message = session.pop("message", "")

    # if user is already logged in, return to home page
    if session.get("admin"):
        return app.redirect("/")

    return render_template("login.html",
                           message=current_message,
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
        session["message"] = routes_content.login_failure
        return app.redirect("/login")

    if len(username) > routes_content.user_max_length:
        session["message"] = routes_content.user_too_long
        return app.redirect("/login")

    if len(password) > routes_content.pass_max_length:
        session["message"] = routes_content.pass_too_long
        return app.redirect("/login")

    cur.execute("SELECT id, username FROM users")
    userdata = cur.fetchall()
    for user in userdata:  # check if user exists under inputted username
        if username == user[1]:
            success = True
            userid = user[0]
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
            session["message"] = routes_content.login_success
            success = True

    if not success:
        session["admin"] = False  # ensure admin session is false
        session["message"] = routes_content.login_failure
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
        categories = ["generic"]  # if there's no "types", set a generic category

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
    for helmet in range(len(helmets)):
        # if penetration more than protection, use damage without calculation
        if results[5] < helmets[helmet][0]:
            helmet_ballistics[helmets[helmet][1]] = (
                floor(2 * results[4] * results[5] / helmets[helmet][0]),
                helmets[helmet][2],
                ceil(50 / floor(results[4] * results[5] / helmets[helmet][0])),
                helmets[helmet][3])
        else:
            helmet_ballistics[helmets[helmet][1]] = (
                2 * results[4],
                helmets[helmet][2],
                ceil(50 / (results[4])),
                helmets[helmet][3])

    # pull protection from visors
    cur.execute('SELECT ballistic, name, image, id FROM visors')
    visors = cur.fetchall()

    # calculate damage against visors
    for visor in range(len(visors)):
        if results[5] < visors[visor][0]:
            visor_ballistics[visors[visor][1]] = (
                floor(2 * results[4] * results[5] / visors[visor][0]),
                visors[visor][2],
                ceil(50 / floor(results[4] * results[5] / visors[visor][0])),
                visors[visor][3])
        else:
            visor_ballistics[visors[visor][1]] = (
                2 * results[4], visors[visor][2],
                ceil(50 / results[4]),
                visors[visor][3])

    # pull protection from rigs
    cur = conn.cursor()
    cur.execute('SELECT ballistic, name, image, id FROM chest_rigs')
    rigs = cur.fetchall()

    # calculate damage against rigs
    for rig in range(len(rigs)):
        if results[5] < rigs[rig][0]:
            rig_ballistics[rigs[rig][1]] = (
                floor(results[4] * results[5] / rigs[rig][0]),
                rigs[rig][2],
                ceil(100 / floor(results[4] * results[5] / rigs[rig][0])),
                rigs[rig][3])
        else:
            rig_ballistics[rigs[rig][1]] = (
                results[4], rigs[rig][2],
                ceil(100 / results[4]),
                rigs[rig][3])

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
    for ammo in range(len(ammunition)):
        if ammunition[ammo][1] < results[4]:
            ballistics[ammunition[ammo][2]] = (
                floor(2 * ammunition[ammo][0] * ammunition[ammo][1] / results[4]),
                ammunition[ammo][3],
                ceil(50 / floor(ammunition[ammo][0] * ammunition[ammo][1] / results[4])),
                ammunition[ammo][4])
        else:  # if penetration > protection, store damage without calculation
            ballistics[ammunition[ammo][2]] = (
                int(2 * ammunition[ammo][0]),
                ammunition[ammo][3],
                ceil(50 / ammunition[ammo][0]),
                ammunition[ammo][4])

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
    for ammo in range(len(ammunition)):
        if ammunition[ammo][1] < results[4]:
            ballistics[ammunition[ammo][2]] = (
                floor(ammunition[ammo][0] * ammunition[ammo][1] / results[4]),
                ammunition[ammo][3],
                ceil(100 / floor(ammunition[ammo][0] * ammunition[ammo][1] / results[4])),
                ammunition[ammo][4])
        else:  # if penetration > protection, store damage without calculation
            ballistics[ammunition[ammo][2]] = (
                int(ammunition[ammo][0]),
                ammunition[ammo][3],
                ceil(100 / ammunition[ammo][0]),
                ammunition[ammo][4])

    conn.close()
    return render_template('detail/rig.html',
                           rig=results,
                           ammunition=ammunition,
                           ballistics=ballistics,
                           title=results[1])


@app.route("/visor/<int:id>")  # route for face shields/visors
def visor(id):
    ballistics = {}

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
    for ammo in range(len(ammunition)):
        if ammunition[ammo][1] < results[4]:
            ballistics[ammunition[ammo][2]] = (
                floor(2 * ammunition[ammo][0] * ammunition[ammo][1] / results[4]),
                ammunition[ammo][3],
                ceil(50 / floor(ammunition[ammo][0] * ammunition[ammo][1] / results[4])),
                ammunition[ammo][4])
        else:
            ballistics[ammunition[ammo][2]] = (
                int(2 * ammunition[ammo][0]),
                ammunition[ammo][3],
                ceil(50 / ammunition[ammo][0]),
                ammunition[ammo][4])

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
    for ammo in range(len(ammunition)):
        if ammunition[ammo][1] < results[4]:
            ballistics[ammunition[ammo][2]] = (
                floor(2 * ammunition[ammo][0] * ammunition[ammo][1] / results[4]),
                ammunition[ammo][3],
                ceil(50 / floor(ammunition[ammo][0] * ammunition[ammo][1] / results[4])),
                ammunition[ammo][4])
        else:  # if penetration > protection, store damage without calculation
            ballistics[ammunition[ammo][2]] = (
                int(2 * ammunition[ammo][0]),
                ammunition[ammo][3],
                ceil(50 / ammunition[ammo][0]),
                ammunition[ammo][4])

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
    stack_value = 0

    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM junk WHERE id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    # check if item can be stacked (stack limit is more than 1)
    if results[4] > 1:
        # calculate value per stack (value * stack limit)
        stack_value = results[3] * results[4]

    conn.close()
    return render_template('detail/junk.html',
                           item=results,
                           stack_value=stack_value,
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


@app.route("/badge/<int:id>")  # route for badges
def badge(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM badges WHERE id = ?", (id,))
    results = cur.fetchone()

    index_range_handler(results)  # check for list index out of range error

    conn.close()
    return render_template('detail/badge.html',
                           badge=results,
                           title=results[1])


# ADMIN
@app.route("/add_badge", methods=["GET", "POST"])  # add a new badge
def add_badge():
    if not session['admin']:  # check if user is an admin
        return app.redirect('/')

    # get error message then clear it
    current_message = session.pop("message", "")

    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    # Fetch next available ID
    cur.execute("SELECT MAX(id) FROM badges")
    last_id = cur.fetchone()[0]
    badge_id = (last_id or 0) + 1

    if request.method == "POST":
        # get form information
        name = request.form.get("name")
        type = request.form.get("type")
        # replace newlines with spaces for database formatting
        requirement = request.form.get("requirement").replace("\n", " ")
        description = request.form.get("description").replace("\n", " ")

        # check if user inputted all fields
        if not name or not type or not requirement or not description:
            session["message"] = routes_content.missing_info
            return app.redirect("/add_badge")

        # request image
        image_file = request.files.get("image")
        image_path = None

        # if no image was uploaded, stop user from adding item
        if not image_file:
            conn.close()
            session["message"] = routes_content.missing_info
            return app.redirect("/add_badge")

        # if unsupported filetype was uploaded, stop user from adding item
        if not allowed_file(image_file.filename):
            conn.close()
            session["message"] = routes_content.invalid_image
            return app.redirect("/add_badge")

        # save the image
        os.makedirs('Flask/static/images/game/badges', exist_ok=True)
        filename = secure_filename(image_file.filename)
        # save the file to disk
        image_file.save(os.path.join('Flask/static/images/game/badges', filename))
        # save only the filename to DB
        image_path = filename

        # insert new badge
        cur.execute(
            "INSERT INTO badges "
            "(id, "
            "name, "
            "type, "
            "requirement, "
            "description, "
            "image) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (badge_id,
             name,
             type,
             requirement,
             description,
             image_path)
        )
        conn.commit()
        badge_id = cur.lastrowid    # fetch the newly created ID

        conn.close()
        return app.redirect("/items/badges")

    return render_template("admin/add_badge.html",
                           badge_id=badge_id,
                           message=current_message,
                           title="Add Badge")


@app.route("/remove_badge", methods=["GET", "POST"])  # remove a badge
def remove_badge():
    if not session.get('admin'):  # check if user is an admin
        return app.redirect('/')

    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    if request.method == "POST":
        badge_id = request.form.get("badge_id")  # get badge ID from form
        if badge_id:
            badge_id = int(badge_id)

            # get image filename for deletion
            cur.execute("SELECT image FROM badges WHERE id = ?", (badge_id,))
            row = cur.fetchone()
            if row:  # check if there is an image, and delete it
                image_filename = row[0]
                if image_filename:
                    image_path = os.path.join('static/images/game/badges', image_filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)

                # delete badge from database
                cur.execute("DELETE FROM badges WHERE id = ?", (badge_id,))
                conn.commit()

        return app.redirect("/items/badges")

    # fetch all badges to display
    cur.execute("SELECT id, name, image FROM badges ORDER BY id")
    badges = cur.fetchall()
    print(badges)
    conn.close()

    return render_template("admin/remove_badge.html",
                           badges=badges,
                           title="Remove Badge")


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
