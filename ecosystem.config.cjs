const path = require('node:path');
const root = __dirname;
const python = process.env.DATAWAIS_PYTHON || path.join(root, '.venv', 'Scripts', 'python.exe');
const server = {
  name: 'datawais-server', cwd: root,
  script: path.join(root, 'scripts', 'bootstrap.py'), interpreter: python,
  args: ['datawais.server', '--root', 'workspace', '--secrets', '.runtime/secrets.json'],
  autorestart: true, restart_delay: 2000, max_restarts: 15,
  out_file: path.join(root, '.runtime', 'server.out.log'),
  error_file: path.join(root, '.runtime', 'server.err.log'),
  env: { PYTHONUNBUFFERED: '1', DATAWAIS_DEPS: process.env.DATAWAIS_DEPS || '', DATAWAIS_PUBLIC_HOST: process.env.DATAWAIS_PUBLIC_HOST || '' }
};
const apps = [server];
if (process.env.DATAWAIS_CLOUDFLARED) apps.push({
  name: 'datawais-tunnel', cwd: root,
  script: process.env.DATAWAIS_CLOUDFLARED, interpreter: 'none',
  args: ['tunnel', '--url', 'http://127.0.0.1:8765', '--no-autoupdate', '--protocol', 'http2'],
  autorestart: true, restart_delay: 3000, max_restarts: 15,
  out_file: path.join(root, '.runtime', 'tunnel.out.log'),
  error_file: path.join(root, '.runtime', 'tunnel.err.log')
});
module.exports = { apps };
