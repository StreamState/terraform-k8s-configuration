from utils import group_applications


def test_group_applications_empty():
    result = group_applications([])
    assert len(result) == 0


def test_group_applications_normal():
    result = group_applications(
        [
            {"metadata": {"labels": {"app": "app1"}, "name": "spark1"}},
            {"metadata": {"labels": {"app": "app2"}, "name": "spark1"}},
            {"metadata": {"labels": {"app": "app1"}, "name": "spark2"}},
        ]
    )
    assert result == [
        {"app_name": "app1", "spark_applications": ["spark1", "spark2"]},
        {"app_name": "app2", "spark_applications": ["spark1"]},
    ]
