"""

Module for handling parsing of image catalog data at "clean_catalog.csv".

Run this script as main to download all images from the catalog URLs to the
local filesystem under the "Data" directory as "models" and "clothes" images.

"""

import os
import requests
import pandas as pd

from PIL import Image
from io import BytesIO


CATALOG_PATH: str = os.path.join("Data", "uniqlo_catalog_updated.csv")
DOWNLOADED_PATH: str = os.path.join("Data", "uniqlo_downloaded.csv")
CLOTHING_IMAGES_PATH: str = os.path.join("static", "images", "clothes")
MODEL_IMAGES_PATH: str = os.path.join("static", "images", "models")


def save_image_data() -> None:
    """
    Save the image data from the image URLs found in the catalog data at 
    `CATALOG_PATH` to the local filesystem as JPGs

    The subset of the catalog data at `CATALOG_PATH` which successfully
    downloaded is saved as a CSV file next to the original catalog data.
    """
    catalog_df: pd.DataFrame = pd.read_csv(CATALOG_PATH)

    for index, row in catalog_df.iterrows():
        clothing_image: Image.Image | None = get_image_url(row["image_link"])
        model_image: Image.Image | None = get_image_url(row["model_image_link"])

        # Just skip saving images which were unable to be found.
        if clothing_image is None or model_image is None:
            catalog_df.drop(index, inplace=True)
            continue

        clothing_image.save(os.path.join(CLOTHING_IMAGES_PATH, str(row["product_id"]) + ".jpg"))
        model_image.save(os.path.join(MODEL_IMAGES_PATH, str(row["product_id"]) + ".jpg"))

        clothing_image.close()
        model_image.close()
    catalog_df.to_csv(DOWNLOADED_PATH, index=False, mode="w")


def get_downloaded_data() -> pd.DataFrame | None:
    """
    Retrieve the catalog data for those images which were successfully downloaded
    by the last call to save_image_data().

    Return None if save_image_data() was never called.
    """
    try:
        return pd.read_csv(DOWNLOADED_PATH)
    except FileNotFoundError:
        print(f"No {DOWNLOADED_PATH} found, must call save_image_data() first!")
        return None


def get_image_url(url: str) -> Image.Image | None:
    """
    Get the image located at the given URL as a PIL Image. 
    
    Return None on failure.
    """
    image: Image.Image | None = None
    try:
        response: requests.Response = requests.get(url)
        response.raise_for_status()

        print("Found image at:", url)
        image = Image.open(BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        print(f"\n\n Error fetching image from ({url}).\nError: {e}\n\n")
    return image


def get_image_filenames() -> list[str]:
    """
    Get a list of all clothing image filenames which were successfully 
    downloaded by the last call to save_image_data()
    """
    downloaded_df: pd.DataFrame | None = get_downloaded_data()

    if downloaded_df is None:
        return []
    return list(downloaded_df["product_id"].astype(str) + ".jpg")


if __name__ == "__main__":
    os.makedirs(CLOTHING_IMAGES_PATH, exist_ok=True)
    os.makedirs(MODEL_IMAGES_PATH, exist_ok=True)
    save_image_data()