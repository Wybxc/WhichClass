from pydantic import BaseModel


class CourseTime(BaseModel):
    星期: int
    节次: int
    周数: list[int]
    教室: str | None = None


class Course(BaseModel):
    课程号: str
    名称: str
    类别: str
    教师: str | None = None
    班号: str | None = None
    学分: float
    开课单位: str | None = None
    专业: str | None = None
    年级: str | None = None
    上课时间及教室: list[str]
    备注: str | None = None
    timings: list[CourseTime]
    keywords: str = ""
