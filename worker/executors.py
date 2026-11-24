from agents.asmr_text import run_text
from models.schemas_task import TaskType

EXECUTORS = {
    TaskType.ASMR_TEXT: run_text,
}
