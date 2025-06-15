from flask import Flask, render_template, request
import sqlite3


easter_egg_queries = ["contributors", "zeno", "pokubit", "immured", "aa battery"]

app = Flask(__name__)
DATABASE = "delta.db"


@app.route("/")
def home():
    return render_template('home.html', title="Home")


@app.route("/weapons", methods=["GET", "POST"])
def all_weapons():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM weapons WHERE name LIKE ? ORDER BY type", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT * FROM weapons ORDER BY type')

    results = cur.fetchall()
    conn.close()
    return render_template('weapons.html', params=results, title="Weapons", search=search_query, easter_egg_queries=easter_egg_queries)


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
    conn.close()
    return render_template('weapon.html', weapon=results, title=results[1])
 
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
    conn.close()
    print(results)
    return render_template('ammo.html', ammo=results, title=results[1])

@app.route("/parts", methods=["GET", "POST"])
def all_parts():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
       cur.execute("SELECT * FROM parts WHERE name LIKE ? ORDER BY id", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT * FROM parts ORDER BY id')
    
    results = cur.fetchall()
    conn.close()
    return render_template('parts.html', params=results, title="Parts", search=search_query, easter_egg_queries=easter_egg_queries)

@app.route("/helmets")
def all_helmets():
    conn = sqlite3.connect('delta.db')
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
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM helmets WHERE helmets.id = ?''', (id,))
    results = cur.fetchall()[0]

    cur = conn.cursor()
    cur.execute('''SELECT id, name FROM visors WHERE id IN (
                SELECT visor_id FROM helmet_attachments where helmet_id = ?)''', (id,))
    attachments = cur.fetchall()
    print(attachments)
    conn.close()
    return render_template('helmet.html', helmet=results, attachments=attachments, title=results[1])

@app.route("/rigs")
def all_rigs():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if search_query:
        cur.execute("SELECT * FROM chest_rigs WHERE name LIKE ? ORDER BY type", ('%' + search_query + '%',))
    else:
        cur.execute('SELECT * FROM chest_rigs ORDER BY id')

    results = cur.fetchall()
    conn.close()
    return render_template('rigs.html', params=results, title="Chest rigs", search=search_query, easter_egg_queries=easter_egg_queries)

@app.route("/rig/<int:id>")
def rig(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM chest_rigs WHERE chest_rigs.id = ?''', (id,))
    results = cur.fetchall()[0]
    conn.close()
    return render_template('rig.html', rig=results, title=results[1])

@app.route("/visors")
def all_visors():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM visors ORDER BY id')
    results = cur.fetchall()
    conn.close()
    return render_template('visors.html', params=results, title="Visors")

@app.route("/visor/<int:id>")
def visor(id):
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('''SELECT * FROM visors WHERE visors.id = ?''', (id,))
    results = cur.fetchall()[0]

    cur = conn.cursor()
    cur.execute('''SELECT id, name FROM helmets WHERE id IN (
                SELECT helmet_id FROM helmet_attachments where visor_id = ?)''', (id,))
    attachments = cur.fetchall()
    print(attachments)
    conn.close()
    return render_template('visor.html', visor=results, attachments=attachments, title=results[1])

if __name__ == '__main__':
    app.run(debug=True)
