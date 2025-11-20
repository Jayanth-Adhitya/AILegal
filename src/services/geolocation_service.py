"""IP-based geolocation service for regional knowledge base detection."""

import logging
from typing import Optional
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


class GeoLocationService:
    """
    Provides IP-based geolocation using MaxMind GeoLite2-Country database.

    Maps IP addresses to country codes and region codes for regional
    knowledge base selection.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize GeoLocationService with GeoIP2 database.

        Args:
            db_path: Path to GeoLite2-Country.mmdb file. If None, uses default from settings.
        """
        self.db_path = db_path
        self.reader = None
        self.db_available = False

        # Import geoip2 here to handle missing dependency gracefully
        try:
            import geoip2.database
            import geoip2.errors
            self.geoip2_database = geoip2.database
            self.geoip2_errors = geoip2.errors
        except ImportError:
            logger.error("geoip2 library not installed. Regional detection disabled. Install with: pip install geoip2")
            return

        # Load database
        if db_path is None:
            from ..core.config import settings
            db_path = settings.geoip_db_path

        self.db_path = db_path

        try:
            if not Path(db_path).exists():
                logger.warning(f"GeoIP database not found at {db_path}. Regional detection disabled.")
                logger.warning("Download from: https://github.com/P3TERX/GeoLite.mmdb/releases/latest")
                return

            self.reader = self.geoip2_database.Reader(db_path)
            self.db_available = True
            logger.info(f"GeoIP database loaded from {db_path}")

        except Exception as e:
            logger.error(f"Failed to load GeoIP database from {db_path}: {e}")
            logger.error("Regional detection disabled")

    @lru_cache(maxsize=1000)
    def get_country_from_ip(self, ip_address: str) -> Optional[str]:
        """
        Get ISO country code for an IP address.

        Args:
            ip_address: IP address string (e.g., "5.1.83.46")

        Returns:
            ISO 3166-1 alpha-2 country code (e.g., "AE" for UAE) or None if:
            - Database not available
            - IP address is invalid
            - IP address not found in database

        Example:
            >>> service = GeoLocationService()
            >>> service.get_country_from_ip("5.1.83.46")
            "AE"
            >>> service.get_country_from_ip("127.0.0.1")
            None
        """
        if not self.db_available or not self.reader:
            return None

        if not ip_address or ip_address.strip() == "":
            return None

        try:
            response = self.reader.country(ip_address)
            country_code = response.country.iso_code

            logger.debug(f"IP {ip_address} → Country {country_code}")
            return country_code

        except self.geoip2_errors.AddressNotFoundError:
            logger.debug(f"IP {ip_address} not found in GeoIP database")
            return None

        except Exception as e:
            logger.debug(f"Error looking up IP {ip_address}: {e}")
            return None

    def get_region_from_ip(self, ip_address: str) -> Optional[str]:
        """
        Get region code for an IP address.

        Maps IP → Country Code → Region Code using REGION_CONFIG.

        Args:
            ip_address: IP address string

        Returns:
            Region code (e.g., "dubai_uae") or None if:
            - Country not detected
            - Country not mapped to any enabled region

        Example:
            >>> service = GeoLocationService()
            >>> service.get_region_from_ip("5.1.83.46")  # UAE IP
            "dubai_uae"
            >>> service.get_region_from_ip("8.8.8.8")    # US IP
            None
        """
        country_code = self.get_country_from_ip(ip_address)

        if not country_code:
            return None

        # Map country code to region code
        from ..core.config import get_region_for_country
        region_code = get_region_for_country(country_code)

        if region_code:
            logger.debug(f"IP {ip_address} → Country {country_code} → Region {region_code}")
        else:
            logger.debug(f"IP {ip_address} → Country {country_code} → No regional KB")

        return region_code

    def is_available(self) -> bool:
        """
        Check if GeoLocationService is available and functional.

        Returns:
            True if GeoIP database is loaded and ready, False otherwise.
        """
        return self.db_available and self.reader is not None

    def close(self):
        """Close GeoIP database reader."""
        if self.reader:
            self.reader.close()
            self.reader = None
            logger.info("GeoIP database closed")


# Global instance (lazy initialization)
_geo_service: Optional[GeoLocationService] = None


def get_geo_service() -> GeoLocationService:
    """
    Get or create global GeoLocationService instance.

    Returns:
        GeoLocationService singleton instance.

    Example:
        >>> from src.services.geolocation_service import get_geo_service
        >>> geo = get_geo_service()
        >>> region = geo.get_region_from_ip("5.1.83.46")
    """
    global _geo_service
    if _geo_service is None:
        _geo_service = GeoLocationService()
    return _geo_service
