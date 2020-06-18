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

As explained in [HA Redis Cluster], use `redis-cli` to check both read and write:

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

Let's shutdown non-primary workers, first.  We'll shutdown the non-primary worker through
`virsh shutdown` and see if [haproxy] correctly manage the failover.

With the `redis-cli info replication`, we can get the master node:

```sh
redis-cli -h head10 -p 6379 info replication |grep master_host
master_host:172.31.255.12
```

Okay, `work12` is the master now.  Let's shutdown `woke13` to see if `haproxy` detect
it and avoid talking to the failed worker:

```sh
sudo virsh shutdown work13
Domain work13 is being shutdown
```

Override the previous key:

```sh
for i in {1..10}; do redis-cli -h head10 -p 6380 set hello$i "great world$i"; done
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

And make sure we get the new value:

```sh
for i in {1..10}; do redis-cli -h head10 -p 6379 get hello$i; done
"great world1"
"great world2"
"great world3"
"great world4"
"great world5"
"great world6"
"great world7"
"great world8"
"great world9"
"great world10"
```

Cool.  Let's restart `work13` and see if it works great, too:

```sh
sudo virsh start work13
```

and the read:

```sh
for i in {1..10}; do redis-cli -h head10 -p 6379 get hello$i; done
"great world1"
"great world2"
"great world3"
"great world4"
"great world5"
"great world6"
"great world7"
"great world8"
"great world9"
"great world10"
```

### Master failover

#### Machine level failover

For the master failover, it seems the machine wide failover doesn't work,
as `redis-sentinel` can't detect it correctly:

```sh
sudo virsh shutdown work12
```

```sh
for i in {1..10}; do redis-cli -h head10 -p 6379 info replication | grep master_host; done
master_host:172.31.255.12
master_host:172.31.255.12
master_host:172.31.255.12
master_host:172.31.255.12
master_host:172.31.255.12
master_host:172.31.255.12
master_host:172.31.255.12
master_host:172.31.255.12
master_host:172.31.255.12
master_host:172.31.255.12
```

```
for i in {1..10}; do redis-cli -h head10 -p 6380 set hello$i world$i; done
Error: Server closed the connection
Error: Server closed the connection
Error: Server closed the connection
Error: Server closed the connection
Error: Server closed the connection
Error: Server closed the connection
Error: Server closed the connection
Error: Server closed the connection
Error: Server closed the connection
Error: Server closed the connection
```

#### Process level failover

But the [redis] process level failover does work:

```sh
ssh work12 sudo systemctl kill --signal=SIGKILL redis
```

and write:


```sh
for i in {1..10}; do redis-cli -h head10 -p 6380 set hello$i "definitely the great world$i"; done
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

and read:

```sh
for i in {1..10}; do redis-cli -h head10 -p 6379 get hello$i; done
"definitely the great world1"
"definitely the great world2"
"definitely the great world3"
"definitely the great world4"
"definitely the great world5"
"definitely the great world6"
"definitely the great world7"
"definitely the great world8"
"definitely the great world9"
"definitely the great world10"
```

I'll take a look at the machine level failover and update the result.

Happy Hacking!

[circleci]: https://circleci.com/gh/keithnoguchi/redis-on-air.svg?style=svg
[ha redis cluster]: https://www.willandskill.se/en/setup-a-highly-available-redis-cluster-with-sentinel-and-haproxy/
[macbook air]: https://github.com/keithnoguchi/arch-on-air
[kube-on-air]: https://github.com/keithnoguchi/kube-on-air
[haproxy]: https://github.com/haproxy/haproxy
[redis]: https://github.com/antirez/redis
