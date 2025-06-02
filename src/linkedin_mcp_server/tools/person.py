# src/linkedin_mcp_server/tools/person.py
"""
Person profile tools for LinkedIn MCP server.

This module provides tools for scraping LinkedIn person profiles.
"""

from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP
from linkedin_scraper import Person

from linkedin_mcp_server.drivers.chrome import get_or_create_driver
from linkedin_mcp_server.tools.storage import save_profile


def register_person_tools(mcp: FastMCP) -> None:
    """
    Register all person-related tools with the MCP server.

    Args:
        mcp (FastMCP): The MCP server instance
    """

    @mcp.tool()
    async def get_person_profile(linkedin_url: str) -> Dict[str, Any]:
        """
        Scrape a person's LinkedIn profile and save it automatically.

        Args:
            linkedin_url (str): The LinkedIn URL of the person's profile

        Returns:
            Dict[str, Any]: Structured data from the person's profile and save status
        """
        print("🔍 Creating driver")
        driver = get_or_create_driver()
        print("🔍 Driver created. Exiting...")

        try:
            print(f"🔍 Scraping profile: {linkedin_url}")
            person = Person(linkedin_url, driver=driver, close_on_complete=False)

            # Convert experiences to structured dictionaries
            experiences: List[Dict[str, Any]] = [
                {
                    "position_title": exp.position_title,
                    "company": exp.institution_name,
                    "from_date": exp.from_date,
                    "to_date": exp.to_date,
                    "duration": exp.duration,
                    "location": exp.location,
                    "description": exp.description,
                }
                for exp in person.experiences
            ]

            # Convert educations to structured dictionaries
            educations: List[Dict[str, Any]] = [
                {
                    "institution": edu.institution_name,
                    "degree": edu.degree,
                    "from_date": edu.from_date,
                    "to_date": edu.to_date,
                    "description": edu.description,
                }
                for edu in person.educations
            ]

            # Build the complete profile data
            profile_data = {
                "name": person.name,
                "linkedin_url": linkedin_url,  # Add the URL for reference
                "company": person.company,
                "job_title": person.job_title,
                "about": person.about,
                "experiences": experiences,
                "educations": educations,
            }

            # Save the profile automatically
            save_result = await save_profile(profile_data)

            # Return both profile data and save status
            return {"profile": profile_data, "save_status": save_result}

        except Exception as e:
            print(f"❌ Error scraping profile: {e}")
            return {"error": f"Failed to scrape profile: {str(e)}"}
