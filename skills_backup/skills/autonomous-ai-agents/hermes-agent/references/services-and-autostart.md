# Hermes Services Architecture & Auto-Start

## Key Insight: hermes-gateway Includes All Platform Integrations

The `hermes-gateway.service` includes **all** messaging platform integrations (WeChat, Telegram, Discord, etc.) in a single service. There is NO separate service for ClawBot/hermesclaw.

```
hermes-gateway.service
├── Hermes main gateway
├── WeChat (Weixin) integration
├── Telegram integration
├── Discord integration
└── All other platforms
```

**Do NOT look for a separate `hermesclaw` service** — it doesn't exist as a systemd unit.

## Check Service Status

```bash
# Check if gateway is running
systemctl status hermes-gateway

# Check if it's enabled (auto-start on boot)
systemctl is-enabled hermes-gateway

# View logs
journalctl -u hermes-gateway -f
```

## Auto-Start Configuration

The `hermes-gateway.service` is typically configured with:
```ini
[Install]
WantedBy=multi-user.target
```

And enabled via:
```bash
sudo systemctl enable hermes-gateway
```

This means the service **automatically starts on boot** — no manual intervention needed after system restart.

## Manual Start/Stop

```bash
# Start
sudo systemctl start hermes-gateway

# Stop
sudo systemctl stop hermes-gateway

# Restart
sudo systemctl restart hermes-gateway
```

## Curator Configuration

Curator manages skill lifecycle (stale detection, archival). Enable it:

```bash
hermes config set memory.curator.enabled true
hermes config set memory.curator.frequency weekly
hermes config set memory.curator.stale_days 30
hermes config set memory.curator.archive_days 90
```

Verify:
```bash
hermes config get memory.curator
```

## Common Confusion

| Myth | Reality |
|------|---------|
| Need separate ClawBot service | ❌ ClawBot is part of hermes-gateway |
| Need to manually start after reboot | ❌ Service is enabled, auto-starts |
| hermesclaw is a systemd service | ❌ It's not a separate service |

## WSL-Specific Notes

On WSL2, ensure systemd is enabled in `/etc/wsl.conf`:
```ini
[boot]
systemd=true
```

Without this, systemd services won't auto-start. The gateway will fall back to `nohup` mode (dies when terminal closes).
