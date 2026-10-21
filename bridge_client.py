"""Local file transport for GPT_Max_Bridge.ms (Python 3.9+, standard library)."""
import argparse
import os
from pathlib import Path
import tempfile
import time
import uuid


def max_string(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def submit(root, source):
    root = Path(root).resolve()
    if not (root / 'GPT_Max_Bridge.ms').is_file():
        raise ValueError('Bridge directory must contain GPT_Max_Bridge.ms')
    source = Path(source).resolve()
    if not source.is_file():
        raise ValueError('MAXScript source file does not exist')
    token = uuid.uuid4().hex
    runtime = root / 'runtime'
    runtime.mkdir(exist_ok=True)
    # Copy the source so edits after submission cannot change this command.
    payload = runtime / (token + '.ms')
    payload.write_bytes(source.read_bytes())
    result = runtime / (token + '.txt')
    wrapper = '''(
local resultPath = %s
try
(
    fileIn %s quiet:true
    local f = createFile resultPath
    format "OK\\n" to:f
    close f
)
catch
(
    local problem = getCurrentException()
    local f = createFile resultPath
    format "ERROR\\n%%\\n" problem to:f
    close f
    throw problem
)
)
''' % (max_string(result), max_string(payload))
    fd, temporary = tempfile.mkstemp(prefix='.request-', suffix='.tmp', dir=root)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8-sig', newline='\r\n') as stream:
            stream.write(wrapper)
        # Publish a complete file atomically. Never replace an existing request.
        if os.name == 'nt':
            # Windows rename fails if the destination exists.
            os.rename(temporary, root / 'bridge_request.ms')
        else:
            os.link(temporary, root / 'bridge_request.ms')
    except BaseException:
        payload.unlink(missing_ok=True)
        raise
    finally:
        Path(temporary).unlink(missing_ok=True)
    return result


def wait_result(result, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if result.exists():
            try:
                value = result.read_text(encoding='utf-8-sig', errors='replace')
            except PermissionError:
                time.sleep(0.2)
                continue
            # A newly created receipt can still be empty until Max closes it.
            if value.startswith('OK\n') or value.startswith('ERROR\n'):
                return value.strip()
        time.sleep(0.2)
    raise TimeoutError('No receipt yet. The command may still run; do not resend blindly. Receipt: ' + str(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('script', type=Path)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    try:
        receipt = submit(args.root, args.script)
        print('Submitted. Receipt: ' + str(receipt), flush=True)
        outcome = wait_result(receipt, args.timeout)
        print(outcome)
        return 0 if outcome == 'OK' else 1
    except (OSError, ValueError, TimeoutError) as error:
        print(str(error))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
