from typing import List


def _metadata(default_body: dict, namespace: str) -> dict:
    default_body["metadata"]["namespace"] = namespace
    return default_body


def spark_service_account_spec(namespace: str) -> dict:
    return {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {"name": "spark", "namespace": namespace},
    }


def spark_role_spec(namespace: str) -> dict:
    return {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "Role",
        "metadata": {"namespace": namespace, "name": "spark-role"},
        "rules": [
            {
                "apiGroups": [""],
                "resources": ["pods"],
                "verbs": ["*"],
            },
            {"apiGroups": [""], "resources": ["services"], "verbs": ["*"]},
        ],
    }


def spark_role_binding_spec(namespace: str) -> dict:
    return {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": {"namespace": namespace, "name": "spark-role-binding"},
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": "spark",
                "namespace": namespace,
            },
        ],
        "roleRef": {
            "kind": "Role",
            "name": "spark-role",
            "apiGroup": "rbac.authorization.k8s.io",
        },
    }


def spark_persist_job_spec(
    default_body: dict, image: str, brokers: List[str], topic: str, namespace: str
) -> dict:
    default_body["metadata"] = {
        "name": f"{topic}-persist",
        "namespace": namespace,
    }
    default_body["spec"]["image"] = image
    default_body["spec"]["arguments"] = [
        f"{topic}-persist",
        ",".join(brokers),
        "test-1",
        topic,
        "/tmp/sink",
        "/tmp/checkpoint",
    ]
    return default_body


def spark_state_job_spec(
    default_body: dict,
    image: str,
    brokers: List[str],
    topics: List[str],
    namespace: str,
    cassandraIp: str,
    cassandraPassword: str,
) -> dict:
    name = "-".join(topics)
    default_body["metadata"] = {"name": f"{name}-application", "namespace": namespace}
    default_body["spec"]["image"] = image
    default_body["spec"]["arguments"] = [
        f"{name}-application",
        ",".join(brokers),
        "test-1",
        ",".join(topics),
        "/tmp/sink",
        "/tmp/checkpoint",
        cassandraIp,
        cassandraPassword,
    ]
    return default_body