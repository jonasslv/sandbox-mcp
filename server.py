from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List, Optional
from mcp_sandbox_tool import PythonSandboxTool
import re


mcp = FastMCP("python-sandbox")
sandbox = PythonSandboxTool()

def extract_imports(script):
        imports = []
        
        # Expressão regular para encontrar imports
        # Captura importações simples e compostas
        import_pattern = r'^(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
        
        # Encontra todas as linhas que contêm imports
        lines = script.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith(('import ', 'from ')):
                # Encontra o nome do pacote
                match = re.match(import_pattern, line)
                if match:
                    imported_package = match.group(1)
                    imports.append(imported_package)
        
        return imports


@mcp.tool()
async def execute(
    script: str
) -> Dict[str, Any]:
    """
    Executa um script Python em um container Docker isolado.

    script:
        String com formatação .py para rodar como script.
    """

    ALLOWED_PACKAGES = [
        # Data
        'numpy',
        'pandas',
        'openpyxl',
        'mpmath',

        # Utils
        'pyyaml',
        'python-dotenv',
        'tqdm',
        'rich',

        # Parsing
        'beautifulsoup4',
        'lxml',

        # Math
        'sympy',

        # Charts
        'matplotlib',
        'plotly',
        'graphviz',

        # Validation
        'pydantic',
        'jsonschema',
        # HTTP
        'requests',
        'youtube-transcript-api'
    ]

    packages = extract_imports(script)

    valid = []
    for item in packages:
        normalized = item.replace("_", "-")
        if normalized in ALLOWED_PACKAGES:
            valid.append(normalized)

    return await sandbox.execute({
        "script": script,
        "packages": valid or [],
    })

    


if __name__ == "__main__":
    mcp.run()