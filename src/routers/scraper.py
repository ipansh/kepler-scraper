from fastapi import APIRouter
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:     %(message)s')
logger = logging.getLogger(__name__)
#logging.info(f"This is {select_env} environment.")

router = APIRouter()

@router.get("/health")
def health_check():
    return "OK"