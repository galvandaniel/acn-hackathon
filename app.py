import flask
import refinery

APP_NAME: str = __name__

app: flask.Flask = flask.Flask(APP_NAME)

@app.route("/", methods=["GET", "POST"])
def index() -> str:
    """
    Serve up the main webpage, "index.html".
    """
    llm_response: str | None = None

    if flask.request.method == "POST":
        user_input: str = flask.request.form["user_input"]
        llm_response: str | None = refinery.generate_response(user_input)
    return flask.render_template("index.html", response=llm_response)

if __name__ == "__main__":
    app.run(debug=True)