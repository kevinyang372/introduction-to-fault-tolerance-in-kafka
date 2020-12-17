# Introduction to Fault Tolerance in Kafka With Experiments

Modern applications are composed of many small microservices, an architecture design which breaks down one application into a suite of independent deployable services (more more detail see [here](https://en.wikipedia.org/wiki/Microservices)). As the number of microservices components grow with increasing demand and complexity of the application, so does the scale of point to point data pipelines that connect different microservices. For example, the backend recommendation system module may request information from various front-end components while in return front-end needs the results from the ML module to update its user interface. However, since the transfer of data between different services have completely different requirements and volume, these pipelines are very hard to maintain and scale.

![image](https://user-images.githubusercontent.com/30107576/102417968-aed6b500-3fb1-11eb-85f8-5b463b76beca.png)
_Figure 1: An example of point-to-point data pipeline design with microservices._

Apache Kafka is a distributed messaging system designed for solving the growing complexity problem in data pipelining between microservices. It provides a unified data-agnostic interface that builds around the concept of "events." An event records the fact that "something happened" in the world or the application. Unlike the traditional conception of organizing data into tables, Kafka considers each event as an immutable truth. As a result, it successfully abstracts away the complicated details of data types and maintaining consistency, allowing the delivery service to be operated in a distributed fashion.

![image](https://user-images.githubusercontent.com/30107576/102418077-e8a7bb80-3fb1-11eb-9368-7b18ac0312f5.png)
_Figure 2: Using Apache Kafka for data delivery between microservices._

Overtime, Apache Kafka has proven to be robust against various component and network failures thanks to its fault tolerance policies in place. In this tutorial, we are going to experiment with some of the real life failure scenarios locally and examine how Kafka handles each of them.

## Partitions and Topics

One potentially confusing aspect in Kafka is the distinguishment between partitions and topics. From a high-level perspective, the topic represents the category of a specific event. In practice, topics as to events could be thought of as tables as to databases -- it is a means of classifying data for services to know which events they should consume. When producing events for Kafka, it is required to specify the topic each one of them belongs.

Topics are further split into partitions. While creating a topic, one can specify the number of partitions in a topic. Partition is the key to parallelization in Kafka as events could be consumed from different partitions within the same topic simultaneously. However, it is also worth noticing that orders are not maintained across different partitions -- therefore, one should always assign events requiring in-order processing to one partition.

## Key Components

Before diving into the experiments, it is crucial first to understand the overall structure of the system. Apache Kafka consists of four key components: producers, consumers, brokers, and Zookeeper.

The __producer__ is an application or service that writes events to Kafka. The client library for producers will specify the topic (provided by the application) and partition (provided or automatically generated) to commit the event to. Optionally, the application could assign a key value for each event: events with the same key will always go to the same partition as long as the number of partitions remains unchanged.

The __consumer__ is an application or service that receives events from Kafka. Individual consumers could be grouped into __consumer groups__. Within each consumer group, one consumer will read events from a set of partitions. However, messages in one partition will only be consumed once by one single consumer group.

__Brokers__ are units for storing Kafka events. Each broker contains multiple partitions from one or more topics but could only store one of the replicates from a particular partition. When a partition has multiple replicates, one broker will become the leader. Only leader broker could receive and service events. Users are able to scale Kafka in availability and fault tolerance by increasing the number of brokers and creating more replicates for every partition.

The __Zookeeper__ monitors the status of each broker. In case of a component or network failure, Zookeeper is also responsible for facilitating a leader election and re-assigning the read and write traffic to the newly elected leader.

A typical workflow in Kafka looks like the following:
1) The producer commits a message to a specific event topic.
2) The message is then recorded and appended to a partition in the brokers.
3) The active consumers subscribed to the partition will consume the message.  

## Prerequisites
Apache Kafka is based on Java. To compile and get Kafka up and running, we need to have JVMs installed in the system. If you don't have one, you could download
it [here](https://www.oracle.com/java/technologies/javase-jdk15-downloads.html)

Then check out this github repository for the config files and producer / consumer code. Install all the necessary dependencies for running the experiment:

    $ pip install -r requirements.txt

Apache Kafka is supported and maintained by multiple organizations. We could download the most up-to-date version from 
[Apache foundation](https://kafka.apache.org/downloads). Once downloaded, we first need to unzip and compile the package __within the local repository folder__.

Unzip the package:

    $ tar -xf kafka-2.6.0-src.tgz

Compile to binary if needed:

    $ cd kafka-'version number'-src && ./gradlew jar -PscalaVersion=2.13.2

## Starting Kafka
Kafka relies on [zookeeper](https://zookeeper.apache.org/) for managing all its broker nodes. So let's first get a zookeeper node up and running. Inside the unzipped kafka folder _(should be `kafka-'version number'-src`)_:

    $ bin/zookeeper-server-start.sh ../config/zookeeper.properties
    
Now we could initiate the broker nodes which are the heart of the Kafka system for delivering messages. To showcase the distributed nature of Kafka, we are going to start three broker nodes:
    
    $ bin/kafka-server-start.sh ../config/server.0.properties
    $ bin/kafka-server-start.sh ../config/server.1.properties
    $ bin/kafka-server-start.sh ../config/server.2.properties

Feel free to setup more broker nodes if needed. You could create additional ones by copying the server properties file and modifying the following sections:
```
# the following attributes should all be unique

broker.id=(number)
listeners=PLAINTEXT://:(port)
log.dirs=../tmp/kafka-logs-(id)
```

After confirming all the brokers have successfully been initiated, we also need to create topics for producers to deliver messages to:

    $ bin/kafka-topics.sh --create --topic my-kafka-topic --zookeeper localhost:2181 --partitions 3 --replication-factor 2
    
The `partitions` keyword decides the number of brokers you want your message to be split between. We chose three here as it is the number of broker nodes we brought up. The `replication-factor` tells Kafka how many times a message should be replicated. Setting it to two avoids losing the message immediately if the broker responsible for delivering accidentally goes down.

With Kafka up and running, we could start the producer and consumer that is currently just delivering simple dummy texts. Run the following code __in the root directory of the repository__:
    
    $ python producer.py
    $ python consumer.py

If you see the consumer process starts printing out log messages like below, congradulations you have successfully set up the Kafka system locally!
```
Consumed message from producer: ConsumerRecord(topic='foo', partition=1, offset=422457, timestamp=1605823820159, timestamp_type=0, key=None, value=b'1605823820.15889: message 5 from producer!', headers=[], checksum=None, serialized_key_size=-1, serialized_value_size=42, serialized_header_size=-1)
Consumed message from producer: ConsumerRecord(topic='foo', partition=1, offset=422458, timestamp=1605823821162, timestamp_type=0, key=None, value=b'1605823821.1625652: message 6 from producer!', headers=[], checksum=None, serialized_key_size=-1, serialized_value_size=44, serialized_header_size=-1)
Consumed message from producer: ConsumerRecord(topic='foo', partition=1, offset=422459, timestamp=1605823822167, timestamp_type=0, key=None, value=b'1605823822.167104: message 7 from producer!', headers=[], checksum=None, serialized_key_size=-1, serialized_value_size=43, serialized_header_size=-1)
...
```

To check the configurations of the topic, you could run:
    
    $ bin/kafka-topics.sh --describe --topic foo --zookeeper localhost:2181

For now, we should see that configuration to be something like this:
```
Topic: foo	PartitionCount: 3	ReplicationFactor: 2	Configs:
	Topic: foo	Partition: 0	Leader: 1	Replicas: 0,1	Isr: 1,0
	Topic: foo	Partition: 1	Leader: 1	Replicas: 1,0	Isr: 1,0
	Topic: foo	Partition: 2	Leader: 1	Replicas: 0,1	Isr: 1,0
```
    
## Experiments
It's time to mess up with the system. We designed three scenarios here for testing the level of fault tolerance Kafka has for component failures.

#### Scenario 1: Shutting Down One Broker
For this scenario, we shut down one out of the three broker nodes currently running. The system should continue to function correctly since we have two replications  for each message delivered. After acknowledging the broker failure, Kafka should be able to balance its load to the other two running nodes and avoid message loss.

After shutting down one broker server:
```
...
Consumed message from producer: ConsumerRecord(topic='foo', partition=0, offset=423846, timestamp=1605831903319, timestamp_type=0, key=None, value=b'1605831903.319744: message 46 from producer!', headers=[], checksum=None, serialized_key_size=-1, serialized_value_size=44, serialized_header_size=-1)
Consumed message from producer: ConsumerRecord(topic='foo', partition=0, offset=423847, timestamp=1605831904322, timestamp_type=0, key=None, value=b'1605831904.322156: message 47 from producer!', headers=[], checksum=None, serialized_key_size=-1, serialized_value_size=44, serialized_header_size=-1)
Consumed message from producer: ConsumerRecord(topic='foo', partition=2, offset=422961, timestamp=1605831905324, timestamp_type=0, key=None, value=b'1605831905.324097: message 48 from producer!', headers=[], checksum=None, serialized_key_size=-1, serialized_value_size=44, serialized_header_size=-1)
...
```

The topic configuration now looks like:
```
Topic: foo	PartitionCount: 3	ReplicationFactor: 2	Configs:
	Topic: foo	Partition: 0	Leader: 0	Replicas: 0,1	Isr: 0
	Topic: foo	Partition: 1	Leader: 0	Replicas: 1,0	Isr: 0
	Topic: foo	Partition: 2	Leader: 0	Replicas: 0,1	Isr: 0
```

Kafka automatically reassigns a new leader, preventing the entire system to come to a failover. When we boot server back, it will automatically start a fetcher to recover its up-to-date log from the leader:
```
[2020-11-19 17:01:34,673] INFO [Partition foo-0 broker=1] Log loaded for partition foo-0 with initial high watermark 423887 (kafka.cluster.Partition)
[2020-11-19 17:01:34,674] INFO [Partition foo-2 broker=1] Log loaded for partition foo-2 with initial high watermark 422998 (kafka.cluster.Partition)
[2020-11-19 17:01:34,674] INFO [Partition foo-1 broker=1] Log loaded for partition foo-1 with initial high watermark 422563 (kafka.cluster.Partition)
[2020-11-19 17:01:34,675] INFO [ReplicaFetcherManager on broker 1] Removed fetcher for partitions HashSet(foo-2, foo-0, foo-1) (kafka.server.ReplicaFetcherManager)
[2020-11-19 17:01:34,691] INFO [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Starting (kafka.server.ReplicaFetcherThread)
[2020-11-19 17:01:34,695] INFO [ReplicaFetcherManager on broker 1] Added fetcher to broker 0 for partitions Map(foo-2 -> (offset=422998, leaderEpoch=12), foo-1 -> (offset=422563, leaderEpoch=11), foo-0 -> (offset=423887, leaderEpoch=12)) (kafka.server.ReplicaFetcherManager)
```

#### Scenario 2: Shutting Down Two Brokers
Now let's try shutting down one more server, bringing the total number of brokers alive to one. Kafka should not be able to continue delivering messages as we specified a replication factor that is greater than the number of brokers and each replication should live in a different broker instance. As specified in the documentation: `For a topic with replication factor N, we will tolerate up to N-1 server failures without losing any messages committed to the log.`

In the experiment, we found that when two brokers are shut down, the consumer simply stops to receive any message from the producer.
```
Topic: foo	PartitionCount: 3	ReplicationFactor: 2	Configs:
	Topic: foo	Partition: 0	Leader: none	Replicas: 0,1	Isr: 0
	Topic: foo	Partition: 1	Leader: none	Replicas: 1,0	Isr: 0
	Topic: foo	Partition: 2	Leader: none	Replicas: 0,1	Isr: 0
```

However, the system could quickly comes back to operation once the two brokers are rebooted. All the logs that are produced in the period of server failover will be lost:
```
Consumed message from producer: ConsumerRecord(topic='foo', partition=1, offset=422787, timestamp=1605834836110, timestamp_type=0, key=None, value=b'1605834836.1103349: message 242 from producer!', headers=[], checksum=None, serialized_key_size=-1, serialized_value_size=46, serialized_header_size=-1)
Consumed message from producer: ConsumerRecord(topic='foo', partition=1, offset=422788, timestamp=1605834875232, timestamp_type=0, key=None, value=b'1605834875.232121: message 281 from producer!', headers=[], checksum=None, serialized_key_size=-1, serialized_value_size=45, serialized_header_size=-1)
```

#### Scenario 3: Shutting Down Zookeeper
Zookeeper is responsible for keeping track of the status of the broker nodes and electing a new leader if the leader node fails. Therefore, shutting down the zookeeper node should not cause problem if all the broker nodes are up and running. However, it comes at a risk of systematic failover if some Kafka broker node fails without the recovery mechanism from zookeeper.

After shutting down the zookeeper, as expected, the messages are still being delivered between the producer and consumer. An interesting observation is that now we are not able to shut down the broker nodes gracefully (with `CTRL C`) as it couldn't discover the zookeeper:
```
[2020-11-19 17:30:37,383] INFO Opening socket connection to server localhost/127.0.0.1:2181. Will not attempt to authenticate using SASL (unknown error) (org.apache.zookeeper.ClientCnxn)
[2020-11-19 17:30:37,385] INFO Socket error occurred: localhost/127.0.0.1:2181: Connection refused (org.apache.zookeeper.ClientCnxn)
```

Once we put zookeeper back into operation, we could see that the messaging system will recovery immediately.

## CAP
The CAP theorem states that we could move in either of the two directions when configuring a distributed system:
* Consistency + Partition (CP)
* Availability + Partition (AP)

We can't achieve both at the same time. Kafka does have both flavors in its design but it doesn't ensure both consistency and availability to 100%.
* Availability: The system will stop delivering messages if the number of servers available falls below the specified replication factor as shown in scenario 2 in the experiment.
* Consistency: There could be differences in the state of log between servers. However, the system is eventually consistent as the broker with an out-of-date log will try fetching updates from its leader with the latest log.

That being said, Kafka allows users to tune the priority based on whichever aspect is more important to them. For example, user could modify the `In-sync Replica (ISR)` parameter to adjust the minimum number of replicas that need to be synced up for Kafka to acknowledge a message has been successfully synced. Lowering this parameter could increase the availability of the system but comes at a cost of replicas may not necessarily all be synced.

For more information on how to optimize consistency versus availability, you could check out [this](https://docs.cloudera.com/documentation/kafka/latest/topics/kafka_ha.html) post written by Cloudera.
