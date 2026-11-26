from agents.asmr_text import run_text
from worker.asmr_text_generate import run_generate
from models.schemas_task import TaskType

EXECUTORS = {
    TaskType.ASMR_TEXT: run_text,
    TaskType.ASMR_TEXT_GENERATE: run_generate,
}
