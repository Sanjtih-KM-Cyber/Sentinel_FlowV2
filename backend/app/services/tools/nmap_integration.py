import asyncio
import xml.etree.ElementTree as ET
from typing import Dict, Any

class NmapIntegration:
    @staticmethod
    async def run_scan(target_host: str) -> Dict[str, Any]:
        """
        Executes nmap against the target.
        """
        try:
            # Running a quick scan with XML output
            process = await asyncio.create_subprocess_exec(
                "nmap", "-T4", "-F", "-oX", "-", target_host,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode()
            open_ports = []
            
            try:
                if output:
                    root = ET.fromstring(output)
                    for host in root.findall('host'):
                        ports = host.find('ports')
                        if ports is not None:
                            for port in ports.findall('port'):
                                state = port.find('state')
                                if state is not None and state.get('state') == 'open':
                                    service = port.find('service')
                                    service_name = service.get('name') if service is not None else 'unknown'
                                    open_ports.append({
                                        'port': int(port.get('portid')),
                                        'protocol': port.get('protocol'),
                                        'service': service_name
                                    })
            except Exception:
                pass
            
            return {
                "target": target_host,
                "open_ports": open_ports,
                "raw_output": output,
                "error": stderr.decode() if process.returncode != 0 else None
            }
        except FileNotFoundError:
            # Fallback for environment without nmap installed
            return {
                "target": target_host,
                "open_ports": [],
                "raw_output": "[MOCK] nmap not found in PATH",
                "error": "Tool not installed"
            }
