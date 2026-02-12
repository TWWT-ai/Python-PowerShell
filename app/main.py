import sys
import os
import subprocess
import shutil
import shlex

PATH = os.getenv("PATH", "")
paths = PATH.split(":")


def main():
    # Uncomment this block to pass the first stage
    sys.stdout.write("$ ")
  # Wait for user input
    user_input = input("")
    # full_command = user_input.split(" ")
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
    sys.exit()


def cmd_type(joined_command, input_command):
    command_list = ["echo", "exit", "type", "pwd", "cd"]
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
            case _:
                other(commands, redirect_file, redirect_mode)


if __name__ == "__main__":
    response = True
    while response:
        response = main()
