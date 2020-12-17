# Introduction to Fault Tolerance in Kafka With Experiments

Modern applications are composed of many small microservices, an architecture design which breaks down one application into a suite of independent deployable services (more more detail see [here](https://en.wikipedia.org/wiki/Microservices)). As the number of microservices components grow with increasing demand and complexity of the application, so does the scale of point to point data pipelines used to connect different microservices. For example, the backend recommender system module may request information from various front-end components, while in return the front-end needs results from the ML module to update its user interface. However, since the transfer of data between different services have completely different requirements and volume, these pipelines are very hard to maintain and scale.

![image](https://user-images.githubusercontent.com/30107576/102417968-aed6b500-3fb1-11eb-85f8-5b463b76beca.png)
_Figure 1: An example of point-to-point data pipeline design with microservices._

Apache Kafka is a distributed messaging system designed for solving the growing complexity problem in data pipelining between microservices. It provides a unified data-agnostic interface that builds around the concept of "events." An event records the fact that "something happened" in the world or the application. Unlike the traditional conception of organizing data into tables, Kafka considers each event as an immutable truth. As a result, it successfully abstracts away the complicated details of data types and consistency maintainence, allowing the delivery service to be operated in a distributed fashion.

![image](https://user-images.githubusercontent.com/30107576/102418077-e8a7bb80-3fb1-11eb-9368-7b18ac0312f5.png)
_Figure 2: Using Apache Kafka for data delivery between microservices._

Overtime, Apache Kafka has proven to be robust against various component and network failures thanks to its fault tolerance policies in place. In this tutorial, we are going to experiment with some of the real life failure scenarios locally and examine how Kafka handles each of them.

## Partitions and Topics

One potentially confusing aspect in Kafka is the distinguishment between partitions and topics. From a high-level perspective, the topic represents the category of a specific event. In practice, topics as to events could be thought of as tables as to databases -- it is a means of classifying data for services to know which events they should consume. When producing events for Kafka, it is required to specify the topic each one of them belongs.

Topics are further split into partitions. While creating a topic, one can specify the number of partitions in a topic. Partition is the key to parallelization in Kafka as events could be consumed from different partitions within one topic simultaneously. However, it is also worth noticing that orders are not maintained across different partitions -- therefore, one should always assign events requiring in-order processing to one partition.

## Key Components

Before diving into the experiments, it is crucial first to understand the overall structure of the system. Apache Kafka consists of four key components: producers, consumers, brokers, and Zookeeper.

The __producer__ is an application or service that writes events to Kafka. The client library for producers specifies the topic (provided by the application) and partition (provided or automatically generated) for each message and commits them to the brokers. Optionally, the application could assign a key value for each event: events with the same key will always go to the same partition as long as the number of partitions remains unchanged. One interesting attribute adjustable in configuring the producer is the ack (acknowledgement) value. It could take one of three possible values -- 0, 1, or all. In default ack is set to 1, meaning the producer will confirm a message has been delivered once it has been accepted by the leader of a partition. At the value of 0, the producer will not give any confirmations, while at the value of all the producer will only give a confirmation once the message has been synced to the leader and all the replicas. We will cover the ack value further in detail in the later discussion on CAP theorem.

The __consumer__ is an application or service that receives events from Kafka. Individual consumers could be grouped into __consumer groups__. Within each consumer group, every member consumer reads events from a set of partitions. However, messages in one partition will only be consumed once within one single consumer group. When a group is initialized to start consuming from a partition, it will always begin reading from the offset (a logical representation of the message ordering) of 0. Kafka also stores the offset of every consumer group which it has read.

__Brokers__ are units for storing Kafka events. Each broker contains multiple partitions from one or more topics but could only store one of the replicates from a particular partition. When a partition has multiple replicates, one broker will become the leader. Only leader broker could receive and service events. Users are able to scale Kafka in availability and fault tolerance by increasing the number of brokers and creating more replicates for every partition.

The __Zookeeper__ is a consensus service that is used to monitor and coordinate the broker nodes in Apache Kafka. Due to its crucial role in Kafka's fault tolerance, Zookeeper is usually setup as a distributed system itself with one leader and multiple followers. It has two main responsibilities:
* Detect the addition and removal of brokers and consumers
* Rebalance the consumer and broker nodes when the number of brokers or consumers changes. It is mainly achieved by re-electing leaders for the affected partitions.

To achieve those responsibilities, Zookeeper stores a list of different registries including:
* Broker registry: The broker’s host name and part, and the set of topics and partitions stored on it.
* Consumer registry: The consumer group to which a consumer belongs and the set of topics it subscribes to.
* Ownership registry: A list of consumers currently consuming from a particular partition.

A typical workflow in Kafka looks like the following:
1) The producer commits a message to a specific event topic.
2) The message is then recorded and appended to a partition in the brokers.
3) The active consumer groups subscribed to the partition will then consume the message.  

## Prerequisites
_Notice that the following tutorial is written in the __Mac__ environment._

Apache Kafka is based on Java. To compile and get Kafka up and running, we need to have JVMs installed in the system. If you don't have one, you could download
it [here](https://www.oracle.com/java/technologies/javase-jdk15-downloads.html).

Then check out [this](https://github.com/kevinyang372/introduction-to-fault-tolerance-in-kafka) Github repository for the config files and producer / consumer code. Install all the necessary dependencies for running the experiment:

    $ pip install -r requirements.txt

Apache Kafka is supported and maintained by multiple organizations. We could download all Kafka versions from 
[Apache foundation](https://kafka.apache.org/downloads). For this tutorial, we are going to use __version 2.6.0__ with scala __2.13__ and make sure to select the __binary downloads__ so we don't need to further compile the package. Once downloaded, we first need to unzip the package __within the local repository folder__.

Unzip the package:

    $ tar -xf kafka_2.13-2.6.0.tgz

## Starting Kafka
Kafka relies on [Zookeeper](https://zookeeper.apache.org/) for managing all its broker nodes. So let's first get a Zookeeper node up and running. Inside the unzipped kafka folder _(should be `kafka_2.13-2.6.0`)_:

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

    $ bin/kafka-topics.sh --create --topic foo --zookeeper localhost:2181 --partitions 3 --replication-factor 2
    
The `partitions` keyword decides the number of brokers you want your message to be split between. We chose three here as it is the number of broker nodes we brought up. If you brought up more broker nodes in the previous step, you could increase the number of partitions to match the number of broker nodes. The `replication-factor` tells Kafka how many times a message should be replicated. Setting it to two avoids losing the message immediately if the leader broker accidentally goes down.

With Kafka up and running, we could start the producer and consumer that is currently just delivering simple dummy texts. Run the following code __in the root directory of the repository__:
    
    $ python producer.py
    $ python consumer.py

If you see the consumer process starts printing out log messages like below, congradulations you have successfully set up the Kafka system locally! As discussed before, we could observe that messages with the same key value always go to the same partition.
```
Consumed message from partition 2: 1608169242.4790661: message 3 with key foo_5 from producer!
Consumed message from partition 1: 1608169243.481664: message 4 with key foo_4 from producer!
Consumed message from partition 0: 1608169244.486679: message 5 with key foo_1 from producer!
Consumed message from partition 2: 1608169245.487614: message 6 with key foo_2 from producer!
Consumed message from partition 2: 1608169246.489738: message 7 with key foo_5 from producer!
Consumed message from partition 0: 1608169247.495711: message 8 with key foo_1 from producer!
Consumed message from partition 0: 1608169248.498251: message 9 with key foo_1 from producer!
Consumed message from partition 0: 1608169249.501703: message 10 with key foo_1 from producer!
Consumed message from partition 2: 1608169250.5059142: message 11 with key foo_5 from producer!
...
```

To check the configurations of the topics and partitions, you could run:
    
    $ bin/kafka-topics.sh --describe --topic foo --zookeeper localhost:2181

For now, we should see that the configuration to be something like this:
```
Topic: foo	PartitionCount: 3	ReplicationFactor: 2	Configs:
	Topic: foo	Partition: 0	Leader: 1	Replicas: 1,0	Isr: 1,0
	Topic: foo	Partition: 1	Leader: 2	Replicas: 2,1	Isr: 2,1
	Topic: foo	Partition: 2	Leader: 0	Replicas: 0,2	Isr: 0,2
```

As both the producer and consumer code are wrapped in an infinite loop, to terminate any of the processes, you could use `CTRL C` to key interrupt the running Python program.
    
## Experiments
It's time to mess up with the system. We designed three scenarios here for testing the level of fault tolerance Kafka provides for component failures.

#### Scenario 1: Shutting Down One Broker
For this scenario, we shut down one out of the three broker nodes currently running. The system should continue to function correctly since we have two replications  for each message delivered. After acknowledging the broker failure, Kafka should be able to balance its load to the other two running nodes and avoid any message loss.

After shutting down one broker server with id = 2 (use `CTRL C` to terminate the process), the consumer is functioning as normal, which supports our hypothesis:
```
...
Consumed message from partition 2: 1608169579.229342: message 22 with key foo_5 from producer!
Consumed message from partition 2: 1608169580.2330618: message 23 with key foo_2 from producer!
Consumed message from partition 0: 1608169581.235913: message 24 with key foo_1 from producer!
Consumed message from partition 0: 1608169582.242093: message 25 with key foo_1 from producer!
Consumed message from partition 2: 1608169583.247047: message 26 with key foo_3 from producer!
...
```

The topic configuration now looks like:
```
Topic: foo	PartitionCount: 3	ReplicationFactor: 2	Configs:
	Topic: foo	Partition: 0	Leader: 1	Replicas: 1,0	Isr: 1,0
	Topic: foo	Partition: 1	Leader: 1	Replicas: 2,1	Isr: 1
	Topic: foo	Partition: 2	Leader: 0	Replicas: 0,2	Isr: 0
```

As we can see, for partitions with replicas on broker 2, now the in-sync replica (ISR) factor excludes broker 2 as it is curently shut-down. At the same time, we could still read messages from all three partitions from the consumer side. This is because after identifying the component failure, Kafka automatically re-assigns a new leader for partition 1, preventing the entire system to come to a failover. When we boot server back, it will automatically start a fetcher to recover its up-to-date log from the leader:
```
[2020-11-19 17:01:34,673] INFO [Partition foo-0 broker=1] Log loaded for partition foo-0 with initial high watermark 423887 (kafka.cluster.Partition)
[2020-11-19 17:01:34,674] INFO [Partition foo-2 broker=1] Log loaded for partition foo-2 with initial high watermark 422998 (kafka.cluster.Partition)
[2020-11-19 17:01:34,674] INFO [Partition foo-1 broker=1] Log loaded for partition foo-1 with initial high watermark 422563 (kafka.cluster.Partition)
[2020-11-19 17:01:34,675] INFO [ReplicaFetcherManager on broker 1] Removed fetcher for partitions HashSet(foo-2, foo-0, foo-1) (kafka.server.ReplicaFetcherManager)
[2020-11-19 17:01:34,691] INFO [ReplicaFetcher replicaId=1, leaderId=0, fetcherId=0] Starting (kafka.server.ReplicaFetcherThread)
[2020-11-19 17:01:34,695] INFO [ReplicaFetcherManager on broker 1] Added fetcher to broker 0 for partitions Map(foo-2 -> (offset=422998, leaderEpoch=12), foo-1 -> (offset=422563, leaderEpoch=11), foo-0 -> (offset=423887, leaderEpoch=12)) (kafka.server.ReplicaFetcherManager)
```

#### Scenario 2: Shutting Down Two Brokers
Now let's try shutting down one more server, bringing the total number of brokers alive to one. Kafka should not be able to fully deliver all messages as we specified a replication factor that is greater than the number of brokers and each replication should live in a different broker instance. As specified in the documentation: `For a topic with replication factor N, we will tolerate up to N-1 server failures without losing any messages committed to the log.`

In the experiment, we found that when two brokers are shut down, Kafka is no longer able to assign any leader to partition 1 as shown below.
```
Topic: foo	PartitionCount: 3	ReplicationFactor: 2	Configs:
	Topic: foo	Partition: 0	Leader: 0	Replicas: 1,0	Isr: 0
	Topic: foo	Partition: 1	Leader: none	Replicas: 2,1	Isr: 1
	Topic: foo	Partition: 2	Leader: 0	Replicas: 0,2	Isr: 0
```

While Kafka is still able to deliver messages that are in partition 0 and 2, it will fail to deliver message to partition 1 -- which currently has no leader nodes. From the producer side, we are able to see failed confirmations:
```
Successfully produced 1608170527.6380339: message 7 with key foo_3 from producer!!
Successfully produced 1608170528.6459231: message 8 with key foo_4 from producer!!
Failed to deliver 1608170529.6546838: message 9 with key foo_1 from producer!
Successfully produced 1608170530.762963: message 10 with key foo_5 from producer!!
```

On the consumer side, message 9 is indeed lost and not captured by the consumer:
```
Consumed message from partition 2: 1608170527.6380339: message 7 with key foo_3 from producer!
Consumed message from partition 2: 1608170528.6459231: message 8 with key foo_4 from producer!
Consumed message from partition 2: 1608170530.762963: message 10 with key foo_5 from producer!
```

All lost messages during the shut-down is not recoverable. However, the system could quickly comes back to operation once the two brokers are rebooted. Zookeeper is able to re-assign the leader to each partition:
```
Topic: foo	PartitionCount: 3	ReplicationFactor: 2	Configs:
	Topic: foo	Partition: 0	Leader: 1	Replicas: 1,0	Isr: 0,1
	Topic: foo	Partition: 1	Leader: 2	Replicas: 2,1	Isr: 1,2
	Topic: foo	Partition: 2	Leader: 0	Replicas: 0,2	Isr: 0,2
```

#### Scenario 3: Shutting Down Zookeeper
Zookeeper is responsible for keeping track of the status of the broker nodes and electing a new leader if the leader node fails. Therefore, shutting down the Zookeeper node should not cause problem if all the broker nodes are up and running. However, it comes at a risk of systematic failover if some Kafka broker node fails without the recovery mechanism supported by Zookeeper.

After shutting down the Zookeeper, we could no longer access some key information to the system like the leader node of partitions and availability of the nodes. This means if any of the brokers goes down, Kafka could come to a completely failover as Zookeeper could not help rebalance the traffic to the shut-down node and notify the corresponding producers and consumers. However, if none of the brokers go down at the duration of Zookeeper shut-down, Kafka should still function normally since the producers and consumers will remain their connection with the assigned brokers.

In the experiment, we could see that the messages are still being delivered between the producer and consumer. An interesting observation is that now we are not able to shut down the broker nodes gracefully (with `CTRL C`) as it couldn't discover the Zookeeper:
```
[2020-12-16 18:36:43,600] INFO Terminating process due to signal SIGINT (org.apache.kafka.common.utils.LoggingSignalHandler)
[2020-12-16 18:36:43,602] INFO [KafkaServer id=1] shutting down (kafka.server.KafkaServer)
[2020-12-16 18:36:43,603] INFO [KafkaServer id=1] Starting controlled shutdown (kafka.server.KafkaServer)
[2020-12-16 18:36:43,691] INFO Opening socket connection to server localhost/[0:0:0:0:0:0:0:1]:2181. Will not attempt to authenticate using SASL (unknown error) (org.apache.zookeeper.ClientCnxn)
[2020-12-16 18:36:43,691] INFO Socket error occurred: localhost/[0:0:0:0:0:0:0:1]:2181: Connection refused (org.apache.zookeeper.ClientCnxn)
[2020-12-16 18:36:43,798] INFO [ZooKeeperClient Kafka server] Waiting until connected. (kafka.zookeeper.ZooKeeperClient)
```

Once we put the Zookeeper back into operation, we could see that the messaging system will recovery immediately as the heartbeat confirmation with the Zookeeper returns successfully for the brokers. Now the Zookeeper rediscovers all the broker node and could continue to perform its role.
```
[2020-12-16 18:35:21,274] INFO Opening socket connection to server localhost/127.0.0.1:2181. Will not attempt to authenticate using SASL (unknown error) (org.apache.zookeeper.ClientCnxn)
[2020-12-16 18:35:21,274] INFO Socket error occurred: localhost/127.0.0.1:2181: Connection refused (org.apache.zookeeper.ClientCnxn)
[2020-12-16 18:35:23,304] INFO Opening socket connection to server localhost/[0:0:0:0:0:0:0:1]:2181. Will not attempt to authenticate using SASL (unknown error) (org.apache.zookeeper.ClientCnxn)
[2020-12-16 18:35:23,305] INFO Socket connection established, initiating session, client: /[0:0:0:0:0:0:0:1]:56830, server: localhost/[0:0:0:0:0:0:0:1]:2181 (org.apache.zookeeper.ClientCnxn)
[2020-12-16 18:35:23,314] INFO Session establishment complete on server localhost/[0:0:0:0:0:0:0:1]:2181, sessionid = 0x10005a515a40000, negotiated timeout = 18000 (org.apache.zookeeper.ClientCnxn)
```

## CAP
The CAP theorem states that it is impossible for a distributed data store to simultaneously provide more than two out of the following three guarantees:
* __Consistency__: Every read receives the most recent write or an error. An inconsistent system may return different results to different read requests.
* __Availability__: Every request receives a (non-error) response, without the guarantee that it contains the most recent write. A system with low availability could be returning all or mostly errors to every request in case of a network partition.
* __Partition Tolerance__: The system continues to operate despite an arbitrary number of messages being dropped (or delayed) by the network between nodes. This is not really an option for distributed systems as we want the system to continue functioning even during a network partition.

Since partition could not be an option to exclude, the CAP theorem ends up to be a choice between two options -- consistency and availability. We can't achieve both at the same time. Kafka does have both flavors in its design but it doesn't ensure either consistency or availability to 100%. In case of availability, the system will failed to deliver some of the messages if the number of servers available falls below the specified replication factor as shown in scenario 2 in the experiment. In case of consistency, there could be differences in the state of log between servers. However, the system is eventually consistent as the broker with an out-of-date log will try fetching updates from its leader with the latest log.

That being said, Kafka allows users to tune the priority based on whichever aspect is more important to them. Let's look at some examples in which the specific application may favor consistency or availability over another.
* In services like online machine learning modules, availability is more important than consistency as missing one or two data points will not drastically change the functioning of model training and predictions.
* In contrast, for services like payment and transaction, consistency is more important than availability as it touches on sensitive data and any failure could be significantly costly to recover from.

However, in neither of the two examples above we want to completely give up on the other aspect (e.g. it will be unreasonable to reject all payments when a small component failure happens in one of the data centers). Therefore, Kafka offers many parameters to change the tradeoffs between the two aspects in a linear rather than binary scale. One of them is the ack value mentioned before in the Key Components section. Changing the ack value to 0 will gaurantee higher availability as the producer does not need any confirmation from any of the brokers. But it also comes at a risk of losing the message completely due to failed delivery. On the contrary, having an ack value of all provides the highest consistency since it ensures the message has been synced to all replicas before returning confirmation. In theory, it is still possible that all of the leader and replica nodes could go down. However, when the number of minimum in-sync replicas (ISR) is set to a large value, the odds becomes almost impossible. In the following extended scenario, we experimented with adjusting minimum in-sync replicas value locally.

For more information on how to optimize consistency versus availability, you could check out [this](https://docs.cloudera.com/documentation/kafka/latest/topics/kafka_ha.html) post written by Cloudera.

#### Extended Scenario: Adjusting Minimum In-Sync Replicas
To address a wide range of use cases, Apache Kafka offers several parameters for users to adjust whether they want to optimize for accessibility or consistency. One of them is `minimum in-sync replica` -- the minimum number of replicas that need to be synced up for Kafka to acknowledge that a message has been successfully synced. Increasing this parameter could improve the consistency of the system by reducing the risk of failure over all of the replicas but comes at a cost of lower availability.

We could change the minimum in-sync replica value by running the following command. The `--alter` parameter allows us to update the configuration without restarting Zookeeper:

	$ bin/kafka-topics.sh --alter --zookeeper localhost:2181 --topic foo --config min.insync.replicas=2
	
Now, taking one server down, we could see that the producer side fails to confirm the delivery on many messages as the partition they belong to could not be replicated to enough brokers.
```
Successfully produced 1608173354.485804: message 1466 with key foo_2 from producer!!
Failed to deliver 1608173355.489635: message 1467 with key foo_3 from producer!
Successfully produced 1608173356.5009768: message 1468 with key foo_1 from producer!!
Failed to deliver 1608173357.505478: message 1469 with key foo_3 from producer!
Failed to deliver 1608173358.5097501: message 1470 with key foo_2 from producer!
Failed to deliver 1608173359.516491: message 1471 with key foo_2 from producer!
```

And the consumer on the other side also fails to receive the corresponding messages:
```
Consumed message from partition 2: 1608173354.485804: message 1466 with key foo_2 from producer!
Consumed message from partition 0: 1608173356.5009768: message 1468 with key foo_1 from producer!
Consumed message from partition 0: 1608173372.601995: message 1484 with key foo_1 from producer!
Consumed message from partition 0: 1608173389.712647: message 1501 with key foo_1 from producer!
Consumed message from partition 0: 1608173392.7440279: message 1504 with key foo_1 from producer
```

By increasing the minimum in-sync replicas value, Kafka now operates with lower availability as it rejects many of the messages that was deliverable in experiment 1. However, it also prevents the permenant data loss in experiment 2 from happening as an early warning is given to the producer for insufficient replication. The producer could implement a temporary store for the failed delivery and retry later.
