import os
import sys
import signal
import asyncio
import logging
import traceback
from alita.serve.config import *
from alita.serve.server import *
from gunicorn.workers.base import Worker


try:
    import ssl
except ImportError:
    ssl = None


class GunicornWorker(Worker):
    http_protocol = HttpProtocol

    def __init__(self, *args, **kw):  # pragma: no cover
        super().__init__(*args, **kw)
        cfg = self.cfg
        if cfg.is_ssl:
            self.ssl_context = self._create_ssl_context(cfg)
        else:
            self.ssl_context = None
        self.servers = {}
        self.connections = set()
        self.exit_code = 0
        self.loop = None
        self._runner = None
        self._server_config = None

    def init_process(self):
        self.loop = init_loop()
        asyncio.set_event_loop(self.loop)
        super().init_process()

    def run(self):
        is_debug = self.log.loglevel == logging.DEBUG
        self._server_config = dict(
            loop=self.loop,
            debug=is_debug,
            ssl=self.ssl_context,
            http_protocol=self.http_protocol
        )
        self._runner = asyncio.ensure_future(self._run(), loop=self.loop)
        try:
            self.loop.run_until_complete(self._runner)
            self.app.callable.is_running = True
            self.loop.run_until_complete(self._check_alive())
            self.loop.run_until_complete(self.close())
        except BaseException:
            traceback.print_exc()
        finally:
            self.loop.close()
        sys.exit(self.exit_code)

    async def close(self):
        if self.servers:
            self.log.info(
                "Stopping server: %s, connections: %s",
                self.pid,
                len(self.connections),
            )
            for server in self.servers:
                server.close()
                await server.wait_closed()
            self.servers.clear()

            # prepare connections for closing
            for conn in self.connections:
                conn.close_if_idle()

            # gracefully shutdown timeout
            start_shutdown = 0
            graceful_shutdown_timeout = self.cfg.graceful_timeout
            while self.connections and (
                start_shutdown < graceful_shutdown_timeout
            ):
                await asyncio.sleep(0.1)
                start_shutdown = start_shutdown + 0.1

            # Force close non-idle connection after waiting for
            # graceful_shutdown_timeout
            coros = []
            for conn in self.connections:
                if hasattr(conn, "websocket") and conn.websocket:
                    coros.append(conn.websocket.close_connection())
                else:
                    conn.close()
            _shutdown = asyncio.gather(*coros, loop=self.loop)
            await _shutdown

    async def _run(self):
        for socket in self.sockets:
            state = ServerState(connections=self.connections)
            config = ServerConfig(
                host=None,
                port=None,
                socket=socket,
                connections=self.connections,
                **self._server_config
            )
            server = await Server(self.app.callable, config, state).run()
            self.servers[server] = state

    async def _check_alive(self):
        pid = os.getpid()
        try:
            while self.alive:
                self.notify()

                req_count = sum(
                    self.servers[srv]["total_requests"] for srv in self.servers
                )
                if self.max_requests and req_count > self.max_requests:
                    self.alive = False
                    self.log.info(
                        "Max requests exceeded, shutting down: %s", self
                    )
                elif pid == os.getpid() and self.ppid != os.getppid():
                    self.alive = False
                    self.log.info("Parent changed, shutting down: %s", self)
                else:
                    await asyncio.sleep(1.0, loop=self.loop)
        except (Exception, BaseException, GeneratorExit, KeyboardInterrupt):
            pass

    @staticmethod
    def _create_ssl_context(cfg):
        """ Creates SSLContext instance for usage in asyncio.create_server.
        See ssl.SSLSocket.__init__ for more details.
        """
        if not ssl:
            raise RuntimeError("Module ssl not installed!")
        ctx = ssl.SSLContext(cfg.ssl_version)
        ctx.load_cert_chain(cfg.certfile, cfg.keyfile)
        ctx.verify_mode = cfg.cert_reqs
        if cfg.ca_certs:
            ctx.load_verify_locations(cfg.ca_certs)
        if cfg.ciphers:
            ctx.set_ciphers(cfg.ciphers)
        return ctx

    def init_signals(self):
        self.loop.add_signal_handler(
            signal.SIGQUIT, self.handle_quit, signal.SIGQUIT, None
        )
        self.loop.add_signal_handler(
            signal.SIGTERM, self.handle_exit, signal.SIGTERM, None
        )
        self.loop.add_signal_handler(
            signal.SIGINT, self.handle_quit, signal.SIGINT, None
        )
        self.loop.add_signal_handler(
            signal.SIGWINCH, self.handle_winch, signal.SIGWINCH, None
        )
        self.loop.add_signal_handler(
            signal.SIGUSR1, self.handle_usr1, signal.SIGUSR1, None
        )
        self.loop.add_signal_handler(
            signal.SIGABRT, self.handle_abort, signal.SIGABRT, None
        )
        signal.siginterrupt(signal.SIGTERM, False)
        signal.siginterrupt(signal.SIGUSR1, False)

    def handle_quit(self, sig, frame):
        self.alive = False
        self.app.callable.is_running = False
        self.cfg.worker_int(self)

    def handle_abort(self, sig, frame):
        self.alive = False
        self.exit_code = 1
        self.cfg.worker_abort(self)
        sys.exit(1)
