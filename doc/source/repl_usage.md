# Using the Faunanet REPL
The `Faunanetlab` REPL (Read-Evaluate-Print loop) has been encountered already in {doc}`getting_started`. It's the main way to interact with a running `Faunanetlab` instance.
To get a list of available commands you can run `help` in a running REPL: 
```bash 
faunanetlab
(Faunanetlab) help 
set_up: set up iSparrow for usage...
start: start a watcher for analyzing incoming files in a directory ...
stop: stop a previously started watcher ...
pause: pause a running watcher
continue: continue a paused watcher
restart: restart an existing watcher
change_analyzer: change the analyzer of a running watcher ...
cleanup: cleanup the output directory of the watcher, assuring data consistency
status: get the current status of the watcher process
exit: leave this shell.
Commands can have optional arguments. Use 'help <command>' to get more information on a specific command.
```

Using a command with wrong arguments will print an explanatory error message, e.g. 
```bash
(Faunanetlab) start --cfg=~/path/to/some/config.yml 
Something in the start command parsing went wrong. Check your passed commands. Caused by:  Invalid input. Expected options structure is --name=<arg> with names [--cfg]
(Faunanetlab)
```
or 
```bash
(Faunanetlab) stop
Cannot stop watcher, no watcher present
``` 
When running a command, you may get additional output from other parts of `Faunanetlab` or its dependencies. This will not interfere with your ability to issue commands though. 

Passing of parameters always happens by passing a configuration file that contains the parameters expected by the respective method of the `Watcher` class. No parameters are 
currently exposed to be given directly on the REPL. This may change in the future, however.

```{important}
When exiting the REPL with `exit` or with a keyboard interrupt, the watcher process will be terminated too, so if you want to have a running instance you can connect or 
disconnect to and from, use a terminal multiplexer like tmux or use docker (see {doc}`using_faunanetlab_through_docker`).
```

