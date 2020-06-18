# Redis-on-Air

[![CircleCI]](https://circleci.com/gh/keithnoguchi/workflows/redis-on-air)

Let's [HA Redis cluster] on [MacBook Air]!

- [Topology](#topology)
- [Deployment](#deployment)
- [Failover](#failover)

## Topology

It's a flat KVM topology, borrowed from [kube-on-air] repo.  Basically,
[haproxy] on the head node and [redis] on the worker nodes:

```
 +----------+ +-----------+ +------------+ +------------+
 |  head10  | |   work11  | |   work12   | |   work13   |
 | (haproxy)| |   (redis) | |   (redis)  | |   (redis)  |
 +----+-----+ +-----+-----+ +-----+------+ +-----+------+
      |             |             |              |
+-----+-------------+-------------+--------------+-------+
|                        air                             |
|                 (KVM/libvirt host)                     |
+--------------------------------------------------------+
```

## Deployment

```sh
ansible-playbook main.yaml | tail -6
PLAY RECAP ********************************************************************************************************************
head10                     : ok=4    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
work11                     : ok=8    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
work12                     : ok=7    changed=2    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
work13                     : ok=8    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

As explained in [HA Redis Cluster], let's use `redis-cli` to check
both read and write:

First write by talking to the port `6380`:

```sh
for i in {1..10}; do redis-cli -h head10 -p 6380 set hello$i world$i; done
OK
OK
OK
OK
OK
OK
OK
OK
OK
OK
```

and then read on port `6379`:

```sh
for i in {1..10}; do redis-cli -h head10 -p 6379 get hello$i; done
"world1"
"world2"
"world3"
"world4"
"world5"
"world6"
"world7"
"world8"
"world9"
"world10"
```

## Failover

Let's have fun with failover/HA!

### Non-master failover

Let's shutdown non-primary workers, first.  We'll shutdown the non-primary
worker through `virsh shutdown` and see if [haproxy] correctly manage the
failover.

With the `redis-cli info replication`, we can get the master node:

```sh
redis-cli -h head10 -p 6379 info replication |grep master_host
master_host:172.31.255.12
```

Okay, `work12` is the master now.  Let's shutdown `woke13` to see if `haproxy`
detect it and avoid talking to the failed worker:

```sh
sudo virsh shutdown work13
Domain work13 is being shutdown
```

Let's check `set`:

```sh
redis-benchmark -h head10 -p 6380 -q -e -t set
SET: 18885.74 requests per second
```

and `get`:

```sh
redis-benchmark -h head10 -p 6379 -q -e -t get
GET: 21172.98 requests per second
```

Cool.  Let's restart `work13` and see if it works great, too:

```sh
sudo virsh start work13
```

First `set`:

```sh
redis-benchmark -h head10 -p 6380 -q -e -t set
SET: 19451.47 requests per second
```

and `set`:

```sh
redis-benchmark -h head10 -p 6379 -q -e -t get
GET: 21958.72 requests per second
```

### Master failover

Let's shutdown the master worker and see how the read and write operation
failover.

```sh
sudo virsh shutdown work12
```

First `set`:

```sh
redis-benchmark -h head10 -p 6380 -q -e -t set
SET: 20746.89 requests per second
```

and `get`:

```sh
redis-benchmark -h head10 -p 6379 -q -e -t get
GET: 22977.94 requests per second
```

Happy Hacking!

[circleci]: https://circleci.com/gh/keithnoguchi/redis-on-air.svg?style=svg
[ha redis cluster]: https://www.willandskill.se/en/setup-a-highly-available-redis-cluster-with-sentinel-and-haproxy/
[macbook air]: https://github.com/keithnoguchi/arch-on-air
[kube-on-air]: https://github.com/keithnoguchi/kube-on-air
[haproxy]: https://github.com/haproxy/haproxy
[redis]: https://github.com/antirez/redis
