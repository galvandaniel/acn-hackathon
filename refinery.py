"""
Backend logic of demo, responsible for interfacing with Accenture AI Refinery
API.
"""

import asyncio
import json
import os

import numpy as np
import pandas as pd
import catalog_data

# AI Refinery relevant imports.
import requests
from air import AIRefinery, DistillerClient, utils
from dotenv import load_dotenv
from user_profile import ALL_USER_PROFILES

# Type hint imports
from typing import AsyncGenerator
from air.types.chat import ChatCompletion
from air.types.distiller.client import DistillerIncomingMessage
from air.types.embeddings import CreateEmbeddingResponse
from user_profile import UserProfile


# API key loaded from .env file.
load_dotenv()
API_KEY: str | None = os.getenv("API_KEY")

# Orchestrator config files as pairs of "config.yaml", "project name".
CONFIG_FILES: list[tuple[str, str]] = [
    ("captioner.yaml", "captioner")
    ]

# Clients for interfacing w/ Accenture AI Refinery, must be initialized with
# setup_refinery().
AIR_CLIENT: AIRefinery | None = AIRefinery(api_key=API_KEY) if API_KEY is not None else None
DISTILLER_CLIENT: DistillerClient | None = DistillerClient(api_key=API_KEY) if API_KEY is not None else None

# LLM in use for chat completions.
LANGUAGE_MODEL: str = "meta-llama/Llama-3.3-70b-Instruct"

# Model in use for creating semantic embeddings.
EMBEDDING_MODEL: str = "intfloat/e5-mistral-7b-instruct"


# Name of locally stored clothing image caption data.
CAPTIONS_FILEPATH: str = os.path.join("Data", "captions.pkl")

# Warning messages.
MISSING_CLIENT_WARN: str = "Clients not initialized. Be sure to create a .env file holding your API key!"
MISSING_PICKLE_WARN: str = f"{CAPTIONS_FILEPATH} not found. Be sure to run `python refinery.py` to generate it!"


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Get a measure of cosine similarity between two ND arrays within [-1, 1],
    1 indicating maximal similarity, -1 indicating completely dissimilar, 0
    indicating unrelated.
    """
    length_a: float = np.linalg.norm(a)
    length_b: float = np.linalg.norm(b)

    similarity: float
    try:
        similarity = np.dot(a, b) / (length_a * length_b)
    except ZeroDivisionError:
        similarity = 0.0
    return similarity


def setup_orchestrators() -> None:
    """
    Setup all orchestrator projects as defined in .yaml config files.

    This function should be called before any other function in the refinery
    module is called.
    """
    if DISTILLER_CLIENT is None:
        print(MISSING_CLIENT_WARN)
        return None

    for config_path, project_name in CONFIG_FILES:
        is_config_valid: bool = DISTILLER_CLIENT.validate_config(config_path=config_path)

        if not is_config_valid:
            print(f"Unable to setup project {project_name}")
        DISTILLER_CLIENT.create_project(config_path=config_path, project=project_name)


async def get_image_caption(path: str) -> str | None:
    """
    Use the ImageUnderstanding agent defined, as provided by AI 
    Refinery, to generate a caption for a filepath to an input image.
    """
    if DISTILLER_CLIENT is None:
        print(MISSING_CLIENT_WARN)
        return None

    CLOTHING_ANALYSIS_PROMPT: str = """
        The provided image is of a piece of clothing. 
        
        Provide a precisely one-sentence-long caption which describes the item.
        The description should include color, material, and style.

        Be succinct, terse, and direct in the caption.
    """

    # Request the captioner orchestrator for an image caption.
    vlm_responses: list[str] = []
    async with DISTILLER_CLIENT(project="captioner", uuid="test") as dc:
        responses: AsyncGenerator[DistillerIncomingMessage] = await dc.query(query=CLOTHING_ANALYSIS_PROMPT, image=utils.image_to_base64(path))
        async for response in responses:
            vlm_responses.append(response["content"])
    return vlm_responses[-1] # The last element of response is caption string.


def get_text_embedding(text: str) -> list[float]:
    """
    Get a semantic embedding vector from the AI Refinery using the chosen
    `EMBEDDING_MODEL`.
    """
    if AIR_CLIENT is None:
        print(MISSING_CLIENT_WARN)
        return []

    embedding_response: CreateEmbeddingResponse = AIR_CLIENT.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return embedding_response.data[0].embedding


def generate_response(query: str, system_prompt: str="You are a helpful assisant.") -> str:
    """
    Get a response from model `LANGUAGE_MODEL` to the given user-query as
    a string, using the given system prompt as context.
    """
    if AIR_CLIENT is None:
        print(MISSING_CLIENT_WARN)
        return ""
    
    response: ChatCompletion = AIR_CLIENT.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        model=LANGUAGE_MODEL
    )
    return response.choices[0].message.content


def get_preference_description(profile: UserProfile) -> str:
    """
    Get a natural language description of the clothing preferences of the given
    user.
    """
    system_prompt: str = f"""
    You're a fashion stylist who's a master at picking out the types of clothes
    someone might like.

    Taking as input JSON data of a user's online clothes shopping profile, give
    a brief suggestion of what clothing the user may like.

    Example:
        USER INPUT:
        f{ALL_USER_PROFILES["Leo Nguyen"].model_dump_json(indent=2)}

        RESPONSE:
        Leo Nguyen is looking for an outfit with a smart casual aesthetic, appropriate
        for the work environment. He has a preference for slim-fitting navy whites, though 
        other colors are likely to match his style too, such as light gray and beige.

    Context:

    The JSON Schema of the user profile you will take as input:
        {json.dumps(UserProfile.model_json_schema()["properties"], indent=2)}
    """

    return generate_response(query=profile.model_dump_json(indent=2), system_prompt=system_prompt)


def get_recommendation(user: UserProfile, top_n: int=3) -> dict[str, list[int]]:
    """
    Get a set of clothing recommendations for the passed user, obtained as
    a list of size `top_n` clothing identifier codes.

    This function is dependent on there existing locally downloaded data
    as created by this module, and the `catalog_data.py` module.
    """
    captions_df: pd.DataFrame
    downloaded_df: pd.DataFrame | None = catalog_data.get_downloaded_data()

    # Get back the saved caption data
    try:
        captions_df = pd.read_pickle(CAPTIONS_FILEPATH)
    except FileNotFoundError:
        print(MISSING_PICKLE_WARN)
        return []
    preference: str = get_preference_description(user)
    preference_embedding: np.ndarray = np.array(get_text_embedding(preference))

    # Compute similarity between profile description and all image captions.
    # Then add this to catalog datalog and sort by similarity.
    all_similarities: list[float] = []
    for _, row in captions_df.iterrows():
        description_embedding: np.ndarray = row["embedding"]
        similarity: float = cosine_similarity(preference_embedding, description_embedding)
        all_similarities.append(similarity)
    downloaded_df["similarity"] = all_similarities
    downloaded_df.sort_values(by="similarity", ascending=False, inplace=True, axis=0)

    # Get the n images which are most semantically similar to the profile desc,
    # organized by clothing category.
    recommendations: dict[str, int] = {"tops": [], "bottoms": [], "outerwear": []}
    most_similar_by_category: pd.Series = downloaded_df.groupby("category")["similarity"].nlargest(top_n)

    for category, clothing_index in most_similar_by_category.index:
        clothing_indices: list[int] = recommendations.get(category, [])
        clothing_indices.append(clothing_index)
    return recommendations


if __name__ == "__main__":
    """
    Use the AI Refinery to generate captions of all (previously downloaded)
    clothing images saved as "{product_id}.JPG"
    """
    setup_orchestrators()

    # Fill out a mapping of clothing numeric IDs to their captions and word
    # embeddings of each caption.
    captions: dict[str, list] = {"product_id": [], "caption": [], "embedding": []}
    clothing_image_filenames: list[str] = catalog_data.get_image_filenames()

    for filename in clothing_image_filenames:
        filepath: str = os.path.join(catalog_data.CLOTHING_IMAGES_PATH, filename)

        caption: str = asyncio.run(get_image_caption(filepath))
        product_id: int = filename.split(".")[0]
        embedding: list[float] = get_text_embedding(caption)

        captions["product_id"].append(product_id)
        captions["caption"].append(caption)
        captions["embedding"].append(np.array(embedding))
    
    # Save the mapping as a pickled Pandas object to reference in app.py
    captions_df: pd.DataFrame = pd.DataFrame.from_dict(captions)
    captions_df.to_pickle(CAPTIONS_FILEPATH)