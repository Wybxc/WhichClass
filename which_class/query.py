import re
from motor.motor_asyncio import AsyncIOMotorDatabase

from which_class.pull_words import PullWords


WEEKDAYS = ["", "一", "二", "三", "四", "五", "六", "日"]


class Engine:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.pull_words = PullWords()

    async def query(
        self, weekday: int, period: int, classroom: str
    ) -> tuple[list, str | None]:
        # 精确搜索
        if classroom:
            result = self.database.courses.find(
                {
                    "timings": {
                        "$elemMatch": {
                            "星期": weekday,
                            "节次": period,
                            "教室": classroom,
                        }
                    }
                }
            )
            if search_result := await result.to_list():
                return search_result, None

        # 模糊搜索（只限定星期和节次，关键词匹配）
        classroom_search = " ".join(re.split(r"(\d+)", classroom))
        text_search = f'"周{WEEKDAYS[weekday]}" "{period}" "{classroom_search}"'
        result = self.database.courses.find(
            {
                "timings": {
                    "$elemMatch": {
                        "星期": weekday,
                        "节次": period,
                    }
                },
                "$text": {
                    "$search": text_search,
                },
            }
        )
        if search_result := await result.to_list():
            return search_result, None

        # 模糊搜索（无限定，关键词匹配）
        result = self.database.courses.aggregate(
            [
                {
                    "$match": {
                        "timings": {
                            "$elemMatch": {
                                "教室": None,
                            }
                        },
                        "$text": {
                            "$search": text_search,
                        },
                    },
                },
                {
                    "$addFields": {
                        "score": {"$meta": "textScore"},
                    }
                },
                {
                    "$match": {
                        "score": {"$gt": 2},
                    }
                },
            ]
        )
        if search_result := await result.to_list():
            return search_result, "没有找到该时段的课程，以下是模糊匹配结果"

        # 模糊搜索（无限定，模糊匹配）
        text_search = f"周{WEEKDAYS[weekday]} {period} {classroom_search}"
        result = self.database.courses.aggregate(
            [
                {
                    "$match": {
                        "timings": {
                            "$elemMatch": {
                                "教室": None,
                            }
                        },
                        "$text": {
                            "$search": text_search,
                        },
                    },
                },
                {
                    "$addFields": {
                        "score": {"$meta": "textScore"},
                    }
                },
                {
                    "$match": {
                        "score": {"$gt": 2},
                    }
                },
            ]
        )
        if search_result := await result.to_list():
            return search_result, "没有找到该时段的课程，以下是模糊匹配结果"

        return [], "没有找到相关课程"

    async def match(
        self,
        classid: str,
        name: str,
        teacher: str,
        department: str,
        notes: str,
    ) -> tuple[list, str | None]:
        query = {}
        if classid:
            query["课程号"] = classid
        if name:
            query["名称"] = {"$regex": name}
        if teacher:
            query["教师"] = {"$regex": teacher}
        if department:
            query["$or"] = [
                {"开课单位": {"$regex": department}},
                {"专业": {"$regex": department}},
            ]
        if notes:
            query["$text"] = {"$search": " ".join(self.pull_words(notes))}

        if not query:
            return [], "搜索条件为空"

        result = self.database.courses.find(query)
        if search_result := await result.to_list():
            return search_result, None

        return [], "没有找到相关课程"
