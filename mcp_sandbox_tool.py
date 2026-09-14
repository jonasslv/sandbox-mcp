#!/usr/bin/env python3
"""
MCP Tool for running Python scripts in a secure Docker sandbox
"""
import asyncio
import json
import tempfile
import os
import sys
from typing import Dict, Any, Optional, List
import docker
from docker.errors import APIError, DockerException
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PythonSandboxTool:
    def __init__(self):
        self.client = docker.from_env()
        self.sandbox_image = "python:3.9"
        self.timeout_seconds = 120
        self.memory_limit = "4096m"
        self.input_folder = "/tmp/input-llm"
        self.artifacts_folder = "/tmp/artifacts-llm"

        
    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Python script in a secure sandbox environment
        """
        try:
            # Extract the script from the request
            script_content = request.get("script", "")
            packages = request.get("packages", "")
            if not script_content:
                return {
                    "error": "No script provided",
                    "status": "error"
                }
            
            # Create a temporary directory for the script
            with tempfile.TemporaryDirectory() as temp_dir:
                script_path = os.path.join(temp_dir, "script.py")
                
                # Write the script to a file
                with open(script_path, "w") as f:
                    f.write(script_content)
                
                # Run the script in a Docker container with security constraints
                result = await self._run_in_sandbox(script_path,packages)
                
                return {
                    "status": "success",
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                    "return_code": result.get("return_code", 0),
                    "artifacts": result.get("artifacts", [])
                }
                
        except Exception as e:
            logger.error(f"Error executing script: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def _run_in_sandbox(self, script_path: str, packages: Optional[List[str]] = []) -> Dict[str, Any]:
        container = None
        """
        Run the script in a Docker container with security constraints
        """
        try:
            if not os.path.exists(self.artifacts_folder):
                os.makedirs(self.artifacts_folder)
            if not os.path.exists(self.input_folder):
                os.makedirs(self.input_folder)
            os.chmod(self.artifacts_folder, 0o1777)
            os.chmod(self.input_folder, 0o1777)
                
            command = ["python", "/app/script.py"]

            if len(packages) > 0:
                command = [
                    "bash",
                    "-c",
                    (
                        "mkdir -p /tmp/packages && "
                        "pip install -qq --disable-pip-version-check --no-cache-dir "
                        "--target /tmp/packages "
                        + " ".join(packages)
                        + " && "
                        "PYTHONPATH=/tmp/packages python /app/script.py"
                    )
                ]
            
            # Create a Docker container with security constraints
            container = self.client.containers.run(
                security_opt=["no-new-privileges"],
                cap_drop=["ALL"],
                pids_limit=128,
                image=self.sandbox_image,
                command=command,
                volumes={
                    script_path: {"bind": "/app/script.py", "mode": "ro"},
                    self.artifacts_folder: {"bind": "/tmp/artifacts", "mode": "rw"},
                    self.input_folder: {"bind": "/tmp/input", "mode": "ro"}
                },
                mem_limit=self.memory_limit,
                network_disabled=False,
                detach=True,
                read_only=False,
                nano_cpus=4_000_000_000,
                user="65534:65534"  # Run as non-root user for additional security
            )
            result = container.wait(timeout=self.timeout_seconds)
            return_code = result["StatusCode"]

            logs = container.logs(stdout=True, stderr=False).decode()

            errors = container.logs(stdout=False, stderr=True).decode()
            
            # Extract artifacts from the temporary artifacts directory
            artifacts = self._extract_artifacts(self.artifacts_folder)
            
            return {
                "stdout": logs,
                "stderr": errors,
                "return_code": return_code,
                "artifacts": artifacts
            }
                
        except DockerException as e:
            logger.error(f"Docker error running in sandbox: {str(e)}")
            return {
                "status": "error",
                "stdout": "",
                "stderr": f"Docker error: {str(e)}",
                "return_code": -1,
                "artifacts": []
            }
        except Exception as e:
            logger.error(f"Error running in sandbox: {str(e)}")
            return {
                "status": "error",
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "artifacts": []
            }
        finally:
            if container is not None:
                container.remove(force=True)
    
    def _extract_artifacts(self, artifacts_temp_dir: str) -> list:
        """
        Extract artifacts created during script execution
        """
        artifacts = []
        
        try:
            # Check if artifacts directory exists
            if os.path.exists(artifacts_temp_dir):
                # List all files in the artifacts directory
                for filename in os.listdir(artifacts_temp_dir):
                    file_path = os.path.join(artifacts_temp_dir, filename)
                    if os.path.isfile(file_path):
                        artifacts.append({
                            "filename": filename
                        })
        except Exception as e:
            logger.error(f"Error extracting artifacts: {str(e)}")
            
        return artifacts
