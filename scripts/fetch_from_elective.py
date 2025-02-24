import os
import re

import tqdm
from playwright.sync_api import Page, Playwright, sync_playwright
from pydantic import TypeAdapter

from which_class.model import Course, CourseTime
from which_class.pull_words import PullWords

pull_words = PullWords()


def parse_上课时间(data: str):
    timing_re = re.compile(r"(\d+)~(\d+)周 (.)周周(.)(\d+)~(\d+)节( (\w+))?")
    notes_re = re.compile(r"\(备注：(.*)\)")
    timings = []
    notes = []

    for match in timing_re.finditer(data):
        (
            start_week,
            end_week,
            week_type,
            weekday,
            start_time,
            end_time,
            _,
            classroom,
        ) = match.groups()
        周数 = list(range(int(start_week), int(end_week) + 1))
        if week_type == "单":
            周数 = [week for week in 周数 if week % 2 == 1]
        elif week_type == "双":
            周数 = [week for week in 周数 if week % 2 == 0]
        星期 = "无一二三四五六日".index(weekday)
        for 节次 in range(int(start_time), int(end_time) + 1):
            timings.append(CourseTime(星期=星期, 节次=节次, 周数=周数, 教室=classroom))

    for match in notes_re.finditer(data):
        note = match.group(1)
        if note:
            notes.append(note)

    return {
        "timings": timings,
        "上课时间及教室": [match.group(0) for match in timing_re.finditer(data)],
        "备注": "\n".join(notes),
    }


def parse_选课计划(data: dict[str, str]):
    course = Course(
        课程号=data["课程号"],
        名称=data["名称"],
        类别=data["类别"],
        教师=data.get("教师") or None,
        班号=data.get("班号") or None,
        学分=float(data["学分"]),
        开课单位=data.get("开课单位") or None,
        专业=None,
        年级=data.get("年级") or None,
        **parse_上课时间(data["上课时间及教室"]),
    )
    if course.备注:
        course.keywords = " ".join(
            pull_words("\n".join(course.上课时间及教室) + course.备注)
        )
    return course


def parse_课程查询(data: dict[str, str]):
    course = Course(
        课程号=data["课程号"],
        名称=data["名称"],
        类别=data["类别"],
        教师=data.get("教师") or None,
        班号=data.get("班号") or None,
        学分=float(data["学分"]),
        开课单位=data.get("开课单位") or None,
        专业=data.get("专业") or None,
        年级=data.get("年级") or None,
        **parse_上课时间(data["上课时间及教室"]),
    )
    course.备注 = data.get("备注") or None
    if course.备注:
        course.keywords = " ".join(
            pull_words("\n".join(course.上课时间及教室) + course.备注)
        )
    return course


def read_table(page: Page, head: list[str]):
    page.wait_for_selector("table.datagrid")
    table = page.locator("css=table.datagrid").all()[0]
    rows = table.locator("css=tr").all()
    for row in rows:
        cells = row.locator("css=td").all()
        data = {}
        for key, cell in zip(head, cells):
            data[key] = cell.inner_text()
        yield data


def run(playwright: Playwright, account: str, password: str):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://elective.pku.edu.cn/")
    page.get_by_role("textbox", name="学号/职工号/手机号").click()
    page.get_by_role("textbox", name="学号/职工号/手机号").fill(account)
    page.get_by_role("textbox", name="密码").click()
    page.get_by_role("textbox", name="密码").fill(password)
    page.get_by_role("button", name="登录").click()

    print("读取选课计划...")
    课程列表_选课计划: dict[tuple[str, str], dict[str, str]] = {}
    page.get_by_role("link", name="选课计划", exact=True).click()
    head = [
        "课程号",
        "名称",
        "班号",
        "类别",
        "年级",
        "学分",
        "周学时",
        "总学时",
        "上课时间及教室",
    ]
    for data in read_table(page, head):
        if "名称" in data and "班号" in data:
            课程列表_选课计划[(data["名称"], data["班号"])] = data

    print("读取补退选...")
    page.get_by_role("link", name="补退选", exact=True).first.click()
    page_options = (
        page.locator('select[name="netui_row"]').first.get_by_role("option").all()
    )
    for option in tqdm.tqdm(page_options):
        page.get_by_role("combobox").first.select_option(option.get_attribute("value"))
        head = [
            "名称",
            "类别",
            "学分",
            "周学时",
            "教师",
            "班号",
            "开课单位",
            "年级",
        ]
        for data in read_table(page, head):
            if "名称" in data and "班号" in data:
                课程列表_选课计划[(data["名称"], data["班号"])].update(data)

    全部课程 = [parse_选课计划(data) for data in 课程列表_选课计划.values()]

    print("读取全部课程...")
    page.get_by_role("link", name="选课计划", exact=True).click()
    page.get_by_role("link", name="添加其它课程").click()
    for 课程分类 in [
        "#speciality",
        "#politics",
        "#english",
        "#gym",
        "#tsk_choice",
        "#pub_choice",
        "#liberal_computer",
    ]:
        page.locator(课程分类).check()
        if page.locator("css=div.item[data-value]").count():
            page.locator("css=div.item[data-value]").first.click()
            page.get_by_text("全部").and_(
                page.locator("css=div[data-selectable]")
            ).click()
        page.get_by_role("button", name="查询").click()

        page_options = (
            page.locator('select[name="netui_row"]').last.get_by_role("option").all()
        )
        for option in tqdm.tqdm(page_options, desc=课程分类):
            page.get_by_role("combobox").last.select_option(
                option.get_attribute("value")
            )
            head = [
                "课程号",
                "名称",
                "类别",
                "学分",
                "教师",
                "班号",
                "开课单位",
                "专业",
                "年级",
                "上课时间及教室",
                "限数/已选",
                "备注",
            ]
            if 课程分类 == "#english":
                head.insert(2, "大英级别")
            for data in read_table(page, head):
                if "课程号" in data and "名称" in data and "类别" in data:
                    全部课程.append(parse_课程查询(data))

    with open("data/全部课程.json", "wb") as f:
        json = TypeAdapter(list[Course]).dump_json(
            全部课程, indent=2, exclude_none=True
        )
        f.write(json)

    context.close()
    browser.close()


if __name__ == "__main__":
    account = os.getenv("PKU_ACCOUNT")
    password = os.getenv("PKU_PASSWORD")
    if not account or not password:
        raise ValueError(
            "Please set PKU_ACCOUNT and PKU_PASSWORD in environment variables."
        )

    with sync_playwright() as playwright:
        run(playwright, account=account, password=password)
