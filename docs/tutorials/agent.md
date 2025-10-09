# Lesson 3: Agent

By the end of this lesson, you'll be able to set up a *Hyperledger Cello* agent on your computer.

!!! note
    Remember: You can totally follow this lesson on a different machine from where you follow the last lesson i.e.
    The agents can be on a different machine from the server.

!!! info
    See also: [*Concepts*](../concepts.md).

## Image
### Agent

First, we have to build the image of the agent by running

```bash
make docker-rest-agent
```

The image will be tagged as `hyperledger/cello-agent-docker:latest`.

## Start the Agent

Next, start the agent by running

```bash
make agent
```

!!! tip
    By doing so, you deploy the agent with a pre-written docker compose file `bootup/docker-compose-files/docker-compose.agent.dev.yml` Nevertheless, You can actually deploy the agent however you like if you want to write your own docker compose file with your own configurations. It's all up to you!

If nothing goes wrong, you should see a container named `cello-docker-agent` running on your computer by executing

```bash
docker ps
```

## Conclustion
That's it! You have successfully run a *Hyperledger Cello* agent on your computer🎉.

In the next lesson, we'll talk about how you can create an organization and its first administrator.

See you then👋!

!!! info "P.S. The "Quickstart" Way"
    Just as mentioned in the [last lesson](./server.md), alternatively, you can run
    ```bash
    make local
    ```

    to set up a *Hyperledger Cello* **server and agent** in the same place as quick as possible.

    However, in order to give you a deeper understanding of how everything works, 
    we instead walked through the entire setup step-by-step in this tutorial.
