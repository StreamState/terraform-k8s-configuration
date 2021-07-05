from utils import group_applications


def test_group_applications_empty():
    result = group_applications([])
    assert len(result) == 0


def test_group_applications_normal():
    result = group_applications(
        [
            {
                "metadata": {
                    "creationTimestamp": "2021-07-04T14:58:34Z",
                    "labels": {"app": "app1"},
                    "name": "spark1",
                },
                "status": {
                    "applicationState": {"state": "RUNNING"},
                    "sparkApplicationId": 1,
                    "lastSubmissionAttemptTime": "2021-07-04T14:58:46Z",
                    "terminationTime": None,
                    "executionAttempts": 1,
                    "submissionAttempts": 1,
                },
            },
            {
                "metadata": {
                    "creationTimestamp": "2021-07-04T14:58:34Z",
                    "labels": {"app": "app2"},
                    "name": "spark1",
                },
                "status": {
                    "applicationState": {"state": "RUNNING"},
                    "sparkApplicationId": 1,
                    "lastSubmissionAttemptTime": "2021-07-04T14:58:46Z",
                    "terminationTime": None,
                    "executionAttempts": 1,
                    "submissionAttempts": 1,
                },
            },
            {
                "metadata": {
                    "creationTimestamp": "2021-07-04T14:58:34Z",
                    "labels": {"app": "app1"},
                    "name": "spark2",
                },
                "status": {
                    "applicationState": {"state": "RUNNING"},
                    "sparkApplicationId": 1,
                    "lastSubmissionAttemptTime": "2021-07-04T14:58:46Z",
                    "terminationTime": None,
                    "executionAttempts": 1,
                    "submissionAttempts": 1,
                },
            },
        ]
    )
    assert result == [
        {
            "job_name": "app1",
            "spark_applications": [
                {
                    "spark_name": "spark1",
                    "state": "RUNNING",
                    "id": 1,
                    "start_time": "2021-07-04T14:58:46Z",
                    "container_start_time": "2021-07-04T14:58:34Z",
                    "stop_time": None,
                    "execution_attempts": 1,
                    "submission_attempts": 1,
                },
                {
                    "spark_name": "spark2",
                    "state": "RUNNING",
                    "id": 1,
                    "start_time": "2021-07-04T14:58:46Z",
                    "container_start_time": "2021-07-04T14:58:34Z",
                    "stop_time": None,
                    "execution_attempts": 1,
                    "submission_attempts": 1,
                },
            ],
        },
        {
            "job_name": "app2",
            "spark_applications": [
                {
                    "spark_name": "spark1",
                    "state": "RUNNING",
                    "id": 1,
                    "start_time": "2021-07-04T14:58:46Z",
                    "container_start_time": "2021-07-04T14:58:34Z",
                    "stop_time": None,
                    "execution_attempts": 1,
                    "submission_attempts": 1,
                }
            ],
        },
    ]
