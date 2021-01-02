from pathlib import Path

DATE_FORMAT = '%d.%m.%Y'
ENV_VAR_PREFIX = 'ANALYZER_'

MAX_QUERY_ARGS = 32767
DEFAULT_PG_URL = 'postgresql://analyzer_user:analyzer_password@localhost/analyzer'
PROJECT_PATH = str(Path(__file__).parent.parent.absolute())

MAX_INTEGER = 2147483647
LONGEST_STR = '0' * 256
