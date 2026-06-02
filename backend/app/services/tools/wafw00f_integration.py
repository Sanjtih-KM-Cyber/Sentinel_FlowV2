import asyncio
import re
from typing import Dict, Any

class Wafw00fIntegration:
    @staticmethod
    async def run_scan(target_url: str) -> Dict[str, Any]:
        """
        Executes wafw00f against the target.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "wafw00f", target_url, "-a",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode()
            
            detected = False
            vendor = None
            confidence = 0.0
            
            # Wafw00f outputs e.g. "The site is behind Cloudflare (Cloudflare Inc.) WAF."
            match = re.search(r"is behind (.*?) WAF", output, re.IGNORECASE)
            if match:
                detected = True
                vendor = match.group(1).strip()
                confidence = 0.95
            elif "No WAF detected" not in output and "WAF" in output.upper():
                detected = True
                vendor = "Unknown WAF Vendor"
                confidence = 0.6
            
            return {
                "target": target_url,
                "detected": detected,
                "vendor": vendor,
                "confidence": confidence,
                "raw_output": output,
                "error": stderr.decode() if process.returncode != 0 else None
            }
        except FileNotFoundError:
            # Fallback for environment without wafw00f installed
            return {
                "target": target_url,
                "detected": False,
                "vendor": None,
                "confidence": 0.0,
                "raw_output": "[MOCK] wafw00f not found in PATH",
                "error": "Tool not installed"
            }
