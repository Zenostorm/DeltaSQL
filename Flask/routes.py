from flask import Flask, render_template
import sqlite3


app = Flask(__name__)
DATABASE = "delta.db"


@app.route("/")
def home():
    return render_template('home.html', title="Home")


@app.route("/weapons")
def all_weapons():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM weapons ORDER BY type')
    results = cur.fetchall()
    conn.close()
    return render_template('weapons.html', params=results, title="Weapons")

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
    cur.execute('SELECT * FROM ammunition ORDER BY id')
    results = cur.fetchall()
    conn.close()
    return render_template('ammunition.html', params=results, title="Ammunition")

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

@app.route("/armor")
def all_armor():
    conn = sqlite3.connect('delta.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM armor ORDER BY type')
    results = cur.fetchall()
    conn.close()
    return render_template('armor.html', params=results, title="Armor")

if __name__ == '__main__':
    app.run(debug=True)
