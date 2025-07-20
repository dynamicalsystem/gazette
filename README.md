# dynamicalsystem.gazette

This is the uv workspace for [dynamicalsystem.gazette](https://github.com/DynamicalSystem/gazette/blob/main/gazette/README.md)

## Deploy

To quickly deploy gazette to a Docker host:

```bash
curl -H 'Cache-Control: no-cache' -sSL https://raw.githubusercontent.com/dynamicalsystem/gazette/main/deploy.sh | bash
```

Or download and review the script first:

```bash
curl -O https://raw.githubusercontent.com/dynamicalsystem/gazette/main/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

This will:
- Download the docker-compose.yml
- Create necessary directories
- Deploy the gazette and signal services

Remember to copy your configuration files to `~/.local/share/dynamicalsystem/config/` after deployment.
