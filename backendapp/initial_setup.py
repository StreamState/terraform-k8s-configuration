from kubernetes.client.api import CoreV1Api
from kubernetes import client, config
from create_body import (
    spark_service_account_spec,
    spark_role_spec,
    spark_role_binding_spec,
)
from kubernetes.client import RbacAuthorizationV1Api


def create_namespace(api: CoreV1Api, namespace: str):
    api.create_namespace(
        client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))
    )


def create_service_account(api: CoreV1Api, namespace: str):
    api.create_namespaced_service_account(
        namespace, spark_service_account_spec(namespace)
    )


def create_cluster_role(api: RbacAuthorizationV1Api, namespace: str):
    api.create_cluster_role(spark_role_spec(namespace))


def create_cluster_role_binding(api: RbacAuthorizationV1Api, namespace: str):
    api.create_cluster_role_binding(spark_role_binding_spec(namespace))


if __name__ == "__main__":
    config.load_incluster_config()
    api = client.CoreV1Api()
    create_namespace(api, "mynamespace")
    create_service_account(api, "mynamespace")
    api_rbac = client.RbacAuthorizationV1Api()
    create_cluster_role(api_rbac, "mynamespace")
    create_cluster_role_binding(api_rbac, "mynamespace")
