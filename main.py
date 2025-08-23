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

            Profile Management:
            --use-profile (default): Uses Chrome profile to save Facebook login sessions
            --no-profile: Starts fresh each time without saving sessions
            💡 With profiles enabled, you only need to login once!

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
        "--headless", default=False, action="store_true", help="Run in headless mode (no browser UI)"
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

    # Create Facebook scraper instance
    scraper = FacebookUIScraper(db_path=args.db_path)

    try:
        # Setup driver with profile management
        if args.use_profile:
            print("🔐 Setting up WebDriver with profile management for persistent Facebook sessions...")
            print("💾 Your Facebook login will be saved and reused in future runs!")
        else:
            print("🔄 Setting up WebDriver without profile (fresh session each time)...")
            
        if not scraper.setup_driver(headless=args.headless):
            print("❌ Failed to setup WebDriver")
            return

        if args.use_profile:
            print("✅ WebDriver setup completed with profile management and human behavior simulation")
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
        print("🔄 This will expand content and capture screenshots for OCR processing...")

        # Capture post screenshots
        posts = scraper.scrape_posts(target_url, max_posts=args.max_posts)

        if posts:
            print(f"✅ Successfully captured {len(posts)} post screenshots!")

            # Save to database
            if hasattr(scraper, "save_posts_to_database"):
                saved_count = scraper.save_posts_to_database(posts)
                print(f"💾 Saved {saved_count} posts to database: {args.db_path}")

            # Export to JSON
            if hasattr(scraper, "save_posts_to_json"):
                output_file = "facebook_screenshots.json"
                if scraper.save_posts_to_json(posts, output_file):
                    print(f"📄 Exported data to: {output_file}")

            # Show screenshot summary
            if hasattr(scraper, "get_screenshot_summary"):
                screenshot_stats = scraper.get_screenshot_summary()
                print("\n📸 Screenshot Summary:")
                print(f"   📁 Directory: {screenshot_stats.get('screenshot_dir', 'N/A')}")
                print(f"   🖼️  Screenshots captured: {screenshot_stats.get('screenshots_found', 0)}")
                print(f"   💾 Total size: {screenshot_stats.get('total_size_mb', 0)} MB")

            # Show sample data
            print("\n📋 Sample captured posts:")
            for i, post in enumerate(posts[:3], 1):
                print(f"  {i}. Post ID: {post.get('post_id', 'N/A')}")
                print(f"     Author: {post.get('author', 'N/A')}")
                print(f"     Content: {post.get('content', 'N/A')[:100]}...")
                print(f"     Screenshot: {post.get('screenshot_path', 'N/A')}")
                print(f"     Timestamp: {post.get('timestamp', 'N/A')}")
                print()

            # Show comprehensive stats
            if hasattr(scraper, "get_scraping_stats"):
                stats = scraper.get_scraping_stats()
                print("📊 Scraping Statistics:")
                print(f"   🎯 Strategy: {stats.get('scraping_strategy', 'N/A')}")
                print(f"   🔐 Authentication: {'✅ Yes' if stats.get('authentication_status') else '❌ No'}")
                print(f"   🤖 Human Behavior: {'✅ Enabled' if stats.get('human_behavior_enabled') else '❌ Disabled'}")
                print(f"   🚗 Driver Status: {'✅ Active' if stats.get('driver_active') else '❌ Inactive'}")
                
                # Show human behavior stats if available
                if 'total_clicks' in stats:
                    print(f"   🖱️  Total clicks: {stats.get('total_clicks', 0)}")
                if 'total_scrolls' in stats:
                    print(f"   📜 Total scrolls: {stats.get('total_scrolls', 0)}")
                if 'session_duration' in stats:
                    print(f"   ⏱️  Session duration: {stats.get('session_duration', 'N/A')}")

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
