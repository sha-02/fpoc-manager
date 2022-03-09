import shlex        # Lexical analysis of shell-style syntaxes
import subprocess


# Based on: https://www.endpointdev.com/blog/2015/01/getting-realtime-output-using-python/
def syscall_realtime(command, *, split=True) -> tuple:
    if split:   # split the 'command' string into a list
        command = shlex.split(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = ''
    while True:
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        else:
            output = output.decode('utf-8')
            print(output)
            result += output

    return process.poll(), result
