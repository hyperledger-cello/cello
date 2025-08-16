# Lesson 6: Channel & Chaincode

!!! bug
    Currently, this feature only works if the server is on the same host with agents i.e. **You can create channels only if all your *Hyperledger Cello* components aren't deployed across multiple hosts**.

    This is a serious bug, and we've noticed that. For the latest information about this issue, follow [#733](https://github.com/hyperledger-cello/cello/issues/733).

!!! info
    If you don't what channels are, please check out [Channels](https://hyperledger-fabric.readthedocs.io/en/release-2.5/channels.html).

!!! info
    If you don't what chaincodes are, please check out [Smart Contracts and Chaincode](https://hyperledger-fabric.readthedocs.io/en/release-2.5/smartcontract/smartcontract.html).

After all the previous 6 lessons, you now are ready to create your first ***Blockchain*** with *Hyperledger Cello*.

*Channel* is the closest concept to what a *blockchain* is known by the general public, or more specifically, a *private* blockchain, in the *Hyperledger Fabric* world.

In contrast, *Chaincode* is the closest concept to what a *smart contract* is known by the general public in the *Hyperledger Fabric* world.

## Create a Channel

Go to the channel management page and click on the "New" button.

Then, name the channel and choose your peers and orderers.

## Deploy a Chaincode

Mainly, there are 4 steps you should do when you deploy a chaincode

1. Package
2. Install
3. Approve (for your organization only)
4. Commit

Each step has its own meaning.

Without packaging, you can't install a chaincode on a peer.

Without installing, you can't approve a chaincode for your organization.

Without approving, you can't commit a chaincode to a channel.

Finally, without commiting, you can't use a chaincode to send transactions.

### Package

You have to do it yourself for this step. Please refer to [Package the smart contract](https://hyperledger-fabric.readthedocs.io/en/release-2.5/deploy_chaincode.html#package-the-smart-contract).

### Install

Go to the chaincode management page and click on the "New" button.

Upload your chaincode package from the last step.

The uploaded chaincode package ID will be shown as the label of it (assigned during packaging) and a hash value.

After that, click on the "Install" button shown on your chaincode.

### Approve

If nothing goes wrong, click on the "Approve" button then.

### Commit

Lastly, commit the chaincode by the "Commit" button.

## Conclusion

That's it! You have successfully created your first *Hyperledger Fabric* channel, which is your first *blockchain*, with *Hyperledger Cello*🎉!

Moreover, you also deployed your first *Hyperledger Fabric* chaincode, which is your first *smart contract*!

In the next lesson, we'll talk about how you can interact with it.

See you then👋!

!!! warning
    **You can't**. Currently you still can't interact with your chaincode through the *Hyperledger Cello*. Such a feature is still under development. Thus, there is no next lesson, but there will be one once the feature is finished😊!
