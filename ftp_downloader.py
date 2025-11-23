#!/usr/bin/env python3
import os
import sys
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from dotenv import load_dotenv

import paramiko
from stat import S_ISDIR

def read_config():
    load_dotenv()

    cfg = {
        'host': os.getenv('SFTP_HOST'),
        'port': int(os.getenv('SFTP_PORT', '22')),
        'user': os.getenv('SFTP_USER'),
        'passwd': os.getenv('SFTP_PASS', None),
        'key_path': os.getenv('SFTP_KEY_PATH', None),
        'key_passphrase': os.getenv('SFTP_KEY_PASSPHRASE', None),
        'dir': os.getenv('SFTP_DIR', '').strip(),
        'output_dir': os.getenv('OUTPUT_DIR', '.'),
        'zip_prefix': os.getenv('ZIP_PREFIX', '').strip(),
        'timeout': int(os.getenv('SFTP_TIMEOUT', '30')),
        'keep_backups': int(os.getenv('KEEP_BACKUPS', '3')),
    }

    if not cfg['host']:
        raise ValueError('SFTP_HOST must be set in .env')
    if not cfg['user']:
        raise ValueError('SFTP_USER must be set in .env')
    if not cfg['dir']:
        raise ValueError('SFTP_DIR must be set in .env')

    return cfg

def connect_sftp(cfg):
    print('Connecting to SFTP server...', cfg['host'])
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = {
        'hostname': cfg['host'],
        'port': cfg['port'],
        'username': cfg['user'],
        'timeout': cfg['timeout'],
    }

    if cfg['passwd']:
        connect_kwargs['password'] = cfg['passwd']

    if cfg['key_path']:
        connect_kwargs['key_filename'] = cfg['key_path']
        if cfg['key_passphrase']:
            connect_kwargs['passphrase'] = cfg['key_passphrase']

    try:
        ssh.connect(**connect_kwargs)
    except Exception as e:
        raise RuntimeError(f'Failed to connect/authenticate to SFTP: {e}')

    sftp = ssh.open_sftp()
    print('SFTP connected.')
    return ssh, sftp

def download_sftp_file(sftp, remote_path, local_path):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    print('  Downloading file:', remote_path)
    sftp.get(remote_path, local_path)

def download_sftp_dir(sftp, remote_dir, local_dir):
    os.makedirs(local_dir, exist_ok=True)

    try:
        entries = sftp.listdir_attr(remote_dir)
    except IOError as e:
        raise RuntimeError(f'Failed to list remote directory {remote_dir}: {e}')

    for entry in entries:
        name = entry.filename
        if name in ('.', '..'):
            continue
        remote_path = remote_dir.rstrip('/') + '/' + name
        local_path = os.path.join(local_dir, name)

        if S_ISDIR(entry.st_mode):
            download_sftp_dir(sftp, remote_path, local_path)
        else:
            download_sftp_file(sftp, remote_path, local_path)

def create_zip_from_folder(src_folder, output_dir, zip_prefix=''):
    timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H-%M-%S.%fZ')
    prefix = (zip_prefix + '_') if zip_prefix else ''
    zip_name = f"{prefix}{timestamp}.zip"
    os.makedirs(output_dir, exist_ok=True)
    zip_path = os.path.join(output_dir, zip_name)

    print('Creating zip archive:', zip_path)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src_folder):
            for file in files:
                fullpath = os.path.join(root, file)
                arcname = os.path.relpath(fullpath, start=src_folder)
                zf.write(fullpath, arcname)

    print('Archive created successfully.')
    return zip_path

def cleanup_old_backups(output_dir, prefix='', keep=3):
    """
    Keep only the newest `keep` zip files in output_dir that start with prefix.
    Newness is determined first by ISO timestamp parsed from filename (if present),
    otherwise by file modification time.
    """
    if keep <= 0:
        return

    try:
        files = [f for f in os.listdir(output_dir) if f.lower().endswith('.zip') and (f.startswith(prefix) if prefix else True)]
    except FileNotFoundError:
        return

    def file_key(fname):
        # try to parse timestamp after prefix and before .zip
        name = fname
        if prefix and fname.startswith(prefix + '_'):
            name = fname[len(prefix) + 1:]
        elif prefix and fname.startswith(prefix):
            name = fname[len(prefix):]
        name = name.rsplit('.zip', 1)[0]
        # Expecting ISO-like '%Y-%m-%dT%H-%M-%S.%fZ' per create_zip_from_folder
        try:
            dt = datetime.strptime(name, '%Y-%m-%dT%H-%M-%S.%fZ')
            return dt.timestamp()
        except Exception:
            # fallback to mtime
            path = os.path.join(output_dir, fname)
            try:
                return os.path.getmtime(path)
            except Exception:
                return 0

    files.sort(key=file_key, r#!/usr/bin/env python3
import os
import sys
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from dotenv import load_dotenv

import paramiko
from stat import S_ISDIR

def read_config():
    load_dotenv()

    cfg = {
        'host': os.getenv('SFTP_HOST'),
        'port': int(os.getenv('SFTP_PORT', '22')),
        'user': os.getenv('SFTP_USER'),
        'passwd': os.getenv('SFTP_PASS', None),
        'key_path': os.getenv('SFTP_KEY_PATH', None),
        'key_passphrase': os.getenv('SFTP_KEY_PASSPHRASE', None),
        'dir': os.getenv('SFTP_DIR', '').strip(),
        'output_dir': os.getenv('OUTPUT_DIR', '.'),
        'zip_prefix': os.getenv('ZIP_PREFIX', '').strip(),
        'timeout': int(os.getenv('SFTP_TIMEOUT', '30')),
        'keep_backups': int(os.getenv('KEEP_BACKUPS', '3')),
    }

    if not cfg['host']:
        raise ValueError('SFTP_HOST must be set in .env')
    if not cfg['user']:
        raise ValueError('SFTP_USER must be set in .env')
    if not cfg['dir']:
        raise ValueError('SFTP_DIR must be set in .env')

    return cfg

def connect_sftp(cfg):
    print('Connecting to SFTP server...', cfg['host'])
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = {
        'hostname': cfg['host'],
        'port': cfg['port'],
        'username': cfg['user'],
        'timeout': cfg['timeout'],
    }

    if cfg['passwd']:
        connect_kwargs['password'] = cfg['passwd']

    if cfg['key_path']:
        connect_kwargs['key_filename'] = cfg['key_path']
        if cfg['key_passphrase']:
            connect_kwargs['passphrase'] = cfg['key_passphrase']

    try:
        ssh.connect(**connect_kwargs)
    except Exception as e:
        raise RuntimeError(f'Failed to connect/authenticate to SFTP: {e}')

    sftp = ssh.open_sftp()
    print('SFTP connected.')
    return ssh, sftp

def download_sftp_file(sftp, remote_path, local_path):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    print('  Downloading file:', remote_path)
    sftp.get(remote_path, local_path)

def download_sftp_dir(sftp, remote_dir, local_dir):
    os.makedirs(local_dir, exist_ok=True)

    try:
        entries = sftp.listdir_attr(remote_dir)
    except IOError as e:
        raise RuntimeError(f'Failed to list remote directory {remote_dir}: {e}')

    for entry in entries:
        name = entry.filename
        if name in ('.', '..'):
            continue
        remote_path = remote_dir.rstrip('/') + '/' + name
        local_path = os.path.join(local_dir, name)

        if S_ISDIR(entry.st_mode):
            download_sftp_dir(sftp, remote_path, local_path)
        else:
            download_sftp_file(sftp, remote_path, local_path)

def create_zip_from_folder(src_folder, output_dir, zip_prefix=''):
    timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H-%M-%S.%fZ')
    prefix = (zip_prefix + '_') if zip_prefix else ''
    zip_name = f"{prefix}{timestamp}.zip"
    os.makedirs(output_dir, exist_ok=True)
    zip_path = os.path.join(output_dir, zip_name)

    print('Creating zip archive:', zip_path)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src_folder):
            for file in files:
                fullpath = os.path.join(root, file)
                arcname = os.path.relpath(fullpath, start=src_folder)
                zf.write(fullpath, arcname)

    print('Archive created successfully.')
    return zip_path

def cleanup_old_backups(output_dir, prefix='', keep=3):
    """
    Keep only the newest `keep` zip files in output_dir that start with prefix.
    Newness is determined first by ISO timestamp parsed from filename (if present),
    otherwise by file modification time.
    """
    if keep <= 0:
        return

    try:
        files = [f for f in os.listdir(output_dir) if f.lower().endswith('.zip') and (f.startswith(prefix) if prefix else True)]
    except FileNotFoundError:
        return

    def file_key(fname):
        # try to parse timestamp after prefix and before .zip
        name = fname
        if prefix and fname.startswith(prefix + '_'):
            name = fname[len(prefix) + 1:]
        elif prefix and fname.startswith(prefix):
            name = fname[len(prefix):]
        name = name.rsplit('.zip', 1)[0]
        # Expecting ISO-like '%Y-%m-%dT%H-%M-%S.%fZ' per create_zip_from_folder
        try:
            dt = datetime.strptime(name, '%Y-%m-%dT%H-%M-%S.%fZ')
            return dt.timestamp()
        except Exception:
            # fallback to mtime
            path = os.path.join(output_dir, fname)
            try:
                return os.path.getmtime(path)
            except Exception:
                return 0

    files.sort(key=file_key, reverse=True)  # newest first
    to_delete = files[keep:]
    for fname in to_delete:
        path = os.path.join(output_dir, fname)
        try:
            print('Removing old backup:', path)
            os.remove(path)
        except Exception as e:
            print(f'Failed to remove {path}: {e}')

def main():
    try:
        cfg = read_config()
    except Exception as e:
        print('Configuration error:', e)
        sys.exit(2)#!/usr/bin/env python3
import os
import sys
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from dotenv import load_dotenv

import paramiko
from stat import S_ISDIR

def read_config():
    load_dotenv()

    cfg = {
        'host': os.getenv('SFTP_HOST'),
        'port': int(os.getenv('SFTP_PORT', '22')),
        'user': os.getenv('SFTP_USER'),
        'passwd': os.getenv('SFTP_PASS', None),
        'key_path': os.getenv('SFTP_KEY_PATH', None),
        'key_passphrase': os.getenv('SFTP_KEY_PASSPHRASE', None),
        'dir': os.getenv('SFTP_DIR', '').strip(),
        'output_dir': os.getenv('OUTPUT_DIR', '.'),
        'zip_prefix': os.getenv('ZIP_PREFIX', '').strip(),
        'timeout': int(os.getenv('SFTP_TIMEOUT', '30')),
        'keep_backups': int(os.getenv('KEEP_BACKUPS', '3')),
    }

    if not cfg['host']:
        raise ValueError('SFTP_HOST must be set in .env')
    if not cfg['user']:
        raise ValueError('SFTP_USER must be set in .env')
    if not cfg['dir']:
        raise ValueError('SFTP_DIR must be set in .env')

    return cfg

def connect_sftp(cfg):
    print('Connecting to SFTP server...', cfg['host'])
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = {
        'hostname': cfg['host'],
        'port': cfg['port'],
        'username': cfg['user'],
        'timeout': cfg['timeout'],
    }

    if cfg['passwd']:
        connect_kwargs['password'] = cfg['passwd']

    if cfg['key_path']:
        connect_kwargs['key_filename'] = cfg['key_path']
        if cfg['key_passphrase']:
            connect_kwargs['passphrase'] = cfg['key_passphrase']

    try:
        ssh.connect(**connect_kwargs)
    except Exception as e:
        raise RuntimeError(f'Failed to connect/authenticate to SFTP: {e}')

    sftp = ssh.open_sftp()
    print('SFTP connected.')
    return ssh, sftp

def download_sftp_file(sftp, remote_path, local_path):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    print('  Downloading file:', remote_path)
    sftp.get(remote_path, local_path)

def download_sftp_dir(sftp, remote_dir, local_dir):
    os.makedirs(local_dir, exist_ok=True)

    try:
        entries = sftp.listdir_attr(remote_dir)
    except IOError as e:
        raise RuntimeError(f'Failed to list remote directory {remote_dir}: {e}')

    for entry in entries:
        name = entry.filename
        if name in ('.', '..'):
            continue
        remote_path = remote_dir.rstrip('/') + '/' + name
        local_path = os.path.join(local_dir, name)

        if S_ISDIR(entry.st_mode):
            download_sftp_dir(sftp, remote_path, local_path)
        else:
            download_sftp_file(sftp, remote_path, local_path)

def create_zip_from_folder(src_folder, output_dir, zip_prefix=''):
    timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H-%M-%S.%fZ')
    prefix = (zip_prefix + '_') if zip_prefix else ''
    zip_name = f"{prefix}{timestamp}.zip"
    os.makedirs(output_dir, exist_ok=True)
    zip_path = os.path.join(output_dir, zip_name)

    print('Creating zip archive:', zip_path)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src_folder):
            for file in files:
                fullpath = os.path.join(root, file)
                arcname = os.path.relpath(fullpath, start=src_folder)
                zf.write(fullpath, arcname)

    print('Archive created successfully.')
    return zip_path

def cleanup_old_backups(output_dir, prefix='', keep=3):
    """
    Keep only the newest `keep` zip files in output_dir that start with prefix.
    Newness is determined first by ISO timestamp parsed from filename (if present),
    otherwise by file modification time.
    """
    if keep <= 0:
        return

    try:
        files = [f for f in os.listdir(output_dir) if f.lower().endswith('.zip') and (f.startswith(prefix) if prefix else True)]
    except FileNotFoundError:
        return

    def file_key(fname):
        # try to parse timestamp after prefix and before .zip
        name = fname
        if prefix and fname.startswith(prefix + '_'):
            name = fname[len(prefix) + 1:]
        elif prefix and fname.startswith(prefix):
            name = fname[len(prefix):]
        name = name.rsplit('.zip', 1)[0]
        # Expecting ISO-like '%Y-%m-%dT%H-%M-%S.%fZ' per create_zip_from_folder
        try:
            dt = datetime.strptime(name, '%Y-%m-%dT%H-%M-%S.%fZ')
            return dt.timestamp()
        except Exception:
            # fallback to mtime
            path = os.path.join(output_dir, fname)
            try:
                return os.path.getmtime(path)
            except Exception:
                return 0

    files.sort(key=file_key, reverse=True)  # newest first
    to_delete = files[keep:]
    for fname in to_delete:
        path = os.path.join(output_dir, fname)
        try:
            print('Removing old backup:', path)
            os.remove(path)
        except Exception as e:
            print(f'Failed to remove {path}: {e}')

def main():
    try:
        cfg = read_config()
    except Exception as e:
        print('Configuration error:', e)
        sys.exit(2)

    ssh = None
    sftp = None
    tmpdir = None
    try:
        ssh, sftp = connect_sftp(cfg)

        tmpdir = tempfile.mkdtemp(prefix='sftp_download_')
        print('Temporary download directory:', tmpdir)

        remote_dir = cfg['dir']
        basename = os.path.basename(remote_dir.rstrip('/')) or remote_dir.strip('/').replace('/', '_')
        local_target = os.path.join(tmpdir, basename)
        print(f'Downloading remote directory: {remote_dir} -> {local_target}')
        try:
            download_sftp_dir(sftp, remote_dir, local_target)
        except Exception as e:
            print(f'Failed to download {remote_dir}: {e}')
            raise

        zip_path = create_zip_from_folder(tmpdir, cfg['output_dir'], cfg['zip_prefix'])
        print('Saved archive to:', zip_path)

        # cleanup old backups, keep newest cfg['keep_backups']
        cleanup_old_backups(cfg['output_dir'], prefix=cfg['zip_prefix'], keep=cfg['keep_backups'])

    except Exception as e:
        print('Error:', e)
        sys.exit(1)

    finally:
        if sftp:
            try:
                sftp.close()
            except Exception:
                pass
        if ssh:
            try:
                ssh.close()
            except Exception:
                pass
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)

if __name__ == '__main__':
    main()

    ssh = None
    sftp = None
    tmpdir = None
    try:
        ssh, sftp = connect_sftp(cfg)

        tmpdir = tempfile.mkdtemp(prefix='sftp_download_')
        print('Temporary download directory:', tmpdir)

        remote_dir = cfg['dir']
        basename = os.path.basename(remote_dir.rstrip('/')) or remote_dir.strip('/').replace('/', '_')
        local_target = os.path.join(tmpdir, basename)
        print(f'Downloading remote directory: {remote_dir} -> {local_target}')
        try:
            download_sftp_dir(sftp, remote_dir, local_target)
        except Exception as e:
            print(f'Failed to download {remote_dir}: {e}')
            raise

        zip_path = create_zip_from_folder(tmpdir, cfg['output_dir'], cfg['zip_prefix'])
        print('Saved archive to:', zip_path)

        # cleanup old backups, keep newest cfg['keep_backups']
        cleanup_old_backups(cfg['output_dir'], prefix=cfg['zip_prefix'], keep=cfg['keep_backups'])

    except Exception as e:
        print('Error:', e)
        sys.exit(1)

    finally:
        if sftp:
            try:
                sftp.close()
            except Exception:
                pass
        if ssh:
            try:
                ssh.close()
            except Exception:
                pass
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)

if __name__ == '__main__':
    main()everse=True)  # newest first
    to_delete = files[keep:]
    for fname in to_delete:
        path = os.path.join(output_dir, fname)
        try:
            print('Removing old backup:', path)
            os.remove(path)
        except Exception as e:
            print(f'Failed to remove {path}: {e}')

def main():
    try:
        cfg = read_config()
    except Exception as e:
        print('Configuration error:', e)
        sys.exit(2)

    ssh = None
    sftp = None
    tmpdir = None
    try:
        ssh, sftp = connect_sftp(cfg)

        tmpdir = tempfile.mkdtemp(prefix='sftp_download_')
        print('Temporary download directory:', tmpdir)

        remote_dir = cfg['dir']
        basename = os.path.basename(remote_dir.rstrip('/')) or remote_dir.strip('/').replace('/', '_')
        local_target = os.path.join(tmpdir, basename)
        print(f'Downloading remote directory: {remote_dir} -> {local_target}')
        try:
            download_sftp_dir(sftp, remote_dir, local_target)
        except Exception as e:
            print(f'Failed to download {remote_dir}: {e}')
            raise

        zip_path = create_zip_from_folder(tmpdir, cfg['output_dir'], cfg['zip_prefix'])
        print('Saved archive to:', zip_path)

        # cleanup old backups, keep newest cfg['keep_backups']
        cleanup_old_backups(cfg['output_dir'], prefix=cfg['zip_prefix'], keep=cfg['keep_backups'])

    except Exception as e:
        print('Error:', e)
        sys.exit(1)

    finally:
        if sftp:
            try:
                sftp.close()
            except Exception:
                pass
        if ssh:
            try:
                ssh.close()
            except Exception:
                pass
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)

if __name__ == '__main__':
    main()
