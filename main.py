#!/usr/bin/env python3
"""
Facebook Public Group Post Scraper
Main entry point for the Facebook scraper with improved user experience.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strategies.facebook_scraper import FacebookScraper


# Load environment variables
load_dotenv()


def main():
    """Main function to run the Facebook scraper with improved user experience."""
    parser = argparse.ArgumentParser(
        description="Facebook Public Group Post Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Quick scrape of a Facebook group
            python main.py --target-url "https://www.facebook.com/groups/example" --mode scrape

            # Monitor a group continuously
            python main.py --target-url "https://www.facebook.com/groups/example" --mode monitor

            # Scrape with custom settings
            python main.py --target-url "https://www.facebook.com/groups/example" --max-posts 50 --fast-mode

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
        default=20,
        help="Maximum posts to scrape per session (default: 20)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Check interval in minutes for monitoring mode (default: 30)",
    )
    parser.add_argument(
        "--db-path",
        default="facebook_posts.db",
        help="Database path for storing scraped posts (default: facebook_posts.db)",
    )
    parser.add_argument(
        "--mode",
        choices=["scrape", "monitor"],
        default="scrape",
        help="Scraping mode: scrape once or monitor continuously (default: scrape)",
    )
    parser.add_argument(
        "--fast-mode",
        action="store_true",
        help="Enable fast mode for quicker scraping (may increase detection risk)",
    )
    parser.add_argument(
        "--use-existing-profile",
        default=True,
        help="Use existing Chrome profile with Facebook login",
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
    scraper = FacebookScraper(db_path=args.db_path, fast_mode=args.fast_mode)

    try:
        # Setup driver
        print("🔧 Setting up WebDriver...")
        if not scraper.setup_driver(
            headless=args.headless, use_existing_profile=args.use_existing_profile
        ):
            print("❌ Failed to setup WebDriver")
            return

        print("✅ WebDriver setup completed")

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

        if args.mode == "scrape":
            # One-time scraping
            print(f"\n📊 Starting to scrape Facebook group: {target_url}")
            print(f"📝 Max posts to scrape: {args.max_posts}")

            posts = scraper.scrape_content(target_url, max_items=args.max_posts)

            if posts:
                print(f"✅ Successfully scraped {len(posts)} posts!")

                # Save to database
                if hasattr(scraper, "save_posts_to_database"):
                    scraper.save_posts_to_database(posts)
                    print(f"💾 Saved {len(posts)} posts to database: {args.db_path}")

                # Export to JSON
                if hasattr(scraper, "save_posts_to_json"):
                    output_file = "scraped_facebook_posts.json"
                    scraper.save_posts_to_json(posts, output_file)
                    print(f"📄 Exported data to: {output_file}")

                # Show sample data
                print("\n📋 Sample scraped posts:")
                for i, post in enumerate(posts[:3], 1):
                    content_preview = (
                        post.content[:100] + "..."
                        if len(post.content) > 100
                        else post.content
                    )
                    print(f"  {i}. {post.title or 'No title'}")
                    print(f"     Content: {content_preview}")
                    print(f"     URL: {post.url}")
                    print()

                # Show stats
                if hasattr(scraper, "get_scraping_stats"):
                    stats = scraper.get_scraping_stats()
                    print(f"📊 Scraping statistics: {stats}")
            else:
                print("❌ No posts were scraped")
                print("   This could be due to:")
                print("   - Group is private or requires membership")
                print("   - No posts available in the group")
                print("   - Facebook's anti-scraping measures")

        else:
            # Continuous monitoring
            print(
                f"\n📊 Starting continuous monitoring of Facebook group: {target_url}"
            )
            print(f"⏰ Check interval: {args.interval} minutes")
            print(f"📝 Max posts per check: {args.max_posts}")
            print("🛑 Press Ctrl+C to stop monitoring")
            print()

            scraper.monitor_group(
                group_url=target_url,
                interval_minutes=args.interval,
                max_posts=args.max_posts,
            )

    except KeyboardInterrupt:
        print("\n🛑 Operation stopped by user")
    except Exception as e:
        print(f"❌ Error during execution: {str(e)}")
        if hasattr(scraper, "logger"):
            scraper.logger.error(f"Detailed error: {str(e)}", exc_info=True)
    finally:
        # Clean up
        scraper.close()
        print("🧹 Scraper cleaned up and closed")


if __name__ == "__main__":
    main()
