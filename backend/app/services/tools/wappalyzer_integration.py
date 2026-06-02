import asyncio
import json
from typing import Dict, Any

class WappalyzerIntegration:
    @staticmethod
    async def run_scan(target_url: str) -> Dict[str, Any]:
        """
        Executes wappalyzer against the target via npx.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "npx", "-y", "wappalyzer", target_url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode()
            technologies = []
            
            if output:
                try:
                    parsed = json.loads(output)
                    if "technologies" in parsed:
                        for t in parsed["technologies"]:
                            technologies.append({
                                "name": t.get("name"),
                                "confidence": t.get("confidence", 0),
                                "categories": [c.get("name") if isinstance(c, dict) else c for c in t.get("categories", [])],
                                "version": t.get("version")
                            })
                    elif isinstance(parsed, list):
                        for t in parsed:
                            if isinstance(t, dict):
                                technologies.append({
                                    "name": t.get("name"),
                                    "confidence": t.get("confidence", 0),
                                    "categories": [c.get("name") if isinstance(c, dict) else c for c in t.get("categories", [])],
                                    "version": t.get("version")
                                })
                except json.JSONDecodeError:
                    pass
            
            return {
                "target": target_url,
                "technologies": technologies,
                "raw_output": output,
                "error": stderr.decode() if process.returncode != 0 else None
            }
        except FileNotFoundError:
            return {
                "target": target_url,
                "technologies": [],
                "raw_output": "[MOCK] npx wappalyzer not found",
                "error": "Tool not installed"
            }
