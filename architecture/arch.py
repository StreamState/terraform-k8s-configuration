from diagrams import Diagram, Cluster
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB
from diagrams.onprem.queue import Kafka
from diagrams.aws.compute import ECS, EKS, Lambda
from diagrams.gcp.database import Firestore
from diagrams.onprem.analytics import Spark
from diagrams.gcp.storage import Storage
from diagrams.programming.language import Python
from diagrams.gcp.devtools import Code
from diagrams.onprem.gitops import Argocd

with Diagram("StreamState", show=False):
    kafka_input = Kafka("Kafka")
    kafka_output = Kafka("Kafka")

    with Cluster("StreamState cluster"):
        # svc_group = [ECS("web1"), ECS("web2"), ECS("web3")]
        with Cluster("Replay"):
            kafka_storage = Storage("Kafka sink")
            spark_reload = Spark("Replay")

        with Cluster("Realtime"):
            spark_persist = Spark("No transforms")
            spark_state = Spark("Analytical Stream")

        argo = Argocd("Gitops")
        argo >> spark_state
        argo >> spark_reload
        with Cluster("Dev"):
            code = Code("Dev App")
            code >> argo
            code >> argo

        firestore = Firestore("Cache/upsert")
        spark_persist >> kafka_storage
        kafka_storage >> spark_reload
        kafka_input >> spark_state
        kafka_input >> spark_persist
        spark_state >> firestore
        spark_reload >> firestore
        spark_state >> kafka_output
        spark_reload >> kafka_output

    firestore >> Python("python sdk")
