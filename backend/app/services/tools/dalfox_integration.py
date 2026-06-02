import asyncio
import json
from typing import Dict, Any

class DalfoxIntegration:
    @staticmethod
    async def run_scan(target_url: str, mode: str = "GET", data: str = None, headers: str = None) -> Dict[str, Any]:
        """
        Executes dalfox against the target with structured JSON parsing.
        """
        args = ["dalfox", "url", target_url, "--format", "json"]
        if mode == "POST":
            args.extend(["-X", "POST"])
        if data:
            args.extend(["-d", data])
        if headers:
            args.extend(["-H", headers])
            
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode()
            findings = []
            if output:
                for line in output.strip().split('\n'):
                    if line:
                        try:
                            j = json.loads(line)
                            # Verify if it's an actionable payload (V = Vulnerability)
                            if j.get("type") == "V":
                                findings.append({
                                    "payload": j.get("payload", j.get("poc")),
                                    "reflection_context": j.get("message", "unknown"),
                                    "execution_evidence": j.get("evidence", j.get("poc")),
                                    "method": mode
                                })
                        except json.JSONDecodeError:
                            pass
            
            return {
                "target": target_url,
                "vulnerable": len(findings) > 0,
                "raw_output": output,
                "findings": findings,
                "error": stderr.decode() if process.returncode != 0 else None
            }
        except FileNotFoundError:
            # Fallback for environment without dalfox installed
            return {
                "target": target_url,
                "vulnerable": False,
                "raw_output": "[MOCK] dalfox not found in PATH",
                "findings": [],
                "error": "Tool not installed"
            }
