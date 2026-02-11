import pandas as pd

from src.data.working_set_builder import (
    TARGET_CATEGORIES,
    add_predicted_category,
    map_main_category,
    train_category_model,
)


class TestCategoryMapping:
    def test_map_main_category_hits_keyword(self):
        label = map_main_category("Computers", ["Electronics", "Laptops"])
        assert label == "laptop"

    def test_map_main_category_phone(self):
        label = map_main_category("Electronics", ["Cell Phones", "Smartphones"])
        assert label == "phone"

    def test_map_main_category_falls_back(self):
        label = map_main_category("Accessories", ["Cables"])
        assert label == "other"


class TestTrainingAndPrediction:
    def test_training_adds_category_column(self):
        df = pd.DataFrame(
            [
                {
                    "title_meta": "Gaming Laptop",
                    "description": ["High performance laptop"],
                    "text": "Great laptop for work",
                    "main_category": "Computers",
                    "categories": ["Electronics", "Laptops"],
                },
                {
                    "title_meta": "Wireless Mouse",
                    "description": ["Bluetooth mouse"],
                    "text": "Mouse works well",
                    "main_category": "Accessories",
                    "categories": ["Electronics", "Computer Accessories"],
                },
                {
                    "title_meta": "Noise Cancelling Headphones",
                    "description": ["Over ear"],
                    "text": "Headphones with great sound",
                    "main_category": "Audio",
                    "categories": ["Electronics", "Headphones"],
                },
            ]
        )
        model = train_category_model(df)
        updated = add_predicted_category(df, model)
        assert "clean_main_category" in updated.columns
        assert updated["clean_main_category"].isin(TARGET_CATEGORIES).all()
