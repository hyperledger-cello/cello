# Lesson 2: Server

By the end of this lesson, you'll be able to set up a *Hyperledger Cello* server on your computer.

To do so, we'll set up 3 components of it: dashboard, database, and the api engine.

!!! info
    See also: [*Concepts*](../concepts.md).

## Image
### Dashboard
First, we'll need a dashboard for our server, which is the UI for us.

Thus, we have to build its image by running:

```bash
make dashboard
```

The image will be tagged as `hyperledger/cello-dashboard:latest`.

This step can take a while because it builds the `node_module` via `yarn install`.

### Database
We'll directly use the official PostgreSQL image as our database, so there is no need to build another one.

### API Engine
Next, we'll build the center of our *Hyperledger Cello* server, which is the *api engine*.

```bash
make api-engine
```

The image will be tagged as `hyperledger/cello-api-engine:latest`.

This step can take a while because it has to install all the dependencies needed for the engine.

## Start the Server

Finally, we can start the server by:

```bash
make server
```

!!! tip
    By doing so, you deploy the server with a pre-written docker compose file `bootup/docker-compose-files/docker-compose.server.dev.yml`. Nevertheless, You can actually deploy the server however you like if you want to write your own docker compose file with your own configurations. It's all up to you!

If nothing goes wrong, you should see 3 containers running on your computer by executing

```bash
docker ps
```

They should be named `cello-dashboard`, `cello-api-engine`, `cello-postgres` respectively.

Go to [http://0.0.0.0:8081](http://0.0.0.0:8081) (replace the hostname with your connectable host e.g. [http://localhost:8081](http://localhost:8081)).

If you can see the login page on your browser, you're good to go.

## Conclusion
That's it! You have successfully run a *Hyperledger Cello* server on your computer🎉.

In the next lesson, we'll talk about how you can run an agent for it.

See you then👋!

!!! info "P.S. The "Quickstart" Way"
    Alternatively, you can run
    ```bash
    make local
    ```

    to set up a *Hyperledger Cello* **server and agent** in the same place as quick as possible.

    However, in order to give you a deeper understanding of how everything works, 
    we instead walked through the entire setup step-by-step in this tutorial.
