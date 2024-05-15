import iSparrow.repl as repl
import multiprocessing

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", True)
    repl.SparrowCmd().cmdloop()
