"""Flask frontend for the CSE 412 music library project (Phase 3).

Frontend-only scaffolding. Mock data lives in `mock_data.py`. Auth is a
session cookie backed by a hardcoded user list — wire to PostgreSQL later.
"""

import os, psycopg2

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import postgres.db_connection as db # database initialization script

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-do-not-use-in-prod")


@app.context_processor
def inject_user():
    return {"current_user": session.get("username")}


@app.route("/")
def home():
    return render_template(
        "home.html",
        releases=db.get_releases(),
        collections=db.get_user_collections(username=inject_user()["current_user"]),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        match = next(
            (u for u in db.get_users()
             if u["username"] == username and u["password"] == password),
            None,
        )
        if match:
            session["username"] = match["username"]
            flash(f"Welcome back, {match['username']}!", "success")
            return redirect(url_for("home"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif any(u["username"] == username for u in db.get_users()):
            flash("Username already taken.", "error")
        elif any(u["email"] == email for u in db.get_users()):
            flash("Email already taken.", "error")
        else:
            uid = db.query("""SELECT MAX(u_id) FROM users""")[0][0] + 1
            successful = db.insert("users", f"'{username}', '{email}', '{password}', '{uid}'")
            if(successful):
                col_success = _new_collection(uid)
                if(col_success == True):
                    session["username"] = username
                    flash(f"Account created. Welcome, {username}!", "success")
                    return redirect(url_for("home"))
                else:
                    flash("Error in account creation.", "error")
                    return redirect(url_for("register"))
            else:
                flash("Error in account creation.", "error")
                return redirect(url_for("register"))
    return render_template("register.html")


@app.route("/release/<int:release_id>")
def release_detail(release_id):
    release = db.get_releases_by_id().get(release_id)
    if release is None:
        flash("Release not found.", "error")
        return redirect(url_for("home"))
    collections = db.get_user_collections(username=inject_user()["current_user"]) or []
    return render_template("release.html", release=release, collections=collections)


@app.route("/collection/<int:c_id>")
def collection_detail(c_id):
    collection = db.get_collections_by_id().get(c_id)
    if collection is None:
        flash("Collection not found.", "error")
        return redirect(url_for("home"))
    releases = [
        db.get_releases_by_id()[rid]
        for rid in collection["release_ids"]
        if rid in db.get_releases_by_id()
    ]
    stats = {
        "total_tracks": sum(len(r["tracks"]) for r in releases),
        "formats": sorted({r["format"] for r in releases}),
        "genres": sorted({r["genre"] for r in releases}),
    }
    return render_template("collection.html", collection=collection,
                           releases=releases, stats=stats)


@app.route("/help")
def help():
    return render_template("help.html")

@app.route("/browse")
def browse():
    return render_template("browse.html", releases=db.get_releases())


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/release/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        contributors = request.form.get("contributors", "").strip()
        r_type = request.form.get("r_type", "")
        r_format = request.form.get("format", "")
        r_date = request.form.get("r_date", "")
        r_label = request.form.get("r_label", "").strip()
        cover = request.form.get("cover", "").strip()
        details = request.form.get("details", "").strip()
        
        if not title or not contributors or not r_type or not r_format or not r_date or not r_label:
            flash("All required fields must be filled out", "error")
            return render_template("add.html")

        good_insert = db.insert(
            "releases",
            f"'{title}', '{contributors}', '{r_type}', '{r_format}', '{r_date}', '{r_label}', '{cover}', '{details}' "
        )
        
        if good_insert:
            flash(f"Release '{title}' added to library!", "success")
            return redirect(url_for("home"))
        else:
            flash("Error adding release", "error")
            return render_template("add.html")
    return render_template("add.html")



def get_tracks(album):
    """ Searches the database for tracks off the given album. 
        Returns a dictionary containing those tracks, and a list of genres."""

    tracks = [] # list of dictionaries
    t_tbl = db.select(tbls="track", pred=f"r_title = '{album}'")
    genres_list = []

    for t in t_tbl:
        if t[5] not in genres_list:
            genres_list.append(t[5])

        tdict = {
            "t_num":    int( t[3] ),
            "title":    t[0],
            "duration": int( t[4] ),
            "genre":    t[5],
            "features": t[6],
        }
        tracks.append(tdict)
    
    # format genres list
    genres = ""
    genres_list.sort()
    for g in genres_list:
        if(genres_list[-1] == g):
            genres += g
        else:
            flash("Error adding release", "error")
            return render_template("add.html")
    return render_template("add.html")

@app.route("/release/<int:release_id>/delete", methods=["GET", "POST"])
def delete(release_id):
    release = db.get_releases_by_id().get(release_id)
    if release is None:
        flash("Release was not found", "error")
        return redirect(url_for("home"))
    
    if request.method == "POST":
        title = release["title"]
        contributors = release["contributors"]
        try:
            db._cur.execute(f"DELETE FROM releases WHERE title = '{title}' AND contributors = '{contributors}'")
            print(db._conn.commit())
            flash(f"Release '{title}' was deleted.", "success")
            return redirect(url_for("home"))
        except Exception as e:
            print(f"DELETE ERROR: {e}")
            flash(f"Error deleting release", "error")
            db._conn.rollback()
            return redirect(url_for("home"))
    return render_template("delete.html", release=release)

@app.route("/release/<int:release_id>/edit", methods=["GET", "POST"])
def edit(release_id):
    release = db.get_releases_by_id().get(release_id)
    if release is None:
        flash("Release was not found", "error")
        return redirect(url_for("home"))
    
    if request.method == "POST":
        org_title = release["title"]
        org_contributors = release["contributors"]
        
        title = request.form.get("title", "").strip()
        contributors = request.form.get("contributors", "").strip()
        r_type = request.form.get("r_type", "")
        r_format = request.form.get("format", "")
        r_date = request.form.get("r_date", "")
        r_label = request.form.get("r_label", "").strip()
        cover = request.form.get("cover", "").strip()
        details = request.form.get("details", "").strip()
        
        if not title or not contributors or not r_type or not r_format or not r_date or not r_label:
            flash("All required fields must be filled out", "error")
            return render_template("edit.html", release=release)
        
        try:
            db._cur.execute(
                f"UPDATE releases SET "
                f"title = '{title}', contributors = '{contributors}', "
                f"r_type = '{r_type}', format = '{r_format}', "
                f"r_date = '{r_date}', r_label = '{r_label}', "
                f"cover = '{cover}', details = '{details}' "
                f"WHERE title = '{org_title}' AND contributors = '{org_contributors}'" 
            )
            db._conn.commit()
            flash(f"Release '{title}' was updated.", "success")
            return redirect(url_for("home"))
        except Exception as e:
            print(f"UPDATE ERROR: {e}")
            flash("Error updating release", "error")
            db._conn.rollback()
            return redirect(url_for("home"))
    return render_template("edit.html", release = release)


@app.route("/release/<int:release_id>/add_to_collection", methods=["POST"])
def add_to_collection(release_id):
    if not session.get("username"):
        flash("Please log in to add to a collection.", "error")
        return redirect(url_for("login"))
    c_id = request.form.get("c_id", type=int)
    release = db.get_releases_by_id().get(release_id)
    if release is None or c_id is None:
        flash("Invalid request.", "error")
        return redirect(url_for("home"))
    success = db.add_release_to_collection(c_id, release["title"], release["contributors"])
    if success:
        flash(f"Added \"{release['title']}\" to collection.", "success")
    else:
        flash("Could not add — release may already be in that collection or has no group entry.", "error")
    return redirect(request.referrer or url_for("home"))


@app.route("/collection/new", methods=["POST"])
def new_collection():
    if not session.get("username"):
        flash("Please log in.", "error")
        return redirect(url_for("login"))
    uid_row = db.query(f"SELECT u_id FROM users WHERE username = '{session['username']}'")
    if not uid_row:
        flash("User not found.", "error")
        return redirect(url_for("home"))
    success = _new_collection(uid_row[0][0])
    if success:
        flash("New collection created!", "success")
    return redirect(url_for("home"))


@app.route("/collection/<int:c_id>/remove/<int:release_id>", methods=["POST"])
def remove_from_collection(c_id, release_id):
    if not session.get("username"):
        flash("Please log in.", "error")
        return redirect(url_for("login"))
    release = db.get_releases_by_id().get(release_id)
    if release is None:
        flash("Release not found.", "error")
        return redirect(url_for("collection_detail", c_id=c_id))
    success = db.remove_release_from_collection(c_id, release["title"], release["contributors"])
    if success:
        flash(f"Removed \"{release['title']}\" from collection.", "success")
    else:
        flash("Error removing release from collection.", "error")
    return redirect(url_for("collection_detail", c_id=c_id))


def _new_collection(uid):
    new_cid = db.query("SELECT MAX(c_id) FROM collection")[0][0] + 1
    try:
        db._cur.execute(f"INSERT INTO collection(c_id, u_id) VALUES ({new_cid}, {uid})")
        db._conn.commit()
        return True
    except:
        flash("Issue creating collection.", "error")
        db._conn.rollback()
        return False


if __name__ == "__main__":
    # macOS reserves port 5000 for AirPlay Receiver, so default to 5001.
    db.init_db()
    port = int(os.environ.get("FLASK_PORT", 5001))
    app.run(debug=True, port=port)
