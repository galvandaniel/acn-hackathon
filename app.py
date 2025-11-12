"""
Module for running a tech-demo Flask app demonstrating an agentic solution
for personalized clothing recommendations.

The application goes through two profile scenarios of online shopping, "Ava" and
"Leo", demonstrating an agent which is able to use unstructured customer data to 
give outfit recommendations based only on a database of clothing images.

"app.py" and "refinery.py" together form the Orchestrator agent which the user
interacts with via this front-end. 

The Orchestrator, on behalf of the user, uses the following models and utility agents:

- Image Understanding Agent (AI Refinery) to gain semantic information on the image database 
of currently available clothes.
- LLM (meta-llama/Llama-3.3-70b-Instruct) to understand the preferences of
a user profile.
- Embedding model (intfloat/e5-mistral-7b-instruct) to understand which clothes
best match the user's preferances based on the understanding gained from the 
LLM.
"""

import flask
import refinery

from user_profile import ALL_USER_PROFILES, UserProfile


APP_NAME: str = __name__

# Session data is encrypted with the secret key. Not important for simple demo.
app: flask.Flask = flask.Flask(APP_NAME)
app.secret_key = "dummy_key" 


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    """
    Serve the welcome webpage, "index.html".
    """
    # Default to "Ava Chen" profile upon opening page, no feedback given.
    flask.session["current_profile"] = flask.session.get("current_profile", ALL_USER_PROFILES["Ava Chen"].model_dump())
    flask.session["gave_feedback"] = False

    # Re-render with feedback box if user chose to give feedback.
    # If not, or if the user just sent feedback, go to /suggestion.
    if flask.request.method == "POST":
        gave_feedback: bool = flask.request.form.get("gave_feedback", None) == "yes" or flask.request.form.get("gave_feedback", None) == "submit"
        flask.session["gave_feedback"] = gave_feedback

        do_profile_switch: bool = flask.request.form.get("do_profile_switch") == "yes"

        # Only if "yes" was pressed do we rerender page to give option to send feedback.
        if flask.request.form.get("gave_feedback", None) == "yes":
            return flask.render_template("index.html")
        
        # On pressing profile switch button switch between Leo and Ava.
        if do_profile_switch:
            if flask.session["current_profile"]["name"] == "Ava Chen":
                flask.session["current_profile"] = ALL_USER_PROFILES["Leo Nguyen"].model_dump()
            else:
                flask.session["current_profile"] = ALL_USER_PROFILES["Ava Chen"].model_dump()
            return flask.render_template("index.html")
        # On unhandled POST request, go to next page.
        return flask.redirect(flask.url_for("suggestion"))
    return flask.render_template("index.html")


@app.route("/suggestion", methods=["GET", "POST"])
def suggestion() -> str:
    """
    Serve page giving an outfit suggestion, "suggestion.html"
    """
    # Use the re-encoded user profile to get outfit suggestions to show the user.
    current_profile: UserProfile = UserProfile.model_validate(flask.session["current_profile"])
    print("Profile:", current_profile)

    if flask.request.method == "POST":
        show_new_outfit: bool = flask.request.form.get("new_outfit", None) == "yes"

        if show_new_outfit:
            return flask.render_template("suggestion.html")
    return flask.render_template("suggestion.html", show_goodbye=False)

if __name__ == "__main__":
    app.run(debug=True)