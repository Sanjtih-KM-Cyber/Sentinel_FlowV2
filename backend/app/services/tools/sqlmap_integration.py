import asyncio
import re
from typing import Dict, Any

class SqlMapIntegration:
    @staticmethod
    async def run_scan(target_url: str) -> Dict[str, Any]:
        """
        Executes sqlmap against the target.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "sqlmap", "-u", target_url, "--batch", "-v", "1",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode()
            
            injections = []
            dbms = None
            
            # Extract DBMS
            dbms_match = re.search(r"back-end DBMS:\s+(.*)", output)
            if dbms_match:
                dbms = dbms_match.group(1).strip()
            
            # Extract injection blocks separated by '---'
            blocks = re.split(r"---", output)
            for block in blocks:
                if "Parameter:" in block and "Type:" in block:
                    lines = block.strip().split('\n')
                    current_type = None
                    current_payload = None
                    for line in lines:
                        if line.startswith("    Type:"):
                            current_type = line.split("Type:", 1)[1].strip()
                        elif line.startswith("    Payload:"):
                            current_payload = line.split("Payload:", 1)[1].strip()
                            if current_type and current_payload:
                                injections.append({
                                    "type": current_type,
                                    "payload": current_payload,
                                    "dbms": dbms
                                })
                                current_type = None
                                current_payload = None
            
            vulnerable = len(injections) > 0
            
            return {
                "target": target_url,
                "vulnerable": vulnerable,
                "injections": injections,
                "raw_output": output,
                "error": stderr.decode() if process.returncode != 0 else None
            }
        except FileNotFoundError:
            # Fallback for environment without sqlmap installed
            return {
                "target": target_url,
                "vulnerable": False,
                "injections": [],
                "raw_output": "[MOCK] sqlmap not found in PATH",
                "error": "Tool not installed"
            }
