# Lesson 5: Agent, Network, & Node

Now, you're ready to connect your server with your agent.

## Agent

To do that, please login to your server and go to the agent management page.

Click on the "New" button to register a new agent with a URL linked to your agent host. The default agent port is `5001`.

!!! info
    Even if you register the agent successfully, it doesn't mean that the server can access the agent successfully. The server will only try to connect the agent when it has to operate *nodes*, and this will happen later in this lesson when we create a *network*.

## Nodes

### Image

Compared to the usual pratice of *Hyperledger Fabric*, *Hyperledger Cello* doesn't use the official peer and orderer images to deploy nodes. Instead, *Hyperledger Cello* uses its own {++customized++} *Hyperledger Fabric* node images, which combines all *Hyperledger Fabric* binaries into one single image.

To build that, run

```bash
make fabric
```

The image will be tagged as `hyperledger/fabric:2.5.10`.

!!! info "The "Quickstart" way"
    The quickstart `make local` command we mentioned in [lesson 2](./server.md) and [lesson 3](./agent.md) will also build the node image for you.

### Create peers and orderers

!!! info
    If you don't know what *peers* and *orderers* are, please check out [*Peers*](https://hyperledger-fabric.readthedocs.io/en/latest/peers/peers.html).

Go to the node management page and click on the "New" button. You can choose to create either a *peer* or an *orderer* and name it.

To create a channel in the following lessons, you must create at least 1 peer and 1 orderer.

You should name them like hostnames just as you do for your organization because their names will also be used as a part of their hostnames.

## Network

You may notice that currently the status of your nodes are "created", and you don't see any container like *Hyperledger Fabric* nodes
running on your agent host. That's because the server **won't ask agents to deploy nodes until they're in a network**.

Thus, you have to create a *network* to place your *nodes*.

!!! info
    *Network* actually derives from a deprecated idea *system channel* in *Hyperledger Fabric*, which means it also will be deprecated in the near future. However, we still need it here to run our nodes currently.

Go to the network management page and click on the "New" button to create a network.

After you create a network successfully, even though it doesn't seem like there is anything happening, you can go to the node management page to see if your node status turns to green with a "running" label. Please wait about 5 minutes if you don't see any change. After that, there may be something wrong in your deployment. You can check the container logs by executing [the `docker logs` command](https://docs.docker.com/reference/cli/docker/container/logs/) with the api engine or agent container or consider [contacting us](../../#communication-channels).

Otherwise, you should see your nodes running as containers on your agent host by executing

```bash
docker ps
```

!!! info
    A peer container will be named as the peer name concatenated with the organization name.

    An orderer container will be named as the organization name with its first part replaced with the orderer name.

    For example, if there is an organization named "org1.cello.com" with a peer named "peer1" and an orderer named "orderer1", their containers should be named as "peer1.org1.cello.com" and "orderer1.cello.com".

    Such a naming method emphasizes that an orderer doesn't solely belong to its organization in a *Hyperledger Fabric* network.

## Conclusion

That's it! You have successfully connected your *Hyperledger Cello* server with your agent🎉!

Moreover, you also managed to deploy some *Hyperledger Fabric* running nodes!

In the next lesson, we'll talk about how you can create a *channel* with them.

See you then👋!

!!! note
    **Network* is not *Blockchain**, and there is no block on it. *Network* is just an abstract idea about what connects between organization *nodes*.
