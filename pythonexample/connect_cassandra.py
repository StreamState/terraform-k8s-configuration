from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import os

import subprocess

cmd = "kubectl get secrets/cluster1-superuser -n cass-operator --template={{.data.password}} | base64 -d"
ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
password = ps.communicate()[0].decode("utf-8")

auth_provider = PlainTextAuthProvider(
    username="cluster1-superuser",
    password=password,
)
cluster = Cluster(["127.0.0.1"], port=30500, auth_provider=auth_provider)
session = cluster.connect()
rows = session.execute("SELECT firstname FROM cycling.cyclist_semi_pro")
for user_row in rows:
    print(user_row)
