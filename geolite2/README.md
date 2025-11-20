# GeoIP Database

This directory contains the MaxMind GeoLite2-Country database used for IP-based geolocation.

## Setup

The GeoLite2-Country database is required for regional knowledge base detection but is not included in the repository due to its size (9.4 MB).

### Download

```bash
# Automatic download (recommended):
curl -L "https://github.com/P3TERX/GeoLite.mmdb/releases/latest/download/GeoLite2-Country.mmdb" -o "geolite2/GeoLite2-Country.mmdb"

# Or download manually from:
# https://github.com/P3TERX/GeoLite.mmdb/releases/latest
```

### Verify

```bash
# Check file exists and is approximately 9-10 MB:
ls -lh geolite2/GeoLite2-Country.mmdb
```

## Alternative: Official MaxMind Database

For production use, consider using the official MaxMind GeoLite2 database:

1. Register for a free MaxMind account: https://www.maxmind.com/en/geolite2/signup
2. Download GeoLite2-Country database
3. Place `GeoLite2-Country.mmdb` in this directory

## Updates

The GeoLite2 database is updated monthly. To update:

```bash
# Remove old database
rm geolite2/GeoLite2-Country.mmdb

# Download latest version
curl -L "https://github.com/P3TERX/GeoLite.mmdb/releases/latest/download/GeoLite2-Country.mmdb" -o "geolite2/GeoLite2-Country.mmdb"

# Restart application to load new database
```

## Configuration

The database path is configured in `src/core/config.py`:

```python
geoip_db_path: str = "./geolite2/GeoLite2-Country.mmdb"
```

You can override this with an environment variable:

```bash
export GEOIP_DB_PATH="/path/to/your/GeoLite2-Country.mmdb"
```

## Troubleshooting

**Issue**: Application can't find GeoIP database
- Check file exists: `ls geolite2/GeoLite2-Country.mmdb`
- Check file size is ~9-10 MB (not 0 bytes)
- Check file permissions are readable

**Issue**: Regional detection not working
- Check logs for: "GeoIP database not found" or "GeoLocationService" errors
- Verify database file is valid (not corrupted download)

## License

GeoLite2 databases are distributed under the Creative Commons Attribution-ShareAlike 4.0 International License.

For more information: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
