FROM public.ecr.aws/lambda/python:3.11

COPY data/lambda/sync_and_fetch/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -t "${LAMBDA_TASK_ROOT}"

COPY data/__init__.py "${LAMBDA_TASK_ROOT}/data/__init__.py"
COPY data/constants.py "${LAMBDA_TASK_ROOT}/data/constants.py"
COPY data/ingestion "${LAMBDA_TASK_ROOT}/data/ingestion"

COPY data/lambda/sync_and_fetch/handler.py "${LAMBDA_TASK_ROOT}/handler.py"

CMD ["handler.lambda_handler"]
