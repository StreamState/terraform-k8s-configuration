from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.queue import Kafka
from diagrams.gcp.database import Firestore
from diagrams.onprem.analytics import Spark
from diagrams.gcp.storage import Storage
from diagrams.gcp.compute import GKE
from diagrams.programming.language import Python
from diagrams.gcp.devtools import Code
from diagrams.onprem.gitops import Argocd
from diagrams.firebase.develop import Hosting

with Diagram("StreamStateLogical", show=False):
    kafka_input = Kafka("Confluent Kafka")
    kafka_output = Kafka("Confluent Kafka")
    with Cluster("Dev Environment"):
        code = Code("Dev App")

    with Cluster("Databases"):
        firestore = Firestore("Cache/upsert")

    with Cluster("StreamState cluster"):
        kafka_storage = Storage("Persisted historic data")
        with Cluster("Spark Replay"):
            spark_reload = Spark()
        with Cluster("Spark App"):
            spark_app = Spark()
        with Cluster("Spark Persist"):
            spark_persist = Spark()
        with Cluster("Gitops"):
            argo = Argocd()
    argo >> spark_app
    argo >> spark_persist
    argo >> spark_reload

    spark_persist >> kafka_storage
    kafka_storage >> Edge(label="load backfill data") >> spark_reload
    kafka_input >> spark_persist
    kafka_input >> spark_app
    spark_app >> kafka_output
    spark_reload >> kafka_output
    code >> Edge(label="code") >> argo
    spark_app >> firestore
    spark_reload >> firestore
    firestore >> Python("python sdk")

with Diagram("StreamStateArchitecture", show=False):

    with Cluster("Dev Environment"):
        gke_dev = GKE("Dev GKE cluster")

    with Cluster("Streamstate home site"):
        main_site = Hosting("Streamstate.io")

    with Cluster("Databases"):
        firestore = Firestore("Cache/upsert")

    with Cluster("StreamState cluster"):
        # with Cluster("Replay"):
        gke_streaming = GKE("Streaming GKE cluster")
        persisted_data = Storage("Persisted historic data")
        # oidc =
    (
        gke_dev
        >> Edge(label="code")
        >> gke_streaming
        >> Edge(label="transformed data for caching")
        >> firestore
    )
    main_site >> Edge(label="oicd id/secret") >> firestore
    firestore >> Edge(label="oicd id/secret") >> gke_streaming
    persisted_data >> gke_streaming
    firestore >> Python("python sdk")
