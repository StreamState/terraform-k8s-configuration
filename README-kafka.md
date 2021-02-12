# setup an example kafka to test spark streaming

## Zookeeper
sudo docker run -d \
   --net=host \
   --name=zk-1 \
   -e ZOOKEEPER_SERVER_ID=1 \
   -e ZOOKEEPER_CLIENT_PORT=22181 \
   -e ZOOKEEPER_TICK_TIME=2000 \
   -e ZOOKEEPER_INIT_LIMIT=5 \
   -e ZOOKEEPER_SYNC_LIMIT=2 \
   -e ZOOKEEPER_SERVERS="localhost:22888:23888;localhost:32888:33888;localhost:42888:43888" \
   confluentinc/cp-zookeeper:5.0.0

sudo docker run -d \
   --net=host \
   --name=zk-2 \
   -e ZOOKEEPER_SERVER_ID=2 \
   -e ZOOKEEPER_CLIENT_PORT=32181 \
   -e ZOOKEEPER_TICK_TIME=2000 \
   -e ZOOKEEPER_INIT_LIMIT=5 \
   -e ZOOKEEPER_SYNC_LIMIT=2 \
   -e ZOOKEEPER_SERVERS="localhost:22888:23888;localhost:32888:33888;localhost:42888:43888" \
   confluentinc/cp-zookeeper:5.0.0


sudo docker run -d \
   --net=host \
   --name=zk-3 \
   -e ZOOKEEPER_SERVER_ID=3 \
   -e ZOOKEEPER_CLIENT_PORT=42181 \
   -e ZOOKEEPER_TICK_TIME=2000 \
   -e ZOOKEEPER_INIT_LIMIT=5 \
   -e ZOOKEEPER_SYNC_LIMIT=2 \
   -e ZOOKEEPER_SERVERS="localhost:22888:23888;localhost:32888:33888;localhost:42888:43888" \
   confluentinc/cp-zookeeper:5.0.0


for i in 22181 32181 42181; do
  sudo docker run --net=host --rm confluentinc/cp-zookeeper:5.0.0 bash -c "echo stat | nc localhost $i | grep Mode"
done 

## Kafka nodes

sudo docker run -d \
    --net=host \
    --name=kafka-1 \
    -e KAFKA_ZOOKEEPER_CONNECT=localhost:22181,localhost:32181,localhost:42181 \
    -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:29092 \
    confluentinc/cp-kafka:5.0.0

sudo docker run -d \
    --net=host \
    --name=kafka-2 \
    -e KAFKA_ZOOKEEPER_CONNECT=localhost:22181,localhost:32181,localhost:42181 \
    -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:39092 \
    confluentinc/cp-kafka:5.0.0

sudo docker run -d \
     --net=host \
     --name=kafka-3 \
     -e KAFKA_ZOOKEEPER_CONNECT=localhost:22181,localhost:32181,localhost:42181 \
     -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:49092 \
     confluentinc/cp-kafka:5.0.0

# create topic
sudo docker run \
  --net=host \
  --rm \
  confluentinc/cp-kafka:5.0.0 \
  kafka-topics --create --topic bar --partitions 3 --replication-factor 3 --if-not-exists --zookeeper localhost:32181

# describe topic

sudo docker run \
    --net=host \
    --rm \
    confluentinc/cp-kafka:5.0.0 \
    kafka-topics --describe --topic bar --zookeeper localhost:32181

# publish to topic

sudo docker run \
  --net=host \
  --rm confluentinc/cp-kafka:5.0.0 \
  bash -c "seq 42 | kafka-console-producer --broker-list localhost:29092 --topic bar && echo 'Produced 42 messages.'"

# read from the topic

sudo docker run \
 --net=host \
 --rm \
 confluentinc/cp-kafka:5.0.0 \
 kafka-console-consumer --bootstrap-server localhost:29092 --topic bar --from-beginning --max-messages 42
