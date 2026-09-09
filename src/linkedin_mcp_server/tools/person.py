# src/linkedin_mcp_server/tools/person.py
"""
Person profile tools for LinkedIn MCP server.

This module provides tools for scraping LinkedIn person profiles using LLM-based extraction.
"""

from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from linkedin_scraper.llm_scraper import scrape_profile_text, extract_with_llm, get_driver
from linkedin_mcp_server.tools.storage import save_profile

# Reusable driver instance
_driver = None


def _get_driver():
    """Get or create a reusable Chrome driver."""
    global _driver
    if _driver is None:
        _driver = get_driver()
    return _driver


def register_person_tools(mcp: FastMCP) -> None:
    """
    Register all person-related tools with the MCP server.

    Args:
        mcp (FastMCP): The MCP server instance
    """

    @mcp.tool()
    async def get_person_profile(
        linkedin_url: str, event_name: str = None
    ) -> Dict[str, Any]:
        """
        Scrape a person's LinkedIn profile using LLM-based extraction.

        Navigates to all profile sections (about, experience, education, posts)
        and uses Claude to extract structured data. Resilient to LinkedIn HTML changes.

        Args:
            linkedin_url (str): The LinkedIn URL of the person's profile
            event_name (str, optional): Name of the event to organize profiles under

        Returns:
            Dict[str, Any]: Structured data from the person's profile and save status
        """
        try:
            print("🔍 Getting Chrome driver...")
            driver = _get_driver()

            print(f"📄 Scraping sections from {linkedin_url}")
            sections = scrape_profile_text(driver, linkedin_url)

            print("🤖 Extracting with LLM...")
            profile_data = extract_with_llm(sections)

            # Add URL to profile data
            profile_data["linkedin_url"] = linkedin_url

            # Compute derived fields for compatibility
            profile_data["post_count"] = len(profile_data.get("recent_posts", []))
            posts = profile_data.get("recent_posts", [])
            profile_data["last_activity"] = posts[0].get("time_ago") if posts else None

            # Save the profile automatically
            save_result = await save_profile(profile_data, event_name)

            # Return both profile data and save status
            return {"profile": profile_data, "save_status": save_result}

        except Exception as e:
            print(f"❌ Error scraping profile: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Failed to scrape profile: {str(e)}"}
