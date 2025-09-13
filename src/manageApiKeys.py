"""
API Keys Management Utility
Command-line tool to manage API keys for social media scrapers
"""

import argparse
from classes.apiKeysManager import api_keys_manager


def list_keys(service: str = None):
    """List all API keys or keys for a specific service"""
    if service:
        if service not in api_keys_manager.keys:
            print(f"Service '{service}' not found")
            return

        status = api_keys_manager.get_key_status(service)
        print(f"\n{service.upper()} API Keys Status:")
        print("=" * 50)
        print(f"Total Keys: {status['total_keys']}")
        print(f"Active Keys: {status['active_keys']}")
        print(f"Inactive Keys: {status['inactive_keys']}")
        print("\nKey Details:")

        for key_info in status["keys"]:
            status_icon = "✅" if key_info["is_active"] else "❌"
            print(f"{status_icon} {key_info['name']}")
            print(f"   Active: {key_info['is_active']}")
            print(f"   Error Count: {key_info['error_count']}")
            print(f"   Last Used: {key_info['last_used'] or 'Never'}")
            if key_info["quota_reset_time"]:
                print(f"   Quota Reset: {key_info['quota_reset_time']}")
            print()
    else:
        print("\nAll API Keys Status:")
        print("=" * 50)
        for service_name in api_keys_manager.keys:
            status = api_keys_manager.get_key_status(service_name)
            print(
                f"{service_name.upper()}: {status['active_keys']}/{status['total_keys']} active"
            )


def add_key(service: str, key: str, name: str = None):
    """Add a new API key"""
    try:
        api_keys_manager.add_api_key(service, key, name)
        print(f"✅ Successfully added API key for {service}")
    except Exception as e:
        print(f"❌ Error adding API key: {e}")


def remove_key(service: str, key: str):
    """Remove an API key"""
    try:
        if api_keys_manager.remove_api_key(service, key):
            print(f"✅ Successfully removed API key from {service}")
        else:
            print(f"❌ API key not found in {service}")
    except Exception as e:
        print(f"❌ Error removing API key: {e}")


def test_keys(service: str = None):
    """Test API keys by making a simple request"""
    import requests

    if service:
        services_to_test = [service]
    else:
        services_to_test = list(api_keys_manager.keys.keys())

    for service_name in services_to_test:
        print(f"\nTesting {service_name.upper()} keys:")
        print("-" * 30)

        active_keys = [k for k in api_keys_manager.keys[service_name] if k.is_active]

        if not active_keys:
            print("No active keys to test")
            continue

        for key_info in active_keys:
            try:
                if service_name == "youtube":
                    # Test YouTube API
                    url = "https://www.googleapis.com/youtube/v3/search"
                    params = {
                        "part": "snippet",
                        "maxResults": 1,
                        "q": "test",
                        "key": key_info.key,
                    }
                    response = requests.get(url, params=params, timeout=10)

                    if response.status_code == 200:
                        print(f"✅ {key_info.name}: Working")
                    elif response.status_code == 403:
                        error_data = response.json()
                        error_reason = (
                            error_data.get("error", {})
                            .get("errors", [{}])[0]
                            .get("reason", "unknown")
                        )
                        print(f"❌ {key_info.name}: {error_reason}")
                    else:
                        print(f"⚠️ {key_info.name}: HTTP {response.status_code}")

                elif service_name == "twitter":
                    # Test Twitter API
                    url = "https://api.twitter.com/2/tweets/search/recent"
                    headers = {"Authorization": key_info.key}
                    params = {"query": "test", "max_results": 10}
                    response = requests.get(
                        url, headers=headers, params=params, timeout=10
                    )

                    if response.status_code == 200:
                        print(f"✅ {key_info.name}: Working")
                    elif response.status_code == 401:
                        print(f"❌ {key_info.name}: Invalid token")
                    elif response.status_code == 429:
                        print(f"⚠️ {key_info.name}: Rate limited")
                    else:
                        print(f"⚠️ {key_info.name}: HTTP {response.status_code}")

                elif service_name == "apify":
                    # Test Apify API
                    url = "https://api.apify.com/v2/acts"
                    headers = {"Authorization": f"Bearer {key_info.key}"}
                    response = requests.get(url, headers=headers, timeout=10)

                    if response.status_code == 200:
                        print(f"✅ {key_info.name}: Working")
                    elif response.status_code == 401:
                        print(f"❌ {key_info.name}: Invalid token")
                    else:
                        print(f"⚠️ {key_info.name}: HTTP {response.status_code}")

            except Exception as e:
                print(f"❌ {key_info.name}: Error - {e}")


def reset_errors(service: str = None):
    """Reset error counts and reactivate keys"""
    if service:
        if service not in api_keys_manager.keys:
            print(f"Service '{service}' not found")
            return

        for key_info in api_keys_manager.keys[service]:
            key_info.error_count = 0
            key_info.is_active = True
            key_info.quota_reset_time = None
        print(f"✅ Reset errors for {service}")
    else:
        for service_name in api_keys_manager.keys:
            for key_info in api_keys_manager.keys[service_name]:
                key_info.error_count = 0
                key_info.is_active = True
                key_info.quota_reset_time = None
        print("✅ Reset errors for all services")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Manage API keys for social media scrapers"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List API keys")
    list_parser.add_argument(
        "--service", help="Filter by service (youtube, twitter, apify)"
    )

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new API key")
    add_parser.add_argument("service", help="Service name (youtube, twitter, apify)")
    add_parser.add_argument("key", help="API key")
    add_parser.add_argument("--name", help="Custom name for the key")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove an API key")
    remove_parser.add_argument("service", help="Service name")
    remove_parser.add_argument("key", help="API key to remove")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test API keys")
    test_parser.add_argument("--service", help="Test specific service")

    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset error counts")
    reset_parser.add_argument("--service", help="Reset specific service")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "list":
        list_keys(args.service)
    elif args.command == "add":
        add_key(args.service, args.key, args.name)
    elif args.command == "remove":
        remove_key(args.service, args.key)
    elif args.command == "test":
        test_keys(args.service)
    elif args.command == "reset":
        reset_errors(args.service)


if __name__ == "__main__":
    main()
