from flask import Flask, render_template, request
from math import ceil, floor
import sqlite3, os


easter_egg_queries = ["contributors", "zeno", "pokubit", "immured", "aa battery"]

app = Flask(__name__)
DATABASE = "delta.db"


@app.route("/")
def home():
    return render_template('home.html', title="Home")


@app.route("/weapons", methods=["GET", "POST"])
def all_weapons():
    conn = sqlite3.connect('delta.db')
    # assault rifles
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM weapons WHERE name LIKE ? AND type = ? ORDER BY caliber_id", ('%' + search_query + '%', 'Assault Rifle'))
    else:
        cur.execute('SELECT * FROM weapons WHERE type = ? ORDER BY caliber_id', ('Assault Rifle', ))

    assault_rifles = cur.fetchall()

    # submachine guns
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM weapons WHERE name LIKE ? AND type = ? ORDER BY caliber_id", ('%' + search_query + '%', 'Submachine Gun'))
    else:
        cur.execute('SELECT * FROM weapons WHERE type = ? ORDER BY caliber_id', ('Submachine Gun', ))

    submachine_guns = cur.fetchall()
    
    # light machine guns
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM weapons WHERE name LIKE ? AND type = ? ORDER BY caliber_id", ('%' + search_query + '%', 'Light Machine Gun'))
    else:
        cur.execute('SELECT * FROM weapons WHERE type = ? ORDER BY caliber_id', ('Light Machine Gun', ))

    light_machine_guns = cur.fetchall()

    # sniper rifles
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM weapons WHERE name LIKE ? AND type = ? ORDER BY caliber_id", ('%' + search_query + '%', 'Sniper Rifle'))
    else:
        cur.execute('SELECT * FROM weapons WHERE type = ? ORDER BY caliber_id', ('Sniper Rifle', ))

    sniper_rifles = cur.fetchall()

    # assault carbines
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM weapons WHERE name LIKE ? AND type = ? ORDER BY caliber_id", ('%' + search_query + '%', 'Assault Carbine'))
    else:
        cur.execute('SELECT * FROM weapons WHERE type = ? ORDER BY caliber_id', ('Assault Carbine', ))

    assault_carbines = cur.fetchall()

    # battle rifles
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM weapons WHERE name LIKE ? AND type = ? ORDER BY caliber_id", ('%' + search_query + '%', 'Battle Rifle'))
    else:
        cur.execute('SELECT * FROM weapons WHERE type = ? ORDER BY caliber_id', ('Battle Rifle', ))

    battle_rifles = cur.fetchall()

    # shotguns
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM weapons WHERE name LIKE ? AND type = ? ORDER BY caliber_id", ('%' + search_query + '%', 'Shotgun'))
    else:
        cur.execute('SELECT * FROM weapons WHERE type = ? ORDER BY caliber_id', ('Shotgun', ))

    shotguns = cur.fetchall()

    # pistols
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM weapons WHERE name LIKE ? AND type = ? ORDER BY caliber_id", ('%' + search_query + '%', 'Pistol'))
    else:
        cur.execute('SELECT * FROM weapons WHERE type = ? ORDER BY caliber_id', ('Pistol', ))

    pistols = cur.fetchall()

    # rocket launchers
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM weapons WHERE name LIKE ? AND type = ? ORDER BY caliber_id", ('%' + search_query + '%', 'Rocket Launcher'))
    else:
        cur.execute('SELECT * FROM weapons WHERE type = ? ORDER BY caliber_id', ('Rocket Launcher', ))

    rocket_launchers = cur.fetchall()
    conn.close()
    return render_template('weapons.html', 
                           assault_rifles=assault_rifles, 
                           submachine_guns=submachine_guns, 
                           light_machine_guns=light_machine_guns, 
                           sniper_rifles=sniper_rifles, 
                           assault_carbines=assault_carbines, 
                           battle_rifles=battle_rifles, 
                           shotguns=shotguns, 
                           pistols=pistols, 
                           rocket_launchers=rocket_launchers, 
                           title="Weapons", search=search_query, easter_egg_queries=easter_egg_queries)

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
    weapons.long_desc
FROM weapons
JOIN calibers ON weapons.caliber_id = calibers.id
WHERE weapons.id = ?''', (id,))
    results = cur.fetchall()[0]

    # fetch optics
    cur = conn.cursor()
    cur.execute('''SELECT id, name, image FROM attachments WHERE id IN (
                SELECT attachment_id FROM weapon_optics where weapon_id = ?)''', (id,))
    optics = cur.fetchall()
    
    # fetch extras
    cur = conn.cursor()
    cur.execute('''SELECT id, name, image FROM attachments WHERE id IN (
                SELECT attachment_id FROM weapon_extras where weapon_id = ?)''', (id,))
    extras = cur.fetchall()

    # fetch magazines
    cur = conn.cursor()
    cur.execute('''SELECT id, name, image FROM magazines WHERE id IN (
                SELECT magazine_id FROM weapon_magazines where weapon_id = ?)''', (id,))
    magazines = cur.fetchall()

    conn.close()
    return render_template('weapon.html', weapon=results, optics=optics, extras=extras, magazines=magazines, title=results[1])
 
@app.route("/ammunition")
def ammunition():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM ammunition WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT * FROM ammunition ORDER BY id')

    results = cur.fetchall()
    conn.close()
    return render_template('ammunition.html', params=results, title="Ammunition", search=search_query, easter_egg_queries=easter_egg_queries)

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

    cur = conn.cursor()
    cur.execute('''SELECT id, name, image FROM weapons WHERE id IN (
                SELECT weapon_id FROM weapon_ammo where ammo_id = ?)''', (id,))
    weapons = cur.fetchall()

    # pull protection from helmets
    cur = conn.cursor()
    cur.execute('SELECT ballistic, name, image FROM helmets')
    helmets = cur.fetchall()

    # helmet damage function
    num = 0
    print(results[4])
    for helmet in helmets:
        if results[5] < helmets[num][0]:
            helmet_ballistics[helmets[num][1]] = floor(2 * results[4] * results[5] / helmets[num][0]), helmets[num][2], ceil(50 / floor(results[4] * results[5] / helmets[num][0]))
        else:
            helmet_ballistics[helmets[num][1]] = 2 * results[4], helmets[num][2], ceil(50 / (results[4]))
        num += 1
    
    # pull protection from visors
    cur = conn.cursor()
    cur.execute('SELECT ballistic, name, image FROM visors')
    visors = cur.fetchall()

    # visor damage function
    num = 0
    print(results[4])
    for visor in visors:
        if results[5] < visors[num][0]:
            visor_ballistics[visors[num][1]] = floor(2 * results[4] * results[5] / visors[num][0]), visors[num][2], ceil(50 / floor(results[4] * results[5] / visors[num][0]))
        else:
            visor_ballistics[visors[num][1]] = 2 * results[4], visors[num][2], ceil(50 / results[4])
        num += 1

    # pull protection from rigs
    cur = conn.cursor()
    cur.execute('SELECT ballistic, name, image FROM chest_rigs')
    rigs = cur.fetchall()

    # rig damage function
    num = 0
    print(results[4])
    for rig in rigs:
        if results[5] < rigs[num][0]:
            rig_ballistics[rigs[num][1]] = floor(results[4] * results[5] / rigs[num][0]), rigs[num][2], ceil(100 / floor(results[4] * results[5] / rigs[num][0]))
        else:
            rig_ballistics[rigs[num][1]] = results[4], rigs[num][2], ceil(100 / results[4])
        num += 1

    print(visor_ballistics)
    conn.close()
    return render_template('ammo.html', ammo=results, weapons=weapons, helmet_ballistics=helmet_ballistics, visor_ballistics=visor_ballistics, rig_ballistics=rig_ballistics, title=results[1])

@app.route("/parts", methods=["GET", "POST"])
def all_parts():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    # fronts
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM parts WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', 'Front'))
    else:
        cur.execute('SELECT * FROM parts WHERE type = ? ORDER BY id', ('Front', ))

    fronts = cur.fetchall()

    # handles
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM parts WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', 'Handle'))
    else:
        cur.execute('SELECT * FROM parts WHERE type = ? ORDER BY id', ('Handle', ))

    handles = cur.fetchall()
    
    # stocks
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM parts WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', 'Stock'))
    else:
        cur.execute('SELECT * FROM parts WHERE type = ? ORDER BY id', ('Stock', ))

    stocks = cur.fetchall()

    results = cur.fetchall()
    conn.close()
    return render_template('parts.html', fronts=fronts, handles=handles, stocks=stocks, title="Parts", search=search_query, easter_egg_queries=easter_egg_queries)

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
    return render_template('part.html', part=results, weapons=weapons, title=results[1])

@app.route("/attachments", methods=["GET", "POST"])
def all_attachments():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')
    # optics
    if search_query:
       cur.execute("SELECT * FROM attachments WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', 'Optic'))
    else:
        cur.execute("SELECT * FROM attachments WHERE type = ? ORDER BY id", ("Optic",))
    
    optics = cur.fetchall()

    # muzzles
    cur = conn.cursor()

    if search_query:
       cur.execute("SELECT * FROM attachments WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', 'Muzzle'))
    else:
        cur.execute("SELECT * FROM attachments WHERE type = ? ORDER BY id", ("Muzzle",))
    
    muzzles = cur.fetchall()

    # extras
    cur = conn.cursor()

    if search_query:
       cur.execute("SELECT * FROM attachments WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', 'Extra'))
    else:
        cur.execute("SELECT * FROM attachments WHERE type = ? ORDER BY id", ("Extra",))
    
    extras = cur.fetchall()
    conn.close()
    return render_template('attachments.html', optics=optics, muzzles=muzzles, extras=extras, title="Parts", search=search_query, easter_egg_queries=easter_egg_queries)

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
    return render_template('attachment.html', attachment=results, weapons=weapons, title=results[1])

@app.route("/magazines", methods=["GET", "POST"])
def all_magazines():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
       cur.execute("SELECT * FROM magazines WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT * FROM magazines ORDER BY id')
    
    results = cur.fetchall()
    conn.close()
    return render_template('magazines.html', params=results, title="Magazines", search=search_query, easter_egg_queries=easter_egg_queries)

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
                SELECT weapon_id FROM weapon_parts where part_id = ?)''', (id,))
    weapons = cur.fetchall()
    conn.close()
    return render_template('magazine.html', magazine=results, weapons=weapons, title=results[1])

@app.route("/helmets")
def all_helmets():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "delta.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
       cur.execute("SELECT * FROM helmets WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT * FROM helmets ORDER BY id')
    
    results = cur.fetchall()
    conn.close()
    return render_template('helmets.html', params=results, title="Helmets", search=search_query, easter_egg_queries=easter_egg_queries)

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
    cur.execute('SELECT damage, penetration, name, image FROM ammunition')
    ammunition = cur.fetchall()

    # damage function
    for ammo in ammunition:
        if ammunition[num][1] < results[4]:
            ballistics[ammunition[num][2]] = floor(2 * ammunition[num][0] * ammunition[num][1] / results[4]), ammunition[num][3], ceil(50 / floor(ammunition[num][0] * ammunition[num][1] / results[4])), 
        else:
            ballistics[ammunition[num][2]] = 2 * ammunition[num][0], ammunition[num][3], ceil(50 / ammunition[num][0])
        num += 1

    conn.close()
    return render_template('helmet.html', helmet=results, attachments=attachments, ammunition=ammunition, ballistics=ballistics, title=results[1])

@app.route("/rigs")
def all_rigs():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM chest_rigs WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT * FROM chest_rigs ORDER BY id')

    results = cur.fetchall()
    conn.close()
    return render_template('rigs.html', params=results, title="Chest rigs", search=search_query, easter_egg_queries=easter_egg_queries)

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
    cur.execute('SELECT damage, penetration, name, image FROM ammunition')
    ammunition = cur.fetchall()

    # damage function
    for ammo in ammunition:
        if ammunition[num][1] < results[4]:
            ballistics[ammunition[num][2]] = floor(ammunition[num][0] * ammunition[num][1] / results[4]), ammunition[num][3], ceil(100 / floor(ammunition[num][0] * ammunition[num][1] / results[4]))
        else:
            ballistics[ammunition[num][2]] = ammunition[num][0], ammunition[num][3], ceil(100 / ammunition[num][0])
        num += 1

    conn.close()
    return render_template('rig.html', rig=results, ammunition=ammunition, ballistics=ballistics, title=results[1])

@app.route("/visors")
def all_visors():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
       cur.execute("SELECT * FROM visors WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT * FROM visors ORDER BY id')
    
    results = cur.fetchall()
    conn.close()
    return render_template('visors.html', params=results, title="Visors", search=search_query, easter_egg_queries=easter_egg_queries)

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
    cur.execute('SELECT damage, penetration, name, image FROM ammunition')
    ammunition = cur.fetchall()

    # damage function
    for ammo in ammunition:
        if ammunition[num][1] < results[4]:
            ballistics[ammunition[num][2]] = floor(2 * ammunition[num][0] * ammunition[num][1] / results[4]), ammunition[num][3], ceil(50 / floor(ammunition[num][0] * ammunition[num][1] / results[4])), 
        else:
            ballistics[ammunition[num][2]] = 2 * ammunition[num][0], ammunition[num][3], ceil(50 / ammunition[num][0])
        num += 1

    conn.close()
    return render_template('visor.html', visor=results, attachments=attachments, ammunition=ammunition, ballistics=ballistics, title=results[1])

@app.route("/consumables")
def all_consumables():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')
    # foods
    if search_query:
       cur.execute("SELECT * FROM consumables WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', 'Food'))
    else:
        cur.execute("SELECT * FROM consumables WHERE type = ? ORDER BY id", ("Food",))
    
    foods = cur.fetchall()

    # drinks
    cur = conn.cursor()

    if search_query:
       cur.execute("SELECT * FROM consumables WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', 'Drink'))
    else:
        cur.execute("SELECT * FROM consumables WHERE type = ? ORDER BY id", ("Drink",))
    
    drinks = cur.fetchall()

    # medicals
    cur = conn.cursor()

    if search_query:
       cur.execute("SELECT * FROM consumables WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', 'Medical'))
    else:
        cur.execute("SELECT * FROM consumables WHERE type = ? ORDER BY id", ("Medical",))
    
    medicals = cur.fetchall()

    # stims
    cur = conn.cursor()

    if search_query:
       cur.execute("SELECT * FROM consumables WHERE name LIKE ? AND type = ? ORDER BY id", ('%' + search_query + '%', 'Stim'))
    else:
        cur.execute("SELECT * FROM consumables WHERE type = ? ORDER BY id", ("Stim",))
    
    stims = cur.fetchall()
    conn.close()
    return render_template('consumables.html', foods=foods, drinks=drinks, medicals=medicals, stims=stims, title="Consumables", search=search_query, easter_egg_queries=easter_egg_queries)

@app.route("/items")
def all_items():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
       cur.execute("SELECT * FROM junk WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%'))
    else:
        cur.execute("SELECT * FROM junk ORDER BY id")
    results = cur.fetchall()
    conn.close()
    return render_template('items.html', params=results, title="Junk", search=search_query, easter_egg_queries=easter_egg_queries)

@app.route("/containers")
def all_containers():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
       cur.execute("SELECT * FROM containers WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%'))
    else:
        cur.execute("SELECT * FROM containers ORDER BY id")
    results = cur.fetchall()
    conn.close()
    return render_template('containers.html', params=results, title="Lootable Containers", search=search_query, easter_egg_queries=easter_egg_queries)

if __name__ == '__main__':
    app.run(debug=True)
