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
import catalog_data

import pandas as pd

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
    # Reset all session variables once entering index page.
    flask.session["current_profile"] = flask.session.get("current_profile", ALL_USER_PROFILES["Ava Chen"].model_dump())
    flask.session["gave_feedback"] = False
    flask.session["recommendation"] = None
    flask.session["recommendation_index"] = {"tops": 0, "bottoms": 0}

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
        return flask.redirect(flask.url_for("suggestion"))
    return flask.render_template("index.html")


@app.route("/suggestion", methods=["GET", "POST"])
def suggestion() -> str:
    """
    Serve page giving an outfit suggestion, "suggestion.html"
    """

    # Use the re-encoded user profile to get outfit suggestions to show the user.
    num_prepared_recommendations: int = 5
    current_profile: UserProfile = UserProfile.model_validate(flask.session["current_profile"])

    # Only generate recommendations once when the user enters the page.
    recommendation: dict[str, list[int]] | None = flask.session.get("recommendation", None)
    if recommendation is None:
        recommendation = refinery.get_recommendation(current_profile, top_n=num_prepared_recommendations)
        flask.session["recommendation"] = recommendation

    # Get an index into the list of clothing item indices
    tops_recommended_index: int = flask.session["recommendation_index"]["tops"] % num_prepared_recommendations
    bottoms_recommended_index: int = flask.session["recommendation_index"]["bottoms"] % num_prepared_recommendations

    # Use the mapping to get an item index into the items dataframe.
    all_items: pd.DataFrame = catalog_data.get_downloaded_data()
    tops_item_index: int = recommendation["tops"][tops_recommended_index]
    bottoms_item_index: int = recommendation["bottoms"][bottoms_recommended_index]

    # Get recommendation data
    recommended_tops: pd.Series = all_items.loc[tops_item_index]
    recommended_bottoms: pd.Series = all_items.loc[bottoms_item_index]
    tops_filename: str = recommended_tops["product_id"] + ".jpg"
    bottoms_filename: str = recommended_bottoms["product_id"] + ".jpg"
    tops_link: str = recommended_tops["product_link"]
    bottoms_link: str = recommended_bottoms["product_link"]

    # Do clothing swapping logic on button press.
    if flask.request.method == "POST":
        swap_choice: str | None = flask.request.form.get("swap", None)
        do_new_outfit: bool = flask.request.form.get("new_outfit") == "yes"

        if swap_choice is not None:
            recommendation_index: dict[str, int] = flask.session["recommendation_index"]
            recommendation_index[swap_choice] += 1
            flask.session["recommendation_index"] = recommendation_index

        if do_new_outfit:
            recommendation_index: dict[str, int] = flask.session["recommendation_index"]
            recommendation_index["tops"] += 1
            recommendation_index["bottoms"] += 1
            flask.session["recommendation_index"] = recommendation_index
        return flask.redirect(flask.url_for("suggestion"))
    return flask.render_template("suggestion.html", 
                                 tops_filename=tops_filename, 
                                 bottoms_filename=bottoms_filename,
                                 tops_link=tops_link,
                                 bottoms_link=bottoms_link)

if __name__ == "__main__":
    app.run(debug=True)