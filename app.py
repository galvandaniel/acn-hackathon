import flask
import refinery

from user_profile import ALL_USER_PROFILES, UserProfile


APP_NAME: str = __name__

app: flask.Flask = flask.Flask(APP_NAME)


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    """
    Serve up the main webpage, "index.html".
    """
    selected_profile: UserProfile | None = None
    llm_response: str | None = None

    if flask.request.method == "POST":
        action: str | None = flask.request.form.get("action")

        # On profile selection, get profile by the profile button that was
        # submitted.
        # Otherwise, extract the selected profile hidden state.
        if action == "select_profile":
            profile_name: str = flask.request.form.get("profile")
            selected_profile: UserProfile = ALL_USER_PROFILES.get(profile_name)
        elif action == "submit_input":
            profile_name: str = flask.request.form.get("selected_profile")
            selected_profile: UserProfile = ALL_USER_PROFILES.get(profile_name)
            
            user_input: str | None = flask.request.form.get("user_input")
            llm_response: str | None = refinery.generate_response(user_input)
    
    return flask.render_template(
        "index.html", 
        all_profiles=ALL_USER_PROFILES, 
        selected_profile=selected_profile, 
        response=llm_response
        )

if __name__ == "__main__":
    app.run(debug=True)