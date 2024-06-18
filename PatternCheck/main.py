# from fastapi_offline import FastAPIOffline as FastAPI
# from fastapi import HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from utils_coordinates import check_boxes, load_patterns
from utils_fastapi import default_fastapi_setup


import logging
from timeit import default_timer

# custom packages
from utils import get_config, set_env_variable
from DataModels import PatternRequest

# get config
CONFIG = get_config()

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

title = "Pattern-Check"
summary = "Minimalistic server providing a REST api to check patterns."
app = default_fastapi_setup(title, summary)


@app.post(ENTRYPOINT + "check")
async def post(request: PatternRequest):
    # bounding boxes
    bboxes = request.coordinates
    class_ids = request.class_ids
    # patterns to check against
    keyword = request.pattern_key.lower() if request.pattern_key else DEFAULT_PATTERN_KEY
    if request.pattern:
        pattern = request.pattern
    else:
        pattern = PATTERNS[keyword]

    t0 = default_timer()
    pattern_name, lg = check_boxes(bboxes, class_ids, pattern)
    dt = default_timer() - t0

    logging.debug(f"check_boxes(): pattern_name={pattern_name}, lg={lg}; took {dt:.4g} s")

    # output
    content = {
        "decision": (len(lg) > 1) and all(lg),
        "pattern_name": pattern_name,
        "lg": lg,
    }

    return JSONResponse(content=content)


if __name__ == "__main__":

    uvicorn.run(app=app, port=5053)
