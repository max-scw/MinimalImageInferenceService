import fastapi
from fastapi import FastAPI
# from fastapi_offline import FastAPIOffline as FastAPI
from datetime import datetime

import sys
import re

# from prometheus_fastapi_instrumentator import Instrumentator


DATETIME_INIT = datetime.now()


def default_fastapi_setup(title: str = None, summary: str = None, description: str = None):
    license_info = {
        "name": "MIT License",
        "url": "https://github.com/max-scw/MinimalImageInference/blob/main/LICENSE",
    }

    contact = {
        "name": "max-scw",
        "url": "https://github.com/max-scw/",
    }

    app = FastAPI(
        title=title,
        summary=summary,
        description=description,
        contact=contact,
        license_info=license_info
    )

    # create endpoint for prometheus
    # instrumentator = Instrumentator(
    #     excluded_handlers=["/test/*", "/metrics"],  # FIXME: not working
    # )
    # # replace not allowed characters
    # metric_namespace = re.sub("[^a-zA-Z0-9]", "_", title.lower())
    # instrumentator.instrument(app, metric_namespace=metric_namespace).expose(app)

    # ----- home
    @app.get("/")
    async def home():
        return {
            "Title": title,
            "Description": summary,
            "Help": "see /docs for help (automatic docs with Swagger UI).",
            "Software": {
                "fastAPI": fastapi.__version__,
                "Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            },
            "License": license_info,
            "Impress": contact,
            "Startup date": DATETIME_INIT
        }

    return app
