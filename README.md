# Kafka Tutorial

## Prerequisites
Apache Kafka is based on Java. To compile and get Kafka up and running, we need to have JVMs installed in the system. If you don't have one, you could download
it [here](https://www.oracle.com/java/technologies/javase-jdk15-downloads.html)

Apache Kafka is supported and maintained by multiple organizations. We could download the most up-to-date version from 
[Apache foundation](https://kafka.apache.org/downloads). Once downloaded, we first need to unzip and compile the package

Unzip the package
```
$ tar -xf kafka-2.6.0-src.tgz
```

Compiling to binary if needed
```
$ cd kafka-2.6.0-src && ./gradlew jar -PscalaVersion=2.13.2
```
