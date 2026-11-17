---
type: reference
tags: [tools]
---
# Linux Commands

## Finding things

- `grep -rn "text" .` searches file contents recursively and shows line numbers.
- `find . -name "*.log" -mtime +7` lists log files older than a week.

## Permissions

- `chmod +x script.sh` makes a script executable.
- `chown user:group file` changes the owner.

## Processes

- `ps aux | grep name` finds a running process.
- `kill -9 <pid>` forces it to stop. Try plain `kill` first.

## Disk

- `df -h` shows free space per disk.
- `du -sh *` shows the size of each item in the current folder.
