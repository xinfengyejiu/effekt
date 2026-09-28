# encoding: UTF-8
"""
Stdlib HTTP/HTTPS CONNECT proxy with latency / bandwidth / loss shaping.
No TLS interception — HTTPS is tunneled after optional delay.
"""
from __future__ import print_function

import argparse
import json
import os
import random
import select
import socket
import sys
import threading
import time

BACKLOG = 128
BUF = 8192


def _load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {
        'latency_ms': int(data.get('latency_ms') or 0),
        'bandwidth_kbps': int(data.get('bandwidth_kbps') or 0),
        'loss_percent': float(data.get('loss_percent') or 0),
        'disconnect_rules': data.get('disconnect_rules') or {},
    }


def _in_disconnect_window(rules):
    if not rules:
        return False
    cycle = int(rules.get('cycle_sec') or 0)
    down = int(rules.get('down_sec') or 0)
    if cycle <= 0 or down <= 0:
        return False
    return (int(time.time()) % cycle) < down


def _throttle_sleep(nbytes, bandwidth_kbps):
    if bandwidth_kbps <= 0 or nbytes <= 0:
        return
    # kbps → bytes/sec
    rate = bandwidth_kbps * 1024 / 8.0
    if rate <= 0:
        return
    time.sleep(nbytes / rate)


def _pipe(src, dst, bandwidth_kbps):
    try:
        while True:
            r, _, _ = select.select([src], [], [], 60)
            if not r:
                break
            data = src.recv(BUF)
            if not data:
                break
            _throttle_sleep(len(data), bandwidth_kbps)
            dst.sendall(data)
    except Exception:
        pass
    finally:
        try:
            src.shutdown(socket.SHUT_RD)
        except Exception:
            pass
        try:
            dst.shutdown(socket.SHUT_WR)
        except Exception:
            pass


class WeaknetProxy(object):
    def __init__(self, host, port, cfg):
        self.host = host
        self.port = port
        self.cfg = cfg
        self._sock = None

    def serve_forever(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(BACKLOG)
        print('weaknet_proxy listening on {}:{} latency={}ms bw={}kbps loss={}%'.format(
            self.host, self.port,
            self.cfg['latency_ms'], self.cfg['bandwidth_kbps'], self.cfg['loss_percent'],
        ), flush=True)
        while True:
            client, addr = self._sock.accept()
            t = threading.Thread(target=self._handle, args=(client, addr))
            t.daemon = True
            t.start()

    def _handle(self, client, addr):
        try:
            if _in_disconnect_window(self.cfg['disconnect_rules']):
                client.close()
                return
            if self.cfg['loss_percent'] > 0 and random.random() * 100 < self.cfg['loss_percent']:
                client.close()
                return
            if self.cfg['latency_ms'] > 0:
                time.sleep(self.cfg['latency_ms'] / 1000.0)
            client.settimeout(30)
            req = b''
            while b'\r\n\r\n' not in req and len(req) < 65536:
                chunk = client.recv(BUF)
                if not chunk:
                    client.close()
                    return
                req += chunk
            header = req.split(b'\r\n\r\n', 1)[0].decode('latin1', errors='ignore')
            lines = header.split('\r\n')
            if not lines:
                client.close()
                return
            parts = lines[0].split()
            if len(parts) < 2:
                client.close()
                return
            method, target = parts[0].upper(), parts[1]
            bw = self.cfg['bandwidth_kbps']
            if method == 'CONNECT':
                host_port = target.split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 443
                remote = socket.create_connection((host, port), timeout=20)
                client.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                t1 = threading.Thread(target=_pipe, args=(client, remote, bw))
                t2 = threading.Thread(target=_pipe, args=(remote, client, bw))
                t1.daemon = True
                t2.daemon = True
                t1.start()
                t2.start()
                t1.join()
                t2.join()
                remote.close()
                client.close()
                return
            # plain HTTP forward
            if target.startswith('http://'):
                from urllib.parse import urlparse
                parsed = urlparse(target)
                host = parsed.hostname
                port = parsed.port or 80
                path = parsed.path or '/'
                if parsed.query:
                    path += '?' + parsed.query
            else:
                host_header = ''
                for line in lines[1:]:
                    if line.lower().startswith('host:'):
                        host_header = line.split(':', 1)[1].strip()
                        break
                if not host_header:
                    client.close()
                    return
                if ':' in host_header:
                    host, port_s = host_header.rsplit(':', 1)
                    port = int(port_s)
                else:
                    host, port = host_header, 80
                path = target
            remote = socket.create_connection((host, port), timeout=20)
            first = '{} {} HTTP/1.1\r\n'.format(method, path)
            rest = '\r\n'.join(lines[1:]) + '\r\n\r\n'
            body = req.split(b'\r\n\r\n', 1)[1] if b'\r\n\r\n' in req else b''
            remote.sendall((first + rest).encode('latin1') + body)
            t1 = threading.Thread(target=_pipe, args=(remote, client, bw))
            t2 = threading.Thread(target=_pipe, args=(client, remote, bw))
            t1.daemon = True
            t2.daemon = True
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            remote.close()
            client.close()
        except Exception as exc:
            try:
                client.close()
            except Exception:
                pass
            sys.stderr.write('weaknet_proxy client error: {}\n'.format(exc))


def main():
    parser = argparse.ArgumentParser(description='Weak-network CONNECT proxy')
    parser.add_argument('--config', required=True, help='profile.json path')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=18888)
    parser.add_argument('--pidfile', default='')
    args = parser.parse_args()
    cfg = _load_config(args.config)
    if args.pidfile:
        with open(args.pidfile, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
    WeaknetProxy(args.host, args.port, cfg).serve_forever()


if __name__ == '__main__':
    main()
