import os

import pymongo
from pydantic import TypeAdapter
from pymongo import MongoClient

from which_class.model import Course

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        print("python-dotenv not installed. Ignoring .env file.")

    client = MongoClient(os.environ["MONGO_URI"])
    database = client[os.environ["MONGO_DB"]]

    schema = TypeAdapter(list[Course])
    with open("data/全部课程.json", "rb") as f:
        全部课程 = schema.validate_json(f.read())

    database.courses.drop()
    database.courses.insert_many(
        schema.dump_python(全部课程, exclude_none=True),
        ordered=False,
    )

    database.courses.create_index(
        [
            ("上课时间及教室.教室", pymongo.ASCENDING),
            ("上课时间及教室.星期", pymongo.ASCENDING),
            ("上课时间及教室.节次", pymongo.ASCENDING),
            ("上课时间及教室.周数", pymongo.ASCENDING),
        ],
        name="classroom_index",
    )
    database.courses.create_index(
        [("keywords", pymongo.TEXT)],
        default_language="english",
        name="keywords_index",
    )
