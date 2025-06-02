"""
Storage tools for LinkedIn MCP server.

This module provides tools for saving and loading LinkedIn profile data.
"""

import json
import os
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

# Create storage directory if it doesn't exist
STORAGE_DIR = os.path.expanduser("~/linkedin_data")
os.makedirs(STORAGE_DIR, exist_ok=True)


async def save_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save a LinkedIn profile to disk."""
    try:
        # Create a filename from the profile name
        filename = f"{profile_data['name'].lower().replace(' ', '_')}.json"
        filepath = os.path.join(STORAGE_DIR, filename)

        # Save the profile data
        with open(filepath, "w") as f:
            json.dump(profile_data, f, indent=2)

        return {
            "status": "success",
            "message": f"Profile saved to {filepath}",
            "filepath": filepath,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to save profile: {str(e)}"}


def register_storage_tools(mcp: FastMCP) -> None:
    """Register storage-related tools with the MCP server."""

    @mcp.tool()
    async def load_profile(profile_name: str) -> Dict[str, Any]:
        """Load a LinkedIn profile from disk."""
        try:
            filename = f"{profile_name.lower().replace(' ', '_')}.json"
            filepath = os.path.join(STORAGE_DIR, filename)

            if not os.path.exists(filepath):
                return {
                    "status": "error",
                    "message": f"Profile not found: {profile_name}",
                }

            with open(filepath, "r") as f:
                profile_data = json.load(f)

            return {"status": "success", "profile": profile_data}
        except Exception as e:
            return {"status": "error", "message": f"Failed to load profile: {str(e)}"}

    @mcp.tool()
    async def list_profiles() -> Dict[str, Any]:
        """List all saved LinkedIn profiles."""
        try:
            profiles = []
            for filename in os.listdir(STORAGE_DIR):
                if filename.endswith(".json"):
                    with open(os.path.join(STORAGE_DIR, filename), "r") as f:
                        profile = json.load(f)
                        profiles.append(
                            {
                                "name": profile.get("name", "Unknown"),
                                "filepath": os.path.join(STORAGE_DIR, filename),
                            }
                        )

            return {"status": "success", "profiles": profiles}
        except Exception as e:
            return {"status": "error", "message": f"Failed to list profiles: {str(e)}"}
