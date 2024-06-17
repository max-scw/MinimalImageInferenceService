from fastapi_offline import FastAPIOffline as FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def default_fastapi_setup(title: str = None, summary: str = None, description: str = None):
    license_info = {
        "name": "MIT License",
        "url": "https://github.com/max-scw/MinimalImageInference/blob/main/LICENSE",
    }

    contact = {
        "name": "max-scw",
        "url": "https://github.com/max-scw/MinimalImageInference",
    }

    app = FastAPI(
        title=title,
        summary=summary,
        description=description,
        contact=contact,
        license_info=license_info
    )

    # create endpoint for prometheus
    instrumentator = Instrumentator(
        excluded_handlers=["/test/*", "/metrics"],
    )
    instrumentator.instrument(app, metric_namespace=title.lower()).expose(app)

    # ----- home
    @app.get("/")
    async def home():
        return {
            "Title": title,
            "Description": summary,
            "Help": "see /docs for help.",
            "License": license_info,
            "Impress": contact
        }

    return app
