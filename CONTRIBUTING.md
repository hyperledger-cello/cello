[//]: # (SPDX-License-Identifier: CC-BY-4.0)

## Introduction

The project employs [GitHub](https://github.com/hyperledger-cello/cello) as the code commit/review system.

In brief, if you want to contribute, create or find some [GitHub Issues](https://docs.github.com/en/issues) and submit changes via [GitHub Pull Requests](https://docs.github.com/en/pull-requests).

## Questions and discussions

* [Wikipage](https://lf-hyperledger.atlassian.net/wiki/spaces/cello/overview): Lots of information and documentation about the project, e.g., meeting schedule, design doc.
* [Mail List](mailto:cello@lists.lfdecentralizedtrust.org): General technical topics with Cello project.

## Code Commit Steps

1. Fork the repository

Click the "Fork" button at the top right of the repository page.

2. Clone the project to your working directory.

```bash
$ git clone https://github.com/<your-username>/cello.git
$ cd cello
```

3. Config your git name and email if not setup previously.

```bash
$ git config user.name "your name"
$ git config user.email "your email"
```

4. Create a feature branch

Always create a meaningful branch name off main:

```bash
$ git checkout -b feature/awesome-feature
```

5. After modifying the code, run `make check` to make sure all the checking is passed.

```bash
$ make check
  ...
  py27: commands succeeded
  py30: commands succeeded
  py35: commands succeeded
  flake8: commands succeeded
  congratulations :)
```

6. Commit your code with `-s` to sign-off, and `-a` to automatically add changes (or run `git add .` to include all changes manually).

```bash
$ git commit -s -a
```

Example commit msg may look like:

```bash
A short description of your change with no period at the end

You can add more details here in several paragraphs, but please keep each line
width less than 80 characters. A bug fix should include the issue number.

Signed-off-by: Your Name <committer@email.address>
```

6. Open a PR on https://github.com/hyperledger-cello/cello/pulls.

After the ci checking passed, wait for reviewers to approve it. The patch will be merged into the `main` branch after passing the review.

If you need to refine the patch further as the reviewers may suggest, you can change on the same branch, and commit the new code, and then re-request review.

<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.
