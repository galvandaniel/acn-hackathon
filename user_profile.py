from pydantic import BaseModel


class UserProfile(BaseModel):
    name: str
    age: int
    gender: str
    aesthetic: str
    size: str
    budget: int
    event_type: list[str]
    browsing_data: list[str]
    purchase_history: list[dict[str, str | int]]
    preferences: list[str]

# List of all JSON-like user profiles.
ALL_USER_DICTS: list[dict[str, any]] = [
    {
        "name": "Ava Chen",
        "age": 27,
        "gender": "female",
        "aesthetic": "minimalist",
        "size": "small",
        "budget": 150,
        "event_type": ["corporate_events", "brunches"],
        "browsing_data": ["blazers", "neutral basics", "capsule wardrobe"],
        "purchase_history": [{"item": "wool coat", "price": 210}, {"item": "silk blouse", "price": 95}, {"item": "tailored trousers", "price": 180}],
        "preferences": ["sustainable_fabrics", "neutral_tones"]
    },
    {
        "name": "Leo Nguyen",
        "age": 29,
        "gender": "male",
        "aesthetic": "smart casual",
        "size": "medium",
        "budget": 120,
        "event_type": ["work_dinners", "travel"],
        "browsing_data": ["polos", "chinos", "travel_blazers"],
        "purchase_history": [{"item": "linen shirt", "price": 65}, {"item": "navy chinos", "price": 80}, {"item": "leather belt", "price": 40}],
        "preferences": ["slim_fits", "navy_white_palette"]
    }
]

# Dictionary mapping from names to profiles.
ALL_USER_PROFILES: dict[str, UserProfile] = {
    user_dict["name"]: UserProfile.model_validate(user_dict) for user_dict in ALL_USER_DICTS
}