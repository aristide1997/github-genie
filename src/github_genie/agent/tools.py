"""Tools for GitHub Genie agent."""

import asyncio
import logging
import os
import re
import shlex
import subprocess
import tempfile

from pydantic_ai import RunContext

from .dependencies import GenieDependencies

# Set up logging
logger = logging.getLogger('github_genie.tools')


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
    
    # Report progress if available
    if ctx.deps.progress_reporter:
        await ctx.deps.progress_reporter.report_progress(f"🔧 Cloning repository: {repo_url}")
    
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
        
        # Use async subprocess to avoid blocking the event loop
        process = await asyncio.create_subprocess_exec(
            *clone_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=lfs_skip_env
        )
        
        # Wait for completion with timeout (5 minutes)
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        stdout = stdout.decode('utf-8') if stdout else ''
        stderr = stderr.decode('utf-8') if stderr else ''
        
        if process.returncode != 0:
            logger.error(f"Git clone failed for {repo_url}: {stderr}")
            return f"Failed to clone repository: {stderr}"
        
        # Store the repo path in dependencies
        ctx.deps.current_repo_path = repo_path
        
        return f"Successfully cloned repository to: {repo_path}"
        
    except asyncio.TimeoutError:
        logger.error(f"Clone timeout for {repo_url}")
        return "Repository cloning timed out (5 minutes). The repository might be too large or network is slow."
    except Exception as e:
        logger.error(f"Clone exception for {repo_url}: {str(e)}")
        return f"Error cloning repository: {str(e)}"


async def get_repository_structure(ctx: RunContext[GenieDependencies], repo_path: str) -> str:
    """Get high-level repository structure and identify key files.
    
    Args:
        ctx: The context.
        repo_path: Path to the cloned repository.
    """
    logger.info(f"🔧 TOOL: get_repository_structure(repo_path='{repo_path}')")
    
    # Report progress if available
    if ctx.deps.progress_reporter:
        await ctx.deps.progress_reporter.report_progress("🔧 Analyzing repository structure...")
    
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


async def list_directory_contents(
    ctx: RunContext[GenieDependencies], 
    directory_path: str = None, 
    filter_pattern: str = None
) -> str:
    """List files and directories with optional filtering.
    
    Args:
        ctx: The context.
        directory_path: Path to the directory to list. If None, '.' or empty, defaults to current repo path.
        filter_pattern: Optional regex pattern to filter files/directories.
    """
    logger.info(f"🔧 TOOL: list_directory_contents(directory_path='{directory_path}', filter_pattern={filter_pattern})")
    
    try:
        # Resolve directory path - default to current repo path if not specified or relative
        if not directory_path or directory_path.strip() in ['', '.']:
            target_dir = ctx.deps.current_repo_path
            if not target_dir:
                logger.error("No directory specified and no repository cloned")
                return "Error: No directory specified and no repository available. Clone a repository first."
        else:
            directory_path = directory_path.strip()
            if os.path.isabs(directory_path):
                target_dir = directory_path
            else:
                # Relative path - resolve relative to current repo
                if not ctx.deps.current_repo_path:
                    logger.error("Relative path provided but no repository cloned")
                    return "Error: Relative path provided but no repository available. Clone a repository first."
                target_dir = os.path.join(ctx.deps.current_repo_path, directory_path)
        
        # Report progress if available
        if ctx.deps.progress_reporter:
            dir_name = os.path.basename(target_dir) or target_dir
            await ctx.deps.progress_reporter.report_progress(f"🔧 Exploring directory: {dir_name}")
        
        if not os.path.exists(target_dir):
            logger.warning(f"Directory not found: {target_dir}")
            return f"Directory does not exist: {target_dir}"
        
        if not os.path.isdir(target_dir):
            logger.warning(f"Path is not a directory: {target_dir}")
            return f"Path is not a directory: {target_dir}"
        
        items = []
        pattern = None
        
        # Validate filter pattern if provided
        if filter_pattern:
            if not isinstance(filter_pattern, str):
                logger.error(f"Invalid filter_pattern parameter: {filter_pattern}")
                return f"Error: filter_pattern must be a string"
            
            try:
                pattern = re.compile(filter_pattern.strip())
            except re.error as regex_err:
                logger.error(f"Invalid regex in filter_pattern '{filter_pattern}': {regex_err}")
                return f"Error: Invalid regex pattern in filter_pattern: {regex_err}"
        
        for item in sorted(os.listdir(target_dir)):
            # Skip hidden files starting with . unless specifically requested
            if item.startswith('.') and (not filter_pattern or not pattern.search(item)):
                continue
                
            if pattern and not pattern.search(item):
                continue
            
            item_path = os.path.join(target_dir, item)
            
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
            return f"No items found in {target_dir}" + (f" matching pattern '{filter_pattern}'" if filter_pattern else "")
        
        result = f"Contents of {target_dir}:"
        if filter_pattern:
            result += f" (filtered by '{filter_pattern}')"
        result += f"\n" + "\n".join(items)
        
        return result
        
    except Exception as e:
        logger.error(f"Directory listing failed for {target_dir}: {str(e)}")
        return f"Error listing directory contents: {str(e)}"


async def read_file_content(
    ctx: RunContext[GenieDependencies], 
    file_path: str, 
    line_start: int = 1, 
    line_end: int = 200
) -> str:
    """Read file contents with line numbers (defaults to first 200 lines).
    
    Args:
        ctx: The context.
        file_path: Path to the file to read. Relative paths are resolved relative to current repo.
        line_start: Starting line number (1-indexed, default: 1).
        line_end: Ending line number (1-indexed, default: 200). Use None to read entire file.
    """
    logger.info(f"🔧 TOOL: read_file_content(file_path='{file_path}', line_start={line_start}, line_end={line_end})")
    
    try:
        # Parameter validation
        if not isinstance(file_path, str) or not file_path.strip():
            logger.error(f"Invalid file_path parameter: {file_path}")
            return f"Error: file_path must be a non-empty string"
        
        if not isinstance(line_start, int) or line_start < 1:
            logger.error(f"Invalid line_start parameter: {line_start}")
            return f"Error: line_start must be a positive integer"
        
        if line_end is not None and (not isinstance(line_end, int) or line_end < line_start):
            logger.error(f"Invalid line_end parameter: {line_end}")
            return f"Error: line_end must be None or an integer >= line_start"
        
        file_path = file_path.strip()
        
        # Resolve file path - handle relative paths relative to current repo
        if os.path.isabs(file_path):
            target_file = file_path
        else:
            # Relative path - resolve relative to current repo
            if not ctx.deps.current_repo_path:
                logger.error("Relative path provided but no repository cloned")
                return "Error: Relative path provided but no repository available. Clone a repository first."
            target_file = os.path.join(ctx.deps.current_repo_path, file_path)
        
        # Report progress if available
        if ctx.deps.progress_reporter:
            file_name = os.path.basename(target_file) or target_file
            await ctx.deps.progress_reporter.report_progress(f"🔧 Reading file: {file_name}")
        
        if not os.path.exists(target_file):
            logger.warning(f"File not found: {target_file}")
            return f"File does not exist: {target_file}"
        
        if not os.path.isfile(target_file):
            logger.warning(f"Path is not a file: {target_file}")
            return f"Path is not a file: {target_file}"
        
        # Check file size to avoid reading very large files
        file_size = os.path.getsize(target_file)
        if file_size > 10 * 1024 * 1024:  # > 10MB
            logger.warning(f"File too large to read: {target_file} ({file_size / (1024 * 1024):.1f}MB)")
            return f"File too large to read ({file_size / (1024 * 1024):.1f}MB): {target_file}"
        
        # Try to read as text
        encodings = ['utf-8', 'latin-1', 'cp1252']
        lines = None
        
        for encoding in encodings:
            try:
                with open(target_file, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        
        if lines is None:
            logger.warning(f"Could not decode file as text: {target_file}")
            return f"Could not decode file as text: {target_file}"
        
        total_lines = len(lines)
        
        # Adjust line numbers (convert to 0-indexed)
        start_idx = line_start - 1
        end_idx = (line_end - 1) if line_end is not None else total_lines - 1
        
        # Validate line ranges
        if start_idx >= total_lines:
            return f"Error: line_start ({line_start}) exceeds file length ({total_lines} lines)"
        
        if end_idx >= total_lines:
            end_idx = total_lines - 1
            if line_end is not None:
                logger.warning(f"line_end adjusted to file length: {total_lines}")
        
        # Extract the requested lines
        selected_lines = lines[start_idx:end_idx + 1]
        
        # Add line numbers for context
        numbered_lines = []
        for i, line in enumerate(selected_lines, start=line_start):
            numbered_lines.append(f"{i:4d}: {line.rstrip()}")
        
        actual_end = start_idx + len(selected_lines)
        result = f"File: {target_file} (lines {line_start}-{actual_end}, total file lines: {total_lines})\n\n"
        result += '\n'.join(numbered_lines)
        
        # Add note if file was truncated
        if line_end is not None and actual_end < total_lines:
            result += f"\n\n... (showing lines {line_start}-{actual_end} of {total_lines} total lines)"
        
        return result
        
    except Exception as e:
        logger.error(f"File reading failed for {target_file}: {str(e)}")
        return f"Error reading file: {str(e)}"


async def search_in_files(
    ctx: RunContext[GenieDependencies], 
    search_pattern: str, 
    directory_path: str = None, 
    file_extensions: list[str] = None,
    max_files: int = 15,
    max_tokens: int = 100000
) -> str:
    """Search for patterns across multiple files with LLM-friendly output limits.
    
    Args:
        ctx: The context.
        search_pattern: Regex pattern to search for.
        directory_path: Directory to search in (defaults to current repo path).
        file_extensions: List of file extensions to search (e.g., ['.py', '.js']).
        max_files: Maximum number of files to include in results (default: 15).
        max_tokens: Approximate token limit to prevent rate limit errors (default: 100k).
    """
    logger.info(f"🔧 TOOL: search_in_files(search_pattern='{search_pattern}', directory_path={directory_path}, file_extensions={file_extensions})")
    
    # Report progress if available
    if ctx.deps.progress_reporter:
        await ctx.deps.progress_reporter.report_progress(f"🔧 Searching for pattern: {search_pattern}")
    
    try:
        # Parameter validation
        if not isinstance(search_pattern, str) or not search_pattern.strip():
            logger.error(f"Invalid search_pattern parameter: {search_pattern}")
            return f"Error: search_pattern must be a non-empty string"
        
        search_pattern = search_pattern.strip()
        
        # Resolve directory path - default to current repo path if not specified or relative
        if not directory_path or directory_path.strip() in ['', '.']:
            search_dir = ctx.deps.current_repo_path
            if not search_dir:
                logger.error("No directory specified and no repository cloned")
                return "Error: No directory specified and no repository available. Clone a repository first."
        else:
            directory_path = directory_path.strip()
            if os.path.isabs(directory_path):
                search_dir = directory_path
            else:
                # Relative path - resolve relative to current repo
                if not ctx.deps.current_repo_path:
                    logger.error("Relative path provided but no repository cloned")
                    return "Error: Relative path provided but no repository available. Clone a repository first."
                search_dir = os.path.join(ctx.deps.current_repo_path, directory_path)
        
        if not os.path.exists(search_dir):
            logger.warning(f"Directory not found: {search_dir}")
            return f"Directory does not exist: {search_dir}"
        
        if not os.path.isdir(search_dir):
            logger.warning(f"Path is not a directory: {search_dir}")
            return f"Path is not a directory: {search_dir}"
        
        # Validate regex pattern
        try:
            pattern = re.compile(search_pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as regex_err:
            logger.error(f"Invalid regex pattern '{search_pattern}': {regex_err}")
            return f"Error: Invalid regex pattern '{search_pattern}': {regex_err}"
        
        matches = []
        files_searched = 0
        total_matches_found = 0
        estimated_tokens = 0
        files_with_matches = 0
        truncated = False
        
        def estimate_tokens(text: str) -> int:
            """Rough token estimation: ~4 characters per token"""
            return len(text) // 4
        
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
                    file_matches = []
                    
                    # Find matches in this file
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if pattern.search(line):
                            total_matches_found += 1
                            
                            # Get some context around the match
                            lines = content.split('\n')
                            start = max(0, line_num - 2)  # Reduced context for token efficiency
                            end = min(len(lines), line_num + 1)
                            context_lines = lines[start:end]
                            
                            # Highlight the matching line
                            context_lines[line_num - 1 - start] = f">>> {context_lines[line_num - 1 - start]}"
                            
                            relative_path = os.path.relpath(file_path, search_dir)
                            match_context = '\n'.join(context_lines)
                            
                            # Estimate tokens for this match
                            match_text = f"📄 {relative_path}:{line_num}\n{match_context}\n"
                            match_tokens = estimate_tokens(match_text)
                            
                            # Check if adding this match would exceed limits
                            if (estimated_tokens + match_tokens > max_tokens or 
                                files_with_matches >= max_files):
                                truncated = True
                                break
                            
                            file_matches.append({
                                'file': relative_path,
                                'line': line_num,
                                'context': match_context,
                                'tokens': match_tokens
                            })
                            estimated_tokens += match_tokens
                            
                            # Limit matches per file to keep results manageable
                            if len(file_matches) >= 3:  # Reduced from 5 for token efficiency
                                break
                    
                    # Add file matches if any found and we haven't exceeded limits
                    if file_matches:
                        matches.extend(file_matches)
                        files_with_matches += 1
                        
                        # Check file limit after adding this file's matches
                        if files_with_matches >= max_files:
                            truncated = True
                            break
                
                except Exception:
                    continue  # Skip files that can't be read
                
                if truncated:
                    break
            
            if truncated:
                break
        
        if not matches:
            return f"No matches found for pattern '{search_pattern}' in {files_searched} files searched."
        
        # Build result with summary
        result_parts = []
        
        # Summary header
        summary = f"Found {total_matches_found} matches for pattern '{search_pattern}' in {files_searched} files"
        if truncated:
            summary += f" (showing first {len(matches)} matches from {files_with_matches} files)"
        result_parts.append(f"{summary}:\n")
        
        # Add matches
        for match in matches:
            result_parts.append(f"📄 {match['file']}:{match['line']}")
            result_parts.append(match['context'])
            result_parts.append("")  # Empty line for separation
        
        # Add truncation notice if applicable
        if truncated:
            result_parts.append("⚠️  Results truncated due to size limits.")
            result_parts.append("💡 Use more specific search patterns to see additional matches.")
        
        return "\n".join(result_parts)
        
    except Exception as e:
        logger.error(f"File search failed in {search_dir}: {str(e)}")
        return f"Error searching files: {str(e)}"
