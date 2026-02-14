import sys
import os
import subprocess
import shutil
import shlex
import readline

PATH = os.getenv("PATH", "")
paths = PATH.split(":")
readline.clear_history()
last_history_written = 0
COMMANDS = ['echo', 'exit', 'type', 'pwd', 'cd', "history"]


def main():

    readline.set_completer(completer)
    readline.set_completer_delims('\t\n')
    readline.parse_and_bind('tab: complete')
    readline.set_completion_display_matches_hook(display_matches)
  # Wait for user input
    user_input = input("$ ")
    # full_command = user_input.split(" ")
    if "|" in user_input:
        handle_pipeline(user_input)
        return True

    full_command = shlex.split(user_input)
    select_commands(full_command)
    return True


def echo(input_command, redirect_file=None, redirect_mode=None):
    text = " ".join(input_command)
    if redirect_file:
        try:
            parent_dir = os.path.dirname(redirect_file)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            mode = "a" if redirect_mode in ["append", "stderr_append"] else "w"

            if redirect_mode in ["stderr", "stderr_append"]:
                with open(redirect_file, mode) as file:
                    pass
                print(text)
            else:
                with open(redirect_file, mode) as file:
                    file.write(text + "\n")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(" ".join(input_command))


def exit():
    histfile = os.environ.get("HISTFILE")
    if histfile:
        readline.write_history_file(histfile)
    sys.exit()


def cmd_type(joined_command, input_command):
    command_list = ["echo", "exit", "type", "pwd", "cd", "history"]
    if joined_command in command_list:
        print(f"{joined_command} is a shell builtin")
    else:
        cmd_to_check = input_command[0]
        found = False
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            full_path = os.path.join(directory, cmd_to_check)

            if os.path.isfile(full_path):
                if os.access(full_path, os.X_OK):
                    print(f"{cmd_to_check} is {full_path}")
                    found = True
                    break
        if not found:
            print(f"{joined_command}: not found")


def pwd(redirect_file=None):
    try:
        cwd = os.getcwd()
        if redirect_file:
            with open(redirect_file, "w") as f:
                f.write(cwd + "\n")
        else:
            print(cwd)
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            return False
    return True


def cd(joined_command):
    try:
        # If rest is empty, default to home directory
        if joined_command != "~":
            target = joined_command
        else:
            target = os.path.expanduser("~")
        os.chdir(target)

    except FileNotFoundError:
        print(f"cd: {target}: No such file or directory")
    except NotADirectoryError:
        print(f"cd: {target}: Not a directory")
    except PermissionError:
        print(f"cd: {target}: Permission denied")


def redirect(commands):
    redirect_file = None
    redirect_mode = None
    redirect_idx = -1
    # Check for redirection operators
    if "2>>" in commands:
        redirect_idx = commands.index("2>>")
        redirect_mode = "stderr_append"
    elif "1>>" in commands:
        redirect_idx = commands.index("1>>")
        redirect_mode = "append"
    elif ">>" in commands:
        redirect_idx = commands.index(">>")
        redirect_mode = "append"
    elif "2>" in commands:
        redirect_idx = commands.index("2>")
        redirect_mode = "stderr"
    elif "1>" in commands:
        redirect_idx = commands.index("1>")
        redirect_mode = "stdout"
    elif ">" in commands:
        redirect_idx = commands.index(">")
        redirect_mode = "stdout"

    if redirect_idx != -1 and redirect_idx + 1 < len(commands):
        redirect_file = commands[redirect_idx + 1]
        commands = commands[:redirect_idx]

    return commands, redirect_file, redirect_mode


def other(commands, redirect_file, redirect_mode):
    cmd_name = commands[0]
    args = commands

    found = False
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        full_path = os.path.join(directory, cmd_name)

        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            # Execute the program and wait
            if redirect_file:
                try:
                    # Create parent directory if needed
                    parent_dir = os.path.dirname(redirect_file)
                    if parent_dir and not os.path.exists(parent_dir):
                        os.makedirs(parent_dir, exist_ok=True)

                    mode = "a" if redirect_mode in [
                        "append", "stderr_append"] else "w"

                    # Redirect stdout to file
                    with open(redirect_file, mode) as f:
                        if redirect_mode in ["stderr", "stderr_append"]:
                            subprocess.run(
                                args, executable=full_path, stderr=f)
                        else:
                            subprocess.run(
                                args, executable=full_path, stdout=f)
                except Exception as e:
                    print(f"Error: {e}")
            else:
                # No redirection, run normally
                subprocess.run(args, executable=full_path)
            found = True
            break

    if not found:
        print(f"{cmd_name}: command not found")


def completer(text, state):
    matches = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    file_matches = get_path_executables(text)

    seen = set()
    all_matches = []
    for m in matches + file_matches:
        if m not in seen:
            seen.add(m)
            all_matches.append(m)

    if state < len(all_matches):
        if len(all_matches) == 1:
            return all_matches[state] + ' '
        return all_matches[state]
    return None


def get_path_executables(text):
    """Find all executables in PATH that start with text."""
    executables = []
    path_dirs = os.environ.get('PATH', '').split(':')
    for directory in path_dirs:
        # PATH can include dirs that don't exist — handle gracefully
        if not os.path.isdir(directory):
            continue
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if filename.startswith(text) and os.access(filepath, os.X_OK):
                executables.append(filename)
    return executables


def display_matches(substitution, matches, longest_match_length):
    # Strip any trailing spaces from matches before joining
    cleaned = [m.strip() for m in sorted(matches)]
    print()
    print('  '.join(cleaned))  # Exactly two spaces between matches
    print("$ " + readline.get_line_buffer(), end='', flush=True)


def select_commands(commands):

    commands, redirect_file, redirect_mode = redirect(commands)

    if not commands:
        return True

    command, *rest = commands
    joined_command = " ".join(rest)
    if command:
        match command:
            case "echo":
                echo(rest, redirect_file, redirect_mode)
            case "exit":
                exit()
            case "type":
                cmd_type(joined_command, rest)
            case "pwd":
                pwd(redirect_file)
            case "cd":
                cd(joined_command)
            case "history":
                history(rest)
            case _:
                other(commands, redirect_file, redirect_mode)


def handle_pipeline(user_input):
    """Handle a pipeline of two (or more) commands connected by |."""
    # Split on the pipe operator, preserving quoting within each segment
    segments = user_input.split('|')
    commands = []
    for seg in segments:
        seg = seg.strip()
        if seg:
            commands.append(shlex.split(seg))

    if len(commands) < 2:
        # Not really a pipeline, just run the single command
        select_commands(commands[0])
        return

    num_cmds = len(commands)
    pipes = []

    # Create (num_cmds - 1) pipes
    for _ in range(num_cmds - 1):
        r, w = os.pipe()
        pipes.append((r, w))

    pids = []

    for i, cmd in enumerate(commands):
        pid = os.fork()
        if pid == 0:
            # Child process

            # If not the first command, read from the previous pipe
            if i > 0:
                os.dup2(pipes[i - 1][0], 0)  # stdin = read end of prev pipe

            # If not the last command, write to the next pipe
            if i < num_cmds - 1:
                os.dup2(pipes[i][1], 1)  # stdout = write end of current pipe

            # Close all pipe fds in the child
            for r, w in pipes:
                os.close(r)
                os.close(w)

            # Try to execute the command
            cmd_name = cmd[0]

            # Check if it's a builtin that writes to stdout
            if cmd_name == "echo":
                print(" ".join(cmd[1:]))
                sys.stdout.flush()
                os._exit(0)
            elif cmd_name == "pwd":
                print(os.getcwd())
                sys.stdout.flush()
                os._exit(0)
            elif cmd_name == "cd":
                # cd in a child doesn't affect parent, but handle gracefully
                os._exit(0)
            elif cmd_name == "exit":
                os._exit(0)
            elif cmd_name == "type":
                # Run type in the child
                joined = " ".join(cmd[1:])
                cmd_type(joined, cmd[1:])
                sys.stdout.flush()
                os._exit(0)
            else:
                # External command — use execvp to replace the child process
                for directory in os.environ.get("PATH", "").split(os.pathsep):
                    full_path = os.path.join(directory, cmd_name)
                    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                        os.execv(full_path, cmd)
                # If not found
                sys.stderr.write(f"{cmd_name}: command not found\n")
                sys.stderr.flush()
                os._exit(127)
        else:
            pids.append(pid)

    # Parent: close all pipe fds
    for r, w in pipes:
        os.close(r)
        os.close(w)

    # Wait for all children
    for pid in pids:
        os.waitpid(pid, 0)


def history(commands):
    global last_history_written

    if commands and commands[0] == '-r':
        if len(commands) > 1:
            history_file = commands[1]
            readline.read_history_file(history_file)
            last_history_written = readline.get_current_history_length()
        return None

    elif commands and commands[0] == '-w':
        if len(commands) > 1:
            history_file = commands[1]
            readline.write_history_file(history_file)
            last_history_written = readline.get_current_history_length()
        return None

    elif commands and commands[0] == '-a':
        if len(commands) > 1:
            history_file = commands[1]
            total = readline.get_current_history_length()
            new_entries = total - last_history_written
            if new_entries > 0:
                readline.append_history_file(new_entries, history_file)
            last_history_written = total
        return None

    else:
        limit = commands[0] if commands else ''
        total = readline.get_current_history_length()
        if not limit or limit.strip() == '':
            start = 1
        else:
            n = int(limit)
            if n >= total:
                start = 1
            else:
                start = total - n + 1
        print('\n'.join([f"{i:>5}  {readline.get_history_item(i)}"
                         for i in range(start, total + 1)]))
    return None


if __name__ == "__main__":
    histfile = os.environ.get("HISTFILE")
    histfile = os.environ.get("HISTFILE")
    if histfile and os.path.exists(histfile):
        try:
            readline.read_history_file(histfile)
        except OSError:
            # If readline can't parse the file, load it manually
            with open(histfile, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        readline.add_history(line)
        last_history_written = readline.get_current_history_length()

    response = True
    while response:
        response = main()
