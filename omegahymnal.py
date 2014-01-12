#!/usr/bin/env python
"""
OMEGA HYMNAL
Copyright 2014 Alan D Moore
www.alandmoore.com
Licensed to you under the terms of the GNU GPL v3.
See the included COPYING file for details.

OMEGA HYMNAL is a song lyrics display program designed for use
in informal settings such as small group meetings, jam sessions,
rehearsals, or anywhere else you might have wasted a lot of paper
printing up lyrics and chords for everyone.

It's written in python and requires the python flask framework
and your favorite standards-compliant web browser.

"""


from flask import Flask, g, render_template, request, json,  abort, Response
from includes.database import Database
import zlib

app = Flask(__name__)


@app.before_request
def before_request():
    g.db = Database(app.config.get("DATABASE_FILE"))

@app.route("/")
def index():
    songs = g.db.get_songlist()
    categories = g.db.get_categories()
    return render_template("main.jinja2", songs=songs, categories=categories)

@app.route("/song/<id>")
def song(id):
    song = g.db.get_song(int(id))
    return render_template("song.jinja2", song=song)

@app.route("/edit_song/<id>")
def edit_song(id):
    song = g.db.get_song(int(id))
    return render_template("edit_form.jinja2", song=song)

@app.route("/export", methods=["GET", "POST"])
def export():
    if request.method == "GET":
        categories = g.db.get_categories()
        return render_template("export_form.jinja2", categories=categories)
    else: #perform an export
        export = g.db.export_songs(request.form)
        #filedata = json.dumps(export).encode("utf-8")
        filedata = zlib.compress(json.dumps(export).encode("utf-8"))
        return Response(filedata, mimetype='application/octet-stream',
                        headers = {"Content-Disposition":"attachment;filename=export.omegahymnal"})

@app.route("/import", methods=["GET", "POST"])
def import_songs():
    if request.method == "GET":
        return render_template("import_form.jinja2")
    else:
        import_file = request.files["import_file"].stream.read()
        songs_imported = 0
        print(type(import_file))
        import_data = json.loads(zlib.decompress(import_file).decode("utf-8"))
        for song in import_data:
            g.db.save_imported_song(song)
            songs_imported += 1
        return "{} songs imported".format(songs_imported)
        
@app.route("/settings")
def settings():
    return render_template("base.jinja2")

@app.route("/post/<callback>", methods=["POST"])
def post(callback):
    callbacks = {
        "song" : g.db.save_posted_song,
        "delete" : g.db.delete_song
                 }
    if callback not in callbacks.keys():
        abort(403)
    else:
        result = callbacks.get(callback)(request.form)
        return result

@app.route("/json/<callback>")
def json_get(callback):
    callbacks = {
        "categories" : g.db.get_categories,
        "names"  : g.db.get_names,
        "export"  : g.db.export_songs
        }
    if callback not in callbacks.keys():
        abort(403)
    else:
        result = callbacks.get(callback)(**request.args)
        return json.dumps(result)

if __name__ == "__main__":
    app.debug = True
    app.config.from_pyfile("omegahymnal.conf", silent=True)
    app.run(
        host=app.config.get("HOST", 'localhost'),
        port=app.config.get("PORT", 5000)
            )
