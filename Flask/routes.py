from flask import Flask, render_template, request, abort, session
from math import ceil, floor
import sqlite3
import routes_content
from werkzeug.security import check_password_hash

app = Flask(__name__)
DATABASE = "delta.db"
app.secret_key = "tGmesA3v77abYK3Y1UkUMlWJny6KAA"


# REQUESTS
def index_range_handler(results):
    if not results:
        abort(404)


def searchbar_length_handler(search, page):
    if len(search) < routes_content.search_min_length:
        abort(400)
    if len(search) > routes_content.search_max_length:
        abort(400)


# GENERAL ROUTES
@app.route("/")
def home():
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

    success = False  # success condition for login
    userid = 0
    username = request.form.get("username")  # request username
    password = request.form.get("password")  # request password

    if not username or not password:
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
    for user in userdata:
        if username == user[1]:
            success = True
            userid = user[0]
            print(userid)
            break
    if success:
        success = False
        cur.execute("SELECT passwordhash FROM users WHERE id = ?", (userid,))
        stored_hash = cur.fetchone()
        print(stored_hash)
        if check_password_hash(stored_hash[0], password):
            session["admin"] = True
            session["login_message"] = routes_content.login_success
            success = True

    if not success:
        session["admin"] = False
        session["login_message"] = routes_content.login_failure
    return app.redirect("/login")


@app.route("/logout")  # replaces admin session to false
def logout():
    session["admin"] = False

    # redirect to homepage
    return app.redirect("/")


@app.route("/contributors")  # list of people who helped me gather data
def contributors():
    # this route is found in the footer of the website
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    cur.execute("SELECT name, description, image FROM contributors")
    contributors = cur.fetchall()  # fetch all contributors

    conn.close()
    return render_template('contributors.html', contributors=contributors)


@app.route("/faq", methods=["GET", "POST"])
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
            if search_query:  # check for search, if none just pull everything
                cur.execute(
                    f"SELECT id, name, description, image, type "
                    f"FROM {table} "
                    "WHERE name LIKE ? AND type = ? "
                    "ORDER BY id",
                    ('%' + search_query + '%', category)
                )
            else:
                cur.execute(
                    f"SELECT id, name, description, image, type "
                    f"FROM {table} "
                    "WHERE type = ? "
                    "ORDER BY id",
                    (category,)
                )
            items_by_type[category] = cur.fetchall()
    else:  # if there are no categories
        if search_query:  # check for search, if none just pull everything
            cur.execute(
                f"SELECT id, name, description, image "
                f"FROM {table} "
                "WHERE name LIKE ? "
                "ORDER BY id",
                ('%' + search_query + '%',)
            )
        else:
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


@app.route("/weapon/<int:id>")
def weapon(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()  # and fetch caliber name from calibers table.
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
    results = cur.fetchone()

    # check for list index out of range error
    index_range_handler(results)

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


@app.route("/ammo/<int:id>")
def ammo(id):
    helmet_ballistics = {}
    visor_ballistics = {}
    rig_ballistics = {}
    num = 0

    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
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
    results = cur.fetchall()[0]

    cur.execute('''SELECT id, name, image FROM weapons WHERE id IN (
                SELECT weapon_id FROM weapon_ammo where ammo_id = ?)''', (id,))
    weapons = cur.fetchall()

    # pull protection from helmets
    cur = conn.cursor()
    cur.execute('SELECT ballistic, name, image, id FROM helmets')
    helmets = cur.fetchall()

    # calculate damage against helmets, then add to helmet_ballistics dictionary
    num = 0
    # iterate and add each helmet as a key
    for helmet in helmets:
        # if penetration is higher than protection, add raw damage without using calculation
        if results[5] < helmets[num][0]:
            helmet_ballistics[helmets[num][1]] = floor(2 * results[4] * results[5] / helmets[num][0]), helmets[num][2], ceil(50 / floor(results[4] * results[5] / helmets[num][0])), helmets[num][3]
        else:
            helmet_ballistics[helmets[num][1]] = 2 * results[4], helmets[num][2], ceil(50 / (results[4])), helmets[num][3]
        num += 1

    # pull protection from visors
    cur = conn.cursor()
    cur.execute('SELECT ballistic, name, image, id FROM visors')
    visors = cur.fetchall()

    # calculate damage against visors, then add to visor_ballistics dictionary
    num = 0
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


@app.route("/attachment/<int:id>")
def attachment(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM attachments WHERE attachments.id = ?''', (id,))
    results = cur.fetchall()[0]

    cur = conn.cursor()
    cur.execute("SELECT id, name, image "
                "FROM weapons WHERE id "
                "IN (SELECT weapon_id "
                "FROM weapon_attachments where attachment_id = ?)",
                (id,))
    weapons = cur.fetchall()
    conn.close()
    return render_template('detail/attachment.html', attachment=results, weapons=weapons, title=results[1])


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


@app.route("/leg_armor/<int:id>")
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
            ballistics[ammunition[num][2]] = floor(2 * ammunition[num][0] * ammunition[num][1] / results[4]), ammunition[num][3], ceil(50 / floor(ammunition[num][0] * ammunition[num][1] / results[4])), ammunition[num][4]
        else:
            ballistics[ammunition[num][2]] = int(2 * ammunition[num][0]), ammunition[num][3], ceil(50 / ammunition[num][0]), ammunition[num][4]
        num += 1

    conn.close()
    return render_template('detail/leg_armor.html', armor=results, ammunition=ammunition, ballistics=ballistics, title=results[1])


@app.route("/wearable/<int:id>")
def wearable(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM wearables WHERE id = ?''', (id,))
    results = cur.fetchall()[0]

    conn.close()
    return render_template('detail/wearable.html', wearable=results, title=results[1])


@app.route("/consumable/<int:id>")
def consumable(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM consumables WHERE id = ?''', (id,))
    results = cur.fetchall()[0]

    conn.close()
    return render_template('detail/consumable.html', consumable=results, title=results[1])


@app.route("/junk/<int:id>")
def junk(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM junk WHERE id = ?''', (id,))
    results = cur.fetchall()[0]

    conn.close()
    return render_template('detail/junk.html', item=results, title=results[1])


@app.route("/key/<int:id>")
def key(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM keys WHERE id = ?''', (id,))
    results = cur.fetchall()[0]

    conn.close()
    return render_template('detail/key.html', key=results, title=results[1])


# ADMIN ROUTES
@app.route("/admin-weapons", methods=["GET", "POST"])
def admin_weapons():
    search_query = request.args.get('search', '')
    return render_template('admin_weapons.html')


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
                           issue="Bad request")


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error_page.html',
                           error=500,
                           issue="Internal server error")


if __name__ == '__main__':
    app.run(debug=True)