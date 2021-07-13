from typing import List, Tuple


def _convert_payload(sparkapp: dict) -> dict:
    app_name = sparkapp["metadata"]["labels"]["app"]
    spark_app_name = sparkapp["metadata"]["name"]
    spark_app_state = sparkapp["status"]["applicationState"]["state"]
    spark_app_id = sparkapp["status"]["sparkApplicationId"]
    spark_app_start_time = sparkapp["status"]["lastSubmissionAttemptTime"]
    app_start_time = sparkapp["metadata"]["creationTimestamp"]
    spark_app_stop_time = sparkapp["status"]["terminationTime"]
    spark_app_execution_attempts = sparkapp["status"]["executionAttempts"]
    spark_app_submission_attempts = sparkapp["status"]["submissionAttempts"]
    spark_app_payload = {
        "job_name": app_name,
        "spark_name": spark_app_name,
        "state": spark_app_state,
        "id": spark_app_id,
        "start_time": spark_app_start_time,
        "container_start_time": app_start_time,
        "stop_time": spark_app_stop_time,
        "execution_attempts": spark_app_execution_attempts,
        "submission_attempts": spark_app_submission_attempts,
    }
    return spark_app_payload


def group_applications(spark_applications: List[dict]) -> List[Tuple[str, list]]:
    # placeholder = {}
    return [_convert_payload(sparkapp) for sparkapp in spark_applications]
