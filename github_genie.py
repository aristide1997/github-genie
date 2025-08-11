"""GitHub Genie - A pydantic-ai agent for analyzing GitHub repositories.

This agent can clone repositories, understand their structure, and answer questions about the codebase.
Similar to cursor/cline but as an agent that can be queried programmatically.
"""

import asyncio
import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic_ai import Agent, RunContext

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_genie')

@dataclass
class GenieDependencies:
    """Essential state for the GitHub Genie agent."""
    current_repo_path: str | None = None


# Create the GitHub Genie agent
github_genie = Agent(
    'openai:gpt-5-nano',
    deps_type=GenieDependencies,
    system_prompt="""You are GitHub Genie, a code analysis agent that helps users understand repositories.

When a user provides a repository URL and asks questions about it:
1. Extract the repo URL from their query
2. Clone the repository using the clone_repository tool
3. Analyze the structure using get_repository_structure to understand the project
4. Use your tools to explore files and find answers to the user's specific questions
5. Provide detailed, helpful responses about the codebase

Be thorough in your analysis but efficient - don't read unnecessary files. Focus on answering the specific question asked.
Use the tools strategically:
- Start with repository structure to get context
- Use list_directory_contents to explore specific directories
- Use read_file_content to examine relevant files
- Use search_in_files when looking for specific patterns or functionality

Always provide comprehensive answers with code examples when relevant.""",
    retries=2,
)


@github_genie.tool
async def clone_repository(
    ctx: RunContext[GenieDependencies], 
    repo_url: str, 
    fast_clone: bool = True
) -> str:
    """Clone a repository and return the local path.
    
    Args:
        ctx: The context.
        repo_url: The GitHub repository URL to clone.
        fast_clone: If True, use shallow clone (depth=1) and single branch for faster cloning.
    """
    logger.info(f"🔧 TOOL: clone_repository(repo_url='{repo_url}')")
    try:
        # Create a temporary directory for the repo
        temp_dir = tempfile.mkdtemp(prefix="github_genie_")
        
        # Extract repo name from URL for the directory name
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        repo_path = os.path.join(temp_dir, repo_name)
        
        # Clone the repository (disable LFS filters entirely to avoid requiring git-lfs)
        # Also ensure the command is fully non-interactive.
        lfs_skip_env = {
            **os.environ,
            'GIT_LFS_SKIP_SMUDGE': '1',  # Do not smudge/download LFS files
            'GIT_LFS_SKIP': '1',         # Additional safeguard
            'GIT_TERMINAL_PROMPT': '0',  # Never prompt for credentials
        }

        # Build clone command with temporary git config overrides placed BEFORE the subcommand
        # to completely disable LFS filters for this invocation
        clone_cmd = [
            'git',
            '-c', 'filter.lfs.smudge=',
            '-c', 'filter.lfs.process=',
            '-c', 'filter.lfs.clean=',
            '-c', 'filter.lfs.required=false',
            'clone',
        ]
        if fast_clone:
            # Shallow and partial clone to speed up and reduce data transfer
            clone_cmd.extend(['--depth=1', '--single-branch', '--no-tags', '--filter=blob:none'])
        clone_cmd.extend([repo_url, repo_path])
        
        result = subprocess.run(
            clone_cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 5 minute timeout
            env=lfs_skip_env
        )
        
        if result.returncode != 0:
            logger.error(f"Git clone failed for {repo_url}: {result.stderr}")
            return f"Failed to clone repository: {result.stderr}"
        
        # Store the repo path in dependencies
        ctx.deps.current_repo_path = repo_path
        
        return f"Successfully cloned repository to: {repo_path}"
        
    except subprocess.TimeoutExpired:
        logger.error(f"Clone timeout for {repo_url}")
        return "Repository cloning timed out (5 minutes). The repository might be too large or network is slow."
    except Exception as e:
        logger.error(f"Clone exception for {repo_url}: {str(e)}")
        return f"Error cloning repository: {str(e)}"


@github_genie.tool
async def get_repository_structure(ctx: RunContext[GenieDependencies], repo_path: str) -> str:
    """Get high-level repository structure and identify key files.
    
    Args:
        ctx: The context.
        repo_path: Path to the cloned repository.
    """
    logger.info(f"🔧 TOOL: get_repository_structure(repo_path='{repo_path}')")
    try:
        if not os.path.exists(repo_path):
            logger.error(f"Repository path not found: {repo_path}")
            return f"Repository path does not exist: {repo_path}"
        
        structure_info = []
        
        # Get basic info about the repository
        repo_name = os.path.basename(repo_path)
        structure_info.append(f"Repository: {repo_name}")
        structure_info.append(f"Path: {repo_path}")
        
        # List top-level contents
        top_level_items = []
        for item in sorted(os.listdir(repo_path)):
            if item.startswith('.git'):
                continue
            item_path = os.path.join(repo_path, item)
            if os.path.isdir(item_path):
                # Count files in directory
                try:
                    file_count = len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))])
                    top_level_items.append(f"📁 {item}/ ({file_count} files)")
                except PermissionError:
                    top_level_items.append(f"📁 {item}/ (permission denied)")
            else:
                # Get file size
                try:
                    size = os.path.getsize(item_path)
                    if size > 1024 * 1024:  # > 1MB
                        size_str = f"{size / (1024 * 1024):.1f}MB"
                    elif size > 1024:  # > 1KB
                        size_str = f"{size / 1024:.1f}KB"
                    else:
                        size_str = f"{size}B"
                    top_level_items.append(f"📄 {item} ({size_str})")
                except OSError:
                    top_level_items.append(f"📄 {item}")
        
        structure_info.append("\nTop-level structure:")
        structure_info.extend(top_level_items)
        
        # Identify key files
        key_files = []
        common_files = [
            'README.md', 'README.rst', 'README.txt', 'README',
            'package.json', 'requirements.txt', 'setup.py', 'pyproject.toml',
            'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle',
            'Makefile', 'CMakeLists.txt', 'Dockerfile',
            'LICENSE', 'LICENSE.txt', 'LICENSE.md',
            '.gitignore', '.env.example'
        ]
        
        for file in common_files:
            if os.path.exists(os.path.join(repo_path, file)):
                key_files.append(file)
        
        if key_files:
            structure_info.append(f"\nKey files found: {', '.join(key_files)}")
        
        return "\n".join(structure_info)
        
    except Exception as e:
        logger.error(f"Repository structure analysis failed for {repo_path}: {str(e)}")
        return f"Error analyzing repository structure: {str(e)}"


@github_genie.tool
async def list_directory_contents(
    ctx: RunContext[GenieDependencies], 
    directory_path: str, 
    filter_pattern: str = None
) -> str:
    """List files and directories with optional filtering.
    
    Args:
        ctx: The context.
        directory_path: Path to the directory to list.
        filter_pattern: Optional regex pattern to filter files/directories.
    """
    logger.info(f"🔧 TOOL: list_directory_contents(directory_path='{directory_path}', filter_pattern={filter_pattern})")
    try:
        if not os.path.exists(directory_path):
            logger.warning(f"Directory not found: {directory_path}")
            return f"Directory does not exist: {directory_path}"
        
        if not os.path.isdir(directory_path):
            logger.warning(f"Path is not a directory: {directory_path}")
            return f"Path is not a directory: {directory_path}"
        
        items = []
        pattern = re.compile(filter_pattern) if filter_pattern else None
        
        for item in sorted(os.listdir(directory_path)):
            # Skip hidden files starting with . unless specifically requested
            if item.startswith('.') and (not filter_pattern or not pattern.search(item)):
                continue
                
            if pattern and not pattern.search(item):
                continue
            
            item_path = os.path.join(directory_path, item)
            
            if os.path.isdir(item_path):
                try:
                    file_count = len([f for f in os.listdir(item_path) 
                                    if os.path.isfile(os.path.join(item_path, f))])
                    items.append(f"📁 {item}/ ({file_count} files)")
                except PermissionError:
                    items.append(f"📁 {item}/ (permission denied)")
            else:
                try:
                    size = os.path.getsize(item_path)
                    if size > 1024 * 1024:  # > 1MB
                        size_str = f"{size / (1024 * 1024):.1f}MB"
                    elif size > 1024:  # > 1KB
                        size_str = f"{size / 1024:.1f}KB"
                    else:
                        size_str = f"{size}B"
                    items.append(f"📄 {item} ({size_str})")
                except OSError:
                    items.append(f"📄 {item}")
        
        if not items:
            return f"No items found in {directory_path}" + (f" matching pattern '{filter_pattern}'" if filter_pattern else "")
        
        result = f"Contents of {directory_path}:"
        if filter_pattern:
            result += f" (filtered by '{filter_pattern}')"
        result += f"\n" + "\n".join(items)
        
        return result
        
    except Exception as e:
        logger.error(f"Directory listing failed for {directory_path}: {str(e)}")
        return f"Error listing directory contents: {str(e)}"


@github_genie.tool
async def read_file_content(ctx: RunContext[GenieDependencies], file_path: str) -> str:
    """Read file contents.
    
    Args:
        ctx: The context.
        file_path: Path to the file to read.
    """
    logger.info(f"🔧 TOOL: read_file_content(file_path='{file_path}')")
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return f"File does not exist: {file_path}"
        
        if not os.path.isfile(file_path):
            logger.warning(f"Path is not a file: {file_path}")
            return f"Path is not a file: {file_path}"
        
        # Check file size to avoid reading very large files
        file_size = os.path.getsize(file_path)
        if file_size > 1024 * 1024:  # > 1MB
            logger.warning(f"File too large to read: {file_path} ({file_size / (1024 * 1024):.1f}MB)")
            return f"File too large to read ({file_size / (1024 * 1024):.1f}MB): {file_path}"
        
        # Try to read as text
        encodings = ['utf-8', 'latin-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            logger.warning(f"Could not decode file as text: {file_path}")
            return f"Could not decode file as text: {file_path}"
        
        # Truncate very long content for display
        if len(content) > 10000:
            truncated_content = content[:10000] + f"\n\n... (truncated, total length: {len(content)} characters)"
            return f"File: {file_path}\n\n{truncated_content}"
        
        return f"File: {file_path}\n\n{content}"
        
    except Exception as e:
        logger.error(f"File reading failed for {file_path}: {str(e)}")
        return f"Error reading file: {str(e)}"


@github_genie.tool
async def search_in_files(
    ctx: RunContext[GenieDependencies], 
    search_pattern: str, 
    directory_path: str = None, 
    file_extensions: list[str] = None
) -> str:
    """Search for patterns across multiple files.
    
    Args:
        ctx: The context.
        search_pattern: Regex pattern to search for.
        directory_path: Directory to search in (defaults to current repo path).
        file_extensions: List of file extensions to search (e.g., ['.py', '.js']).
    """
    logger.info(f"🔧 TOOL: search_in_files(search_pattern='{search_pattern}', directory_path={directory_path}, file_extensions={file_extensions})")
    try:
        search_dir = directory_path or ctx.deps.current_repo_path
        if not search_dir or not os.path.exists(search_dir):
            logger.error(f"Invalid search directory: {search_dir}")
            return f"Invalid search directory: {search_dir}"
        
        pattern = re.compile(search_pattern, re.IGNORECASE | re.MULTILINE)
        matches = []
        files_searched = 0
        
        # Walk through directory
        for root, dirs, files in os.walk(search_dir):
            # Skip common directories that shouldn't be searched
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = os.path.join(root, file)
                
                # Filter by extensions if specified
                if file_extensions:
                    if not any(file.endswith(ext) for ext in file_extensions):
                        continue
                
                # Skip binary files and very large files
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > 1024 * 1024:  # Skip files > 1MB
                        continue
                except OSError:
                    continue
                
                # Try to read and search file
                try:
                    encodings = ['utf-8', 'latin-1']
                    for encoding in encodings:
                        try:
                            with open(file_path, 'r', encoding=encoding) as f:
                                content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        continue  # Skip if can't decode
                    
                    files_searched += 1
                    
                    # Find matches
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if pattern.search(line):
                            # Get some context around the match
                            lines = content.split('\n')
                            start = max(0, line_num - 3)
                            end = min(len(lines), line_num + 2)
                            context_lines = lines[start:end]
                            
                            # Highlight the matching line
                            context_lines[line_num - 1 - start] = f">>> {context_lines[line_num - 1 - start]}"
                            
                            relative_path = os.path.relpath(file_path, search_dir)
                            matches.append({
                                'file': relative_path,
                                'line': line_num,
                                'context': '\n'.join(context_lines)
                            })
                            
                            # Limit matches per file
                            if len([m for m in matches if m['file'] == relative_path]) >= 5:
                                break
                
                except Exception:
                    continue  # Skip files that can't be read
                
                # Limit total matches
                if len(matches) >= 50:
                    break
            
            if len(matches) >= 50:
                break
        
        if not matches:
            return f"No matches found for pattern '{search_pattern}' in {files_searched} files searched."
        
        result = [f"Found {len(matches)} matches for pattern '{search_pattern}' in {files_searched} files:\n"]
        
        for match in matches:
            result.append(f"📄 {match['file']}:{match['line']}")
            result.append(match['context'])
            result.append("")  # Empty line for separation
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"File search failed in {search_dir}: {str(e)}")
        return f"Error searching files: {str(e)}"


async def ask_genie(question: str) -> str:
    """Main function to ask the GitHub Genie a question about a repository.
    
    Args:
        question: Question that should include a repository URL and the actual question.
    
    Returns:
        The agent's response as a string.
    """
    deps = GenieDependencies()
    result = await github_genie.run(question, deps=deps)
    
    # Clean up temporary directory if it was created
    if deps.current_repo_path and os.path.exists(deps.current_repo_path):
        try:
            shutil.rmtree(os.path.dirname(deps.current_repo_path))
        except Exception:
            pass  # Ignore cleanup errors
    
    return result.data


async def main():
    """Example usage of the GitHub Genie."""
    # Example question
    # question = """
    # Repository: https://github.com/pydantic/pydantic-ai
    # Question: How does the agent system work? What are the main components and how do they interact?
    # """
    question = """
    Repository: https://github.com/cline/cline
    Question: How does the agent system work? What are the main components and how do they interact?
    """
    
    print("Asking GitHub Genie...")
    response = await ask_genie(question)
    print("\nResponse:")
    print(response)


if __name__ == '__main__':
    asyncio.run(main())
