import os
from faunanet import repl

if __name__ == "__main__":
    cmd = repl.FaunanetCmd()

    run_cfg = os.environ.get("RUN_CONFIG", "")

    if run_cfg != "":
        cmd.do_start("--cfg=/home/faunanet/config/" + run_cfg)
    else:
        cmd.do_start("")

    cmd.wait_for_watcher_event(
        lambda _: cmd.watcher is not None and cmd.watcher.is_running,
    )

    cmd.do_status("")

    cmd.cmdloop()
