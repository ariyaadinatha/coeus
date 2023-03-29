from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

def create():
    if request.method == "POST":
        
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if error is not None:
            flash(error)
        else:
            db = get_db()
            # SQL injection vuln
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            )

            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")