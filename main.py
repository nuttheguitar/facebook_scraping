#!/usr/bin/env python3
"""
Facebook UI Screenshot Scraper
Main entry point for capturing Facebook post screenshots with human behavior simulation.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from strategies.facebook_scraper import FacebookUIScraper

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()


def main():
    """Main function to run the Facebook UI screenshot scraper."""
    parser = argparse.ArgumentParser(
        description="Facebook UI Screenshot Scraper - Capture post screenshots with OCR-ready content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Quick screenshot capture of a Facebook group
            python main.py --target-url "https://www.facebook.com/groups/example" --max-posts 10

            # Capture screenshots with authentication and profile persistence
            python main.py --target-url "https://www.facebook.com/groups/example" --max-posts 20 --use-profile

            # Capture screenshots without profile (fresh session each time)
            python main.py --target-url "https://www.facebook.com/groups/example" --max-posts 20 --no-profile

            # Custom database path
            python main.py --target-url "https://www.facebook.com/groups/example" --db-path "my_facebook_data.db"

            # Disable post validation to capture all containers
            python main.py --target-url "https://www.facebook.com/groups/example" --no-validate-posts

            Profile Management:
            --use-profile (default): Uses Chrome profile to save Facebook login sessions
            --no-profile: Starts fresh each time without saving sessions
            💡 With profiles enabled, you only need to login once!

            Post Validation:
            --validate-posts (default): Enable post validation to filter actual posts from comments
            --no-validate-posts: Disable validation - capture all containers as posts
            💡 Use --no-validate-posts when you want to see everything Facebook serves!

            Environment Variables:
            FACEBOOK_EMAIL: Your Facebook email for authentication
            FACEBOOK_PASSWORD: Your Facebook password for authentication
            FACEBOOK_GROUP_URL: Default Facebook group URL (can override with --target-url)
        """,
    )

    parser.add_argument(
        "--target-url",
        help="Facebook group URL to scrape (overrides FACEBOOK_GROUP_URL env var)",
    )
    parser.add_argument(
        "--headless",
        default=False,
        action="store_true",
        help="Run in headless mode (no browser UI)",
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=10,
        help="Maximum posts to capture screenshots (default: 10)",
    )
    parser.add_argument(
        "--db-path",
        default="facebook_posts.db",
        help="Database path for storing scraped posts (default: facebook_posts.db)",
    )
    parser.add_argument(
        "--use-profile",
        default=True,
        action="store_true",
        help="Use Chrome profile for persistent Facebook sessions (default: True)",
    )
    parser.add_argument(
        "--no-profile",
        dest="use_profile",
        action="store_false",
        help="Disable Chrome profile usage (start fresh each time)",
    )
    parser.add_argument(
        "--validate-posts",
        default=True,
        action="store_true",
        help="Enable post validation to filter actual posts from comments (default: True)",
    )
    parser.add_argument(
        "--no-validate-posts",
        dest="validate_posts",
        action="store_false",
        help="Disable post validation - capture all containers as posts",
    )

    args = parser.parse_args()

    # Get target URL from args or environment variable
    target_url = args.target_url or os.getenv("FACEBOOK_GROUP_URL")
    if not target_url:
        print("❌ Error: No target URL provided!")
        print("   Use --target-url or set FACEBOOK_GROUP_URL environment variable")
        print("   Example: --target-url 'https://www.facebook.com/groups/example'")
        return

    # Validate Facebook group URL
    if not target_url.startswith("https://www.facebook.com/groups/"):
        print("❌ Error: Invalid Facebook group URL!")
        print(
            "   URL must be a Facebook group (e.g., https://www.facebook.com/groups/example)"
        )
        return

    # Create Facebook scraper instance with validation control
    scraper = FacebookUIScraper(
        db_path=args.db_path, validate_posts=args.validate_posts
    )

    try:
        # Setup driver with profile management
        if args.use_profile:
            print(
                "🔐 Setting up WebDriver with profile management for persistent Facebook sessions..."
            )
            print("💾 Your Facebook login will be saved and reused in future runs!")
        else:
            print(
                "🔄 Setting up WebDriver without profile (fresh session each time)..."
            )

        if not scraper.setup_driver(headless=args.headless):
            print("❌ Failed to setup WebDriver")
            return

        if args.use_profile:
            print(
                "✅ WebDriver setup completed with profile management and human behavior simulation"
            )
            print("🔐 Your Facebook session will persist between runs!")
        else:
            print("✅ WebDriver setup completed with human behavior simulation")

        # Check for login credentials
        email = os.getenv("FACEBOOK_EMAIL")
        password = os.getenv("FACEBOOK_PASSWORD")

        if email and password:
            print("🔐 Attempting to authenticate with Facebook...")
            credentials = {"email": email, "password": password}
            if scraper.authenticate(credentials):
                print("✅ Facebook authentication successful!")
            else:
                print("⚠️ Authentication failed, continuing in public mode...")
        else:
            print("ℹ️ No Facebook credentials provided, running in public mode...")
            print(
                "   Set FACEBOOK_EMAIL and FACEBOOK_PASSWORD environment variables for login"
            )

        # Start screenshot capture
        print(f"\n📸 Starting to capture Facebook post screenshots: {target_url}")
        print(f"📝 Max posts to capture: {args.max_posts}")
        print(
            f"🔍 Post validation: {'✅ Enabled' if args.validate_posts else '❌ Disabled'}"
        )
        if args.validate_posts:
            print("   Only actual posts will be processed (comments filtered out)")
        else:
            print("   All containers will be captured as posts (no filtering)")
        print(
            "🔄 This will expand content and capture screenshots for OCR processing..."
        )

        # Capture post screenshots
        posts = scraper.scrape_posts(target_url, max_posts=args.max_posts)

        if posts:
            print(f"✅ Successfully captured {len(posts)} post screenshots!")

            # Show sample data
            print("\n📋 Sample captured posts:")
            for i, post in enumerate(posts[:3], 1):
                print(f"  {i}. Post ID: {post.get('post_id', 'N/A')}")
                print(f"     Screenshot: {post.get('screenshot_path', 'N/A')}")
                print(f"     Scraped at: {post.get('scraped_at', 'N/A')}")
                print(
                    f"     Container role: {post.get('container_info', {}).get('role', 'N/A')}"
                )
                print(
                    f"     Container testid: {post.get('container_info', {}).get('data_testid', 'N/A')}"
                )
                print()

            # Show screenshot summary
            print("\n📸 Screenshot Summary:")
            print(f"   📁 Directory: {scraper.screenshot_dir}")
            print(f"   🖼️  Screenshots captured: {len(posts)}")

            # Calculate total size of screenshots
            total_size_mb = 0
            for post in posts:
                screenshot_path = post.get("screenshot_path")
                if screenshot_path and os.path.exists(screenshot_path):
                    total_size_mb += os.path.getsize(screenshot_path) / (1024 * 1024)
            print(f"   💾 Total size: {total_size_mb:.2f} MB")

            # Show comprehensive stats
            print("📊 Scraping Statistics:")
            print("   🎯 Strategy: Screenshot-only with scroll-find-capture logic")
            print(
                f"   🔐 Authentication: {'✅ Yes' if scraper.is_authenticated else '❌ No'}"
            )
            print("   🤖 Human Behavior: ✅ Enabled")
            print(
                f"   🚗 Driver Status: {'✅ Active' if scraper.driver else '❌ Inactive'}"
            )

        else:
            print("❌ No post screenshots were captured")
            print("   This could be due to:")
            print("   - Group is private or requires membership")
            print("   - No posts available in the group")
            print("   - Facebook's anti-scraping measures")
            print("   - Network or browser issues")

    except KeyboardInterrupt:
        print("\n🛑 Operation stopped by user")
    except Exception as e:
        print(f"❌ Error during execution: {str(e)}")
        if hasattr(scraper, "logger"):
            scraper.logger.error(f"Detailed error: {str(e)}", exc_info=True)
    finally:
        # Clean up
        print("\n🧹 Cleaning up and closing scraper...")
        scraper.close()
        print("✅ Scraper cleaned up and closed")


if __name__ == "__main__":
    main()
