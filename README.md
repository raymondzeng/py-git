Py-git
===
A git clone in Python. 

How to Use
===
Initiate a directory as a py-git repo
`./vcs init`

Take a snapshot of the current state (equiv. to git add -A && git commit)
`./vcs snap [-m <message>]`

Checkout an older snapshot (equiv. to git checkout <filename>)
`./vcs checkout <version>`

Checkout the last snapshot
`./vcs last`

Print the version number of the current snapshot
`./vcs current`

Print the log of snapshots including timestamps and messages (git log)
`./vcs log`

Help
`./vcs --help`