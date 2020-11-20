# Kafka Tutorial

Apache Kafka is a distributed messaging system for event processing. Together with the growing traffic and features of modern application systems, the traditional method of maintaining a data lake for a pool of different logs and data becomes increasingly unfeasible due to its low maintainability. 

On contrast, Kafka reimagined modern application systems as various microservices producing and consuming "messages" instead of multiple separated and independent business layers. As a result, it successfully abstracts away the complicated details of data types and processing methods by generalizing them to "log messages" and builds a highly scalable and reliable distributed communication system for delivering the messages.

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
    
## Experiments
It's time to mess up with the system. We designed three scenarios here for testing the level of fault tolerance Kafka has for component failures.

#### Scenario 1: Shutting Down One Broker
For this scenario, we shut down one out of the three broker nodes currently running. The system should continue to function correctly since we have two replications  for each message delivered. After acknowledging the broker failure, Kafka should be able to balance its load to the other two running nodes and avoid message loss.

