import bisect
import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
from litestar import Litestar, get
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.plugins.htmx import HTMXPlugin, HTMXTemplate
from litestar.response import Template
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig
from litestar.datastructures import State
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

from which_class.query import Engine

load_dotenv()


async def connect_db(app: Litestar):
    engine = getattr(app.state, "engine", None)
    if engine is None:
        mongodb = AsyncIOMotorClient(os.environ["MONGO_URI"], server_api=ServerApi("1"))
        database = mongodb[os.environ["MONGO_DB"]]
        engine = Engine(database)
        app.state.engine = engine


@get("/")
async def index() -> Template:
    下课时间 = [
        (0, 0),
        (8, 50),
        (9, 50),
        (11, 0),
        (12, 0),
        (13, 50),
        (14, 50),
        (16, 0),
        (17, 0),
        (18, 0),
        (19, 30),
        (20, 30),
    ]
    now = datetime.datetime.now()
    当前节次 = bisect.bisect(下课时间, (now.hour, now.minute))

    return Template(
        template_name="index.html",
        context={"当前节次": 当前节次},
    )


@get("/about")
async def about() -> Template:
    return Template(template_name="about.html")


@get("/query")
async def query(state: State, weekday: int, period: int, classroom: str) -> Template:
    engine: Engine = state.engine
    courses, messsage = await engine.query(weekday, period, classroom)
    return HTMXTemplate(
        template_name="query.html",
        context={"courses": courses, "message": messsage},
    )


base_dir = Path(__file__).parent


def register_template_callables(engine: JinjaTemplateEngine) -> None:
    engine.register_template_callable(
        key="now",
        template_callable=lambda _: datetime.datetime.now(),
    )


app = Litestar(
    [
        index,
        about,
        query,
        create_static_files_router(
            path="/static",
            directories=[base_dir.parent / "public"],
        ),
    ],
    on_startup=[connect_db],
    plugins=[HTMXPlugin()],
    template_config=TemplateConfig(
        directory=base_dir / "templates",
        engine=JinjaTemplateEngine,
        engine_callback=register_template_callables,
    ),
)
