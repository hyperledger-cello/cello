# Lesson 4: User & Organization

Finally! After the previous lessons, you now are ready to enter and use *Hyperledger Cello*🎉!

Remember the *Hyperledger Cello* server you built in the [lesson 2](./server.md)?

By the end of that lesson, you should be able to enter [http://0.0.0.0:8081](http://0.0.0.0:8081) to see the login page.

Now go back to it because we're going to enter the server.

## Register

The site asks for your email and password to login, but since we haven't registered before, just click on the "register" first.

Once you switch to the registration form, you may notice that there is an admonition on it:

> This registration form is only for setting up a new organization and its first administrator. If your organization already exists, please ask your administrator to create your account.

It means that the registration is actually for **organizations**, and it will create a user for it incidentally to make sure that there won't be an organization without a user can login.

In *Hyperledger Cello*, every user must belong to an organization just like they does in *Hyperledger Fabric*.

To join an existing organization afterwards, ask its administrators to register you. Remember, a user can belong to only one organization.

Now, fill in the form, so we can go to the next step. You must name your organization like hostnames (e.g. "org1.cello.com") because it will be used as a part of your *node* hostnames. (We'll talk about *nodes* in the following lessons.)

You should see the "Register successfully!" message once you finish. Then, go to the login page and login with the email and password you just registered!

## After login

You can see the 2 concepts we talk about in this lesson by going to the "Organization" and "User" managerment page. You can see all organizations and users there.

Additionally, you can start invite others to your organization by registering them on the user management page.

## Conclusion

That's it! You have successfully created your organization and register a user🎉!

In the next lesson, we'll talk about how you can connect you server with your agent.

See you then👋!

!!! info "P.S. The "default" user"
    You may have noticed that on the user management page, there is another user named "admin" created besides the user you just registered for yourself. That's the "default" user. The default user can't operate anything because it has no organization, but it allows one to login a *Hyperledger Cello* server to wander around and check if it's OK.

    The default user email and password is assigned by the environment varables `API_ENGINE_ADMIN_EMAIL` and `API_ENGINE_ADMIN_PASSWORD` of the api engine container. By default, they're `admin@cello.com` and `pass`.
