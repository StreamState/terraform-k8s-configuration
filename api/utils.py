from typing import List, Tuple


def group_applications(spark_applications: List[dict]) -> List[Tuple[str, list]]:
    placeholder = {}
    for sparkapp in spark_applications:
        app_name = sparkapp["metadata"]["labels"]["app"]
        spark_app_name = sparkapp["metadata"]["name"]
        if app_name in placeholder:
            placeholder[app_name].append(spark_app_name)
        else:
            placeholder[app_name] = [spark_app_name]
    return [
        {"app_name": key, "spark_applications": value}
        for (key, value) in placeholder.items()
    ]
