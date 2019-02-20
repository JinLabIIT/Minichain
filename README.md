# Minichain

Minichain is a blockchain emulator that provides container-based emulation for blockchain application and network environment. You can evaluate the performance of blockchain system under different host-to-host network conditions.

## Getting Started

### Prerequisites

If you want to use virtual time component, it only supports ubuntu-14.04 so far. 

### Installing

#### Mininet

We modify part of Mininet's code to support virtual time. Please use following instructions to install.

```
$ git clone https://github.com/xwu64/mininet
$ cd mininet
$ util/install.sh
```


#### Minichain

```
$ cd
$ git clone https://github.com/xwu64/Minichain
$ cd Minichain
$ sudo python setup.py install
```

#### Virtual time

Follow the instruction in the repository below.

```
https://github.com/littlepretty/VirtualTimeKernel
```

#### Go-Ethereum

Follow the instruction in the repository.

```
https://github.com/ethereum/go-ethereum
```


## Running the tests

### Network performance evaluation

For evaluating host-to-host delay

```
$ cd examples/network_evaluate
$ sudo python delay.py
```

For evaluating host-to-host throughput

```
$ cd examples/network_evaluate
$ sudo python bw.py
```

### Application evaluation

For reproducing experiments in paper.

```
$ cd examples/geth_evaluate
$ sudo python block_dist.py
```
