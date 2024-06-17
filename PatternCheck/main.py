from fastapi_offline import FastAPIOffline as FastAPI
# from fastapi import HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator

from utils_coordinates import check_boxes, load_patterns


import logging
from timeit import default_timer

# custom packages
from utils import get_config, set_env_variable
from DataModels import PatternRequest

set_env_variable("LOGGING_LEVEL", "DEBUG")  # FIXME
# get config
CONFIG = get_config(default_prefix="")
logging.debug(f"CONFIG: {CONFIG}")

# load patterns
PATTERNS = load_patterns(CONFIG["FOLDER"])
DEFAULT_PATTERN_KEY = CONFIG["DEFAULT_PATTERN"]

# use fist pattern if no pattern key was provided
if not DEFAULT_PATTERN_KEY:
    if len(PATTERNS) > 0:
        DEFAULT_PATTERN_KEY = list(PATTERNS.keys())[0]
        logging.info(f"No default pattern key provided. Using '{DEFAULT_PATTERN_KEY}' as default pattern")
    else:
        msg = f"No pattern file found in {CONFIG['FOLDER']}."
        logging.error(msg)
        raise Exception(msg)
elif DEFAULT_PATTERN_KEY not in PATTERNS:
    msg = f"Default pattern '{DEFAULT_PATTERN_KEY}' not found in {CONFIG['FOLDER']}"
    logging.error(msg)
    raise Exception(msg)

# entry points
ENTRYPOINT = "/"

summary = "Minimalistic server to provide a REST api to check patterns."
app = FastAPI(
    title="PatternCheck",
    summary=summary,
    # contact={
    #     "name": "max-scw",
    #     "url": "https://github.com/max-scw/FIXME",
    # },
    # license_info={
    #     "name": "BSD 3-Clause License",
    #     "url": "https://github.com/max-scw/FIXME/blob/main/LICENSE",
    # }
)

# create endpoint for prometheus
Instrumentator().instrument(app).expose(app)  # produces a False in the console every time a valid entrypoint is called


# ----- home
@app.get("/")
async def home():
    return {
        "Description": summary
    }


@app.post(ENTRYPOINT)
async def main(request: PatternRequest):
    bboxes = request.coordinates
    keyword = request.pattern_key.lower() if request.pattern_key else DEFAULT_PATTERN_KEY
    class_ids = request.class_ids

    t0 = default_timer()
    pattern_name, lg = check_boxes(bboxes, class_ids, PATTERNS[keyword])
    dt = default_timer() - t0
    logging.debug(f"check_boxes(): {pattern_name}, {lg}; took {dt:.4g} s")

    # output
    content = {
        "decision": (len(lg) > 1) and all(lg),
        "pattern_name": pattern_name,
        "lg": lg,
    }

    return JSONResponse(content=content)


if __name__ == "__main__":
    # set logging to DEBUG when called as default entry point
    logging.basicConfig(level=logging.DEBUG)

    uvicorn.run(app=app, port=5053)
